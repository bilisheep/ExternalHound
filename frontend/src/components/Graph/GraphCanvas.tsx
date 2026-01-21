import { forwardRef, useEffect, useImperativeHandle, useRef } from 'react';
import { Graph } from '@antv/g6';
import type { GraphData, NodeData, EdgeData, State } from '@antv/g6';

interface GraphCanvasProps {
  data: GraphData;
  linkMode?: boolean;
  onCreateEdge?: (edge: EdgeData) => void;
  onEdgeClick?: (edgeId: string) => void;
  onNodeDoubleClick?: (nodeId: string) => void;
  onNodeClick?: (nodeId: string) => void;
}

export interface GraphCanvasHandle {
  removeEdge: (edgeId: string) => void;
}

const NODE_COLORS: Record<string, string> = {
  Organization: '#2f54eb',
  Domain: '#13c2c2',
  IP: '#fa8c16',
  Netblock: '#722ed1',
  Service: '#52c41a',
  Certificate: '#eb2f96',
  ClientApplication: '#1890ff',
  Credential: '#fa541c',
  default: '#8c8c8c',
};

const NODE_SIZE = 42;
const EDGE_COLOR = '#94a3b8';
const EDGE_LABEL_COLOR = '#475569';
const HIGHLIGHT_COLOR = '#faad14';
const CANVAS_BACKGROUND = '#f8fafc';
const CANVAS_BORDER = '#e2e8f0';

const getNodeColor = (type?: string) => NODE_COLORS[type ?? 'default'] ?? NODE_COLORS.default;

const buildAdjacency = (data: GraphData) => {
  const map = new Map<string, { neighbors: Set<string>; edges: Set<string> }>();
  const ensure = (id: string) => {
    const existing = map.get(id);
    if (existing) {
      return existing;
    }
    const entry = { neighbors: new Set<string>(), edges: new Set<string>() };
    map.set(id, entry);
    return entry;
  };

  (data.edges ?? []).forEach((edge) => {
    const source = String(edge.source);
    const target = String(edge.target);
    const edgeId = edge.id ? String(edge.id) : undefined;
    const sourceEntry = ensure(source);
    const targetEntry = ensure(target);
    sourceEntry.neighbors.add(target);
    targetEntry.neighbors.add(source);
    if (edgeId) {
      sourceEntry.edges.add(edgeId);
      targetEntry.edges.add(edgeId);
    }
  });

  return map;
};

const LINK_ASSIST_NODE_ID = 'graph-link-assist-node';
const LINK_ASSIST_EDGE_ID = 'graph-link-assist-edge';

const GraphCanvas = forwardRef<GraphCanvasHandle, GraphCanvasProps>(
  ({ data, linkMode = false, onCreateEdge, onEdgeClick, onNodeDoubleClick, onNodeClick }, ref) => {
    const containerRef = useRef<HTMLDivElement | null>(null);
    const graphRef = useRef<Graph | null>(null);
    const dataRef = useRef<GraphData>(data);
    const adjacencyRef = useRef<Map<string, { neighbors: Set<string>; edges: Set<string> }>>(
      new Map()
    );
    const focusRef = useRef<string | null>(null);
    const linkSourceRef = useRef<string | null>(null);
    const linkModeRef = useRef<boolean>(linkMode);
    const onCreateEdgeRef = useRef<GraphCanvasProps['onCreateEdge']>(onCreateEdge);
    const onEdgeClickRef = useRef<GraphCanvasProps['onEdgeClick']>(onEdgeClick);
    const onNodeDoubleClickRef = useRef<GraphCanvasProps['onNodeDoubleClick']>(
      onNodeDoubleClick
    );
    const onNodeClickRef = useRef<GraphCanvasProps['onNodeClick']>(onNodeClick);

    useEffect(() => {
      onCreateEdgeRef.current = onCreateEdge;
    }, [onCreateEdge]);

    useEffect(() => {
      onEdgeClickRef.current = onEdgeClick;
    }, [onEdgeClick]);

    useEffect(() => {
      onNodeDoubleClickRef.current = onNodeDoubleClick;
    }, [onNodeDoubleClick]);

    useEffect(() => {
      onNodeClickRef.current = onNodeClick;
    }, [onNodeClick]);

    useEffect(() => {
      linkModeRef.current = linkMode;
      if (!linkMode && linkSourceRef.current) {
        cleanupLinkAssist();
        linkSourceRef.current = null;
        graphRef.current?.getCanvas().setCursor('default');
      }
      if (graphRef.current) {
        graphRef.current.updateBehavior({
          key: 'drag-element',
          trigger: linkMode ? ['shift'] : [],
        });
      }
    }, [linkMode]);

    const applyStates = (states: Record<string, State | State[]>) => {
      if (!graphRef.current) {
        return;
      }
      graphRef.current.setElementState(states, true);
    };

    const clearStates = () => {
      const nextStates: Record<string, State[]> = {};
      (dataRef.current.nodes ?? []).forEach((node) => {
        nextStates[String(node.id)] = [];
      });
      (dataRef.current.edges ?? []).forEach((edge) => {
        if (edge.id) {
          nextStates[String(edge.id)] = [];
        }
      });
      focusRef.current = null;
      applyStates(nextStates);
    };

    const focusNode = (nodeId: string) => {
      if (focusRef.current === nodeId) {
        clearStates();
        return;
      }

      const adjacency = adjacencyRef.current.get(nodeId);
      const neighborIds = new Set<string>([nodeId]);

      adjacency?.neighbors.forEach((neighbor) => neighborIds.add(neighbor));

      const nextStates: Record<string, State[]> = {};
      (dataRef.current.nodes ?? []).forEach((node) => {
        const id = String(node.id);
        if (neighborIds.has(id)) {
          nextStates[id] = id === nodeId ? ['selected'] : ['active'];
        } else {
          nextStates[id] = ['inactive'];
        }
      });
      (dataRef.current.edges ?? []).forEach((edge) => {
        if (!edge.id) {
          return;
        }
        const id = String(edge.id);
        const source = String(edge.source);
        const target = String(edge.target);
        // Highlight edge if it connects two highlighted nodes (or at least one if we wanted less strict)
        // Strictly speaking, if we want to highlight edges connected to the focal node:
        // Check if this edge is connected to the focal node.
        const isConnectedToFocal = source === nodeId || target === nodeId;
        
        if (isConnectedToFocal) {
           nextStates[id] = ['active'];
        } else {
           nextStates[id] = ['inactive'];
        }
      });

      focusRef.current = nodeId;
      applyStates(nextStates);
    };

    const getCanvasPoint = (
      graph: Graph,
      event: {
        canvas?: { x: number; y: number };
        canvasX?: number;
        canvasY?: number;
        x?: number;
        y?: number;
        client?: { x: number; y: number };
        clientX?: number;
        clientY?: number;
      }
    ) => {
      if (event.canvas) {
        return [event.canvas.x, event.canvas.y] as const;
      }
      if (typeof event.canvasX === 'number' && typeof event.canvasY === 'number') {
        return [event.canvasX, event.canvasY] as const;
      }
      if (typeof event.x === 'number' && typeof event.y === 'number') {
        return [event.x, event.y] as const;
      }
      if (event.client) {
        return graph.getCanvasByClient([event.client.x, event.client.y]);
      }
      if (typeof event.clientX === 'number' && typeof event.clientY === 'number') {
        return graph.getCanvasByClient([event.clientX, event.clientY]);
      }
      return null;
    };

    const cleanupLinkAssist = () => {
      if (!graphRef.current) {
        return;
      }
      try {
        graphRef.current.removeEdgeData([LINK_ASSIST_EDGE_ID]);
      } catch (error) {
        // Ignore missing assist edge.
      }
      try {
        graphRef.current.removeNodeData([LINK_ASSIST_NODE_ID]);
      } catch (error) {
        // Ignore missing assist node.
      }
      graphRef.current.draw();
    };

    useImperativeHandle(ref, () => ({
      removeEdge: (edgeId: string) => {
        if (!edgeId || !graphRef.current) {
          return;
        }
        try {
          const edges = graphRef.current.getEdgeData() as EdgeData[];
          if (!edges.some((edge) => String(edge.id) === edgeId)) {
            return;
          }
          graphRef.current.removeEdgeData([edgeId]);
          graphRef.current.draw();
        } catch (error) {
          // Ignore missing edges or transient graph sync issues.
        }
      },
    }));

    useEffect(() => {
      dataRef.current = data;
      adjacencyRef.current = buildAdjacency(data);
      if (graphRef.current) {
        graphRef.current.setData(data);
        graphRef.current.render().then(() => {
          if (graphRef.current?.destroyed) {
            return;
          }
          graphRef.current?.fitView(undefined, false);
          clearStates();
        });
      }
    }, [data]);

    useEffect(() => {
      if (!containerRef.current || graphRef.current) {
        return;
      }

      const container = containerRef.current;
      const graph = new Graph({
        container,
        width: container.clientWidth || 800,
        height: container.clientHeight || 600,
        animation: true,
        layout: {
          type: 'dagre',
          rankdir: 'LR',
          nodesep: 30,
          ranksep: 100,
        },
        behaviors: [
          'drag-canvas',
          'zoom-canvas',
          {
            type: 'drag-element',
            key: 'drag-element',
            trigger: linkMode ? ['shift'] : [],
          },
        ],
        node: {
          type: 'circle',
          style: (datum) => {
            const nodeData = (datum as NodeData).data as { type?: string; label?: string } | undefined;
            const nodeType = nodeData?.type;
            const color = getNodeColor(nodeType);
            return {
              size: NODE_SIZE,
              fill: color,
              stroke: '#ffffff',
              lineWidth: 2,
              shadowColor: 'rgba(15, 23, 42, 0.18)',
              shadowBlur: 12,
              shadowOffsetY: 2,
              labelText: nodeData?.label ?? String(datum.id),
              labelFill: '#0f172a',
              labelPlacement: 'bottom',
              labelOffsetY: 10,
              labelFontSize: 12,
              labelFontWeight: 500,
            };
          },
          state: {
            selected: {
              halo: true,
              haloStroke: HIGHLIGHT_COLOR,
              haloLineWidth: 14,
              lineWidth: 2,
              opacity: 1,
              labelOpacity: 1,
            },
            active: {
              stroke: HIGHLIGHT_COLOR,
              lineWidth: 2,
              opacity: 1,
              labelOpacity: 1,
            },
            inactive: {
              opacity: 0.15,
              labelOpacity: 0.15,
            },
          },
        },
        edge: {
          type: 'line',
          style: (datum) => {
            const edgeData = (datum as EdgeData).data as { label?: string } | undefined;
            return {
              stroke: EDGE_COLOR,
              strokeOpacity: 0.8,
              lineWidth: 1.4,
              endArrow: true,
              endArrowType: 'triangle',
              endArrowSize: 10,
              endArrowFill: EDGE_COLOR,
              labelText: edgeData?.label ?? '',
              labelFill: EDGE_LABEL_COLOR,
              labelFontSize: 11,
              labelBackground: true,
              labelBackgroundFill: '#fff',
              labelBackgroundRadius: 4,
              labelPadding: [2, 6, 2, 6],
              labelOpacity: 0.8,
              labelOffsetY: -6,
            };
          },
          state: {
            active: {
              stroke: HIGHLIGHT_COLOR,
              lineWidth: 2,
              labelFill: HIGHLIGHT_COLOR,
              labelOpacity: 1,
              opacity: 1,
              strokeOpacity: 1,
            },
            inactive: {
              strokeOpacity: 0.08,
              labelOpacity: 0.08,
            },
          },
        },
      });

      graphRef.current = graph;
      graph.setData(dataRef.current);
      graph.render().then(() => {
        if (graph.destroyed) {
          return;
        }
        graph.fitView(undefined, false);
        clearStates();
      });

      graph.on('node:click', (event) => {
        const id = String(event.target.id);
        focusNode(id);
        onNodeClickRef.current?.(id);
      });
      graph.on('node:pointerdown', (event) => {
        if (!onCreateEdgeRef.current || !linkModeRef.current) {
          return;
        }
        const isShift = event.shiftKey || event.originalEvent?.shiftKey;
        if (isShift || linkSourceRef.current) {
          return;
        }
        const sourceId = String(event.target.id);
        linkSourceRef.current = sourceId;
        cleanupLinkAssist();
        const sourcePosition = graph.getElementPosition(sourceId);
        graph.addNodeData([
          {
            id: LINK_ASSIST_NODE_ID,
            type: 'circle',
            style: {
              x: sourcePosition[0],
              y: sourcePosition[1],
              size: 1,
              visibility: 'hidden',
            },
          },
        ]);
        graph.addEdgeData([
          {
            id: LINK_ASSIST_EDGE_ID,
            source: sourceId,
            target: LINK_ASSIST_NODE_ID,
            style: {
              stroke: HIGHLIGHT_COLOR,
              lineDash: [4, 4],
              endArrow: true,
              endArrowType: 'triangle',
              endArrowSize: 8,
              pointerEvents: 'none',
            },
          },
        ]);
        graph.draw();
        graph.getCanvas().setCursor('crosshair');
      });
      const handlePointerMove = (event: {
        canvas?: { x: number; y: number };
        canvasX?: number;
        canvasY?: number;
        x?: number;
        y?: number;
        client?: { x: number; y: number };
        clientX?: number;
        clientY?: number;
      }) => {
        if (!linkSourceRef.current || !linkModeRef.current) {
          return;
        }
        const point = getCanvasPoint(graph, event);
        if (!point) {
          return;
        }
        graph.translateElementTo(LINK_ASSIST_NODE_ID, point, false);
      };
      const handlePointerUp = (event: {
        targetType?: string;
        target?: { id?: string };
      }) => {
        if (!linkSourceRef.current || !linkModeRef.current) {
          return;
        }
        const sourceId = linkSourceRef.current;
        const targetId =
          event.targetType === 'node' && event.target?.id ? String(event.target.id) : null;
        cleanupLinkAssist();
        linkSourceRef.current = null;
        graph.getCanvas().setCursor('default');
        if (!targetId) {
          return;
        }
        const edgeId = `link-${sourceId}-${targetId}-${Date.now()}`;
        graph.addEdgeData([
          {
            id: edgeId,
            source: sourceId,
            target: targetId,
            style: {
              stroke: EDGE_COLOR,
              lineWidth: 1.4,
              endArrow: true,
              endArrowType: 'triangle',
              endArrowSize: 10,
              endArrowFill: EDGE_COLOR,
            },
          },
        ]);
        graph.draw();
        onCreateEdgeRef.current?.({
          id: edgeId,
          source: sourceId,
          target: targetId,
        });
      };
      graph.on('canvas:pointermove', handlePointerMove);
      graph.on('node:pointermove', handlePointerMove);
      graph.on('edge:pointermove', handlePointerMove);
      graph.on('canvas:pointerup', handlePointerUp);
      graph.on('node:pointerup', handlePointerUp);
      graph.on('edge:pointerup', handlePointerUp);
      graph.on('node:dblclick', (event) => {
        const id = String(event.target.id);
        onNodeDoubleClickRef.current?.(id);
      });
      graph.on('edge:click', (event) => {
        const id = String(event.target.id);
        onEdgeClickRef.current?.(id);
      });
      graph.on('canvas:click', (event) => {
        if (!event.targetType || event.targetType === 'canvas') {
          clearStates();
        }
      });
      graph.on('node:pointerenter', () => {
        if (linkSourceRef.current || linkModeRef.current) {
          return;
        }
        if (containerRef.current) {
          containerRef.current.style.cursor = 'pointer';
        }
      });
      graph.on('node:pointerleave', () => {
        if (linkSourceRef.current || linkModeRef.current) {
          return;
        }
        if (containerRef.current) {
          containerRef.current.style.cursor = 'default';
        }
      });

      return () => {
        graph.destroy();
        graphRef.current = null;
      };
    }, []);

    useEffect(() => {
      if (!containerRef.current) {
        return;
      }

      const observer = new ResizeObserver((entries) => {
        const entry = entries[0];
        if (!entry || !graphRef.current) {
          return;
        }
        const { width, height } = entry.contentRect;
        if (!width || !height) {
          return;
        }
        graphRef.current.setSize(width, height);
      });

      observer.observe(containerRef.current);
      return () => observer.disconnect();
    }, []);

    return (
      <div
        ref={containerRef}
        style={{
          width: '100%',
          height: 640,
          background: CANVAS_BACKGROUND,
          border: `1px solid ${CANVAS_BORDER}`,
          borderRadius: 12,
        }}
      />
    );
  }
);

export default GraphCanvas;
