import { forwardRef, useEffect, useImperativeHandle, useRef } from 'react';
import Graph, { MultiDirectedGraph } from 'graphology';
import forceAtlas2 from 'graphology-layout-forceatlas2';
import Sigma from 'sigma';
import type { GraphData, EdgeData } from '@/types/graph';

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

type NodeState = 'selected' | 'active' | 'inactive';
type EdgeState = 'active' | 'inactive';

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

const NODE_SIZE = 12;
const EDGE_COLOR = '#94a3b8';
const EDGE_LABEL_COLOR = '#475569';
const HIGHLIGHT_COLOR = '#faad14';
const CANVAS_BACKGROUND = '#f8fafc';
const CANVAS_BORDER = '#e2e8f0';

const LINK_ASSIST_NODE_ID = 'graph-link-assist-node';
const LINK_ASSIST_EDGE_ID = 'graph-link-assist-edge';

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

const GraphCanvas = forwardRef<GraphCanvasHandle, GraphCanvasProps>(
  ({ data, linkMode = false, onCreateEdge, onEdgeClick, onNodeDoubleClick, onNodeClick }, ref) => {
    const containerRef = useRef<HTMLDivElement | null>(null);
    const graphRef = useRef<Graph | null>(null);
    const sigmaRef = useRef<Sigma | null>(null);
    const dataRef = useRef<GraphData>(data);
    const adjacencyRef = useRef<Map<string, { neighbors: Set<string>; edges: Set<string> }>>(
      new Map()
    );
    const focusRef = useRef<string | null>(null);
    const linkSourceRef = useRef<string | null>(null);
    const linkPrimedRef = useRef<boolean>(false);
    const draggingNodeRef = useRef<string | null>(null);
    const hoverNodeRef = useRef<string | null>(null);
    const linkModeRef = useRef<boolean>(linkMode);
    const onCreateEdgeRef = useRef<GraphCanvasProps['onCreateEdge']>(onCreateEdge);
    const onEdgeClickRef = useRef<GraphCanvasProps['onEdgeClick']>(onEdgeClick);
    const onNodeDoubleClickRef = useRef<GraphCanvasProps['onNodeDoubleClick']>(
      onNodeDoubleClick
    );
    const onNodeClickRef = useRef<GraphCanvasProps['onNodeClick']>(onNodeClick);
    const nodeStateRef = useRef<Map<string, NodeState>>(new Map());
    const edgeStateRef = useRef<Map<string, EdgeState>>(new Map());

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
        linkPrimedRef.current = false;
        sigmaRef.current?.getCamera().enable();
        if (containerRef.current) {
          containerRef.current.style.cursor = 'default';
        }
      }
    }, [linkMode]);

    const applyStates = (nodes: Map<string, NodeState>, edges: Map<string, EdgeState>) => {
      nodeStateRef.current = nodes;
      edgeStateRef.current = edges;
      sigmaRef.current?.refresh();
    };

    const clearStates = () => {
      focusRef.current = null;
      applyStates(new Map(), new Map());
    };

    const focusNode = (nodeId: string) => {
      if (focusRef.current === nodeId) {
        clearStates();
        return;
      }

      const visited = new Set<string>([nodeId]);
      const queue: string[] = [nodeId];
      while (queue.length > 0) {
        const current = queue.shift();
        if (!current) {
          continue;
        }
        const entry = adjacencyRef.current.get(current);
        if (!entry) {
          continue;
        }
        entry.neighbors.forEach((neighbor) => {
          if (!visited.has(neighbor)) {
            visited.add(neighbor);
            queue.push(neighbor);
          }
        });
      }

      const nextNodeStates = new Map<string, NodeState>();
      (dataRef.current.nodes ?? []).forEach((node) => {
        const id = String(node.id);
        if (visited.has(id)) {
          nextNodeStates.set(id, id === nodeId ? 'selected' : 'active');
        } else {
          nextNodeStates.set(id, 'inactive');
        }
      });

      const nextEdgeStates = new Map<string, EdgeState>();
      (dataRef.current.edges ?? []).forEach((edge) => {
        if (!edge.id) {
          return;
        }
        const id = String(edge.id);
        const source = String(edge.source);
        const target = String(edge.target);
        if (visited.has(source) && visited.has(target)) {
          nextEdgeStates.set(id, 'active');
        } else {
          nextEdgeStates.set(id, 'inactive');
        }
      });

      focusRef.current = nodeId;
      applyStates(nextNodeStates, nextEdgeStates);
    };

    const cleanupLinkAssist = () => {
      if (!graphRef.current) {
        return;
      }
      try {
        if (graphRef.current.hasEdge(LINK_ASSIST_EDGE_ID)) {
          graphRef.current.dropEdge(LINK_ASSIST_EDGE_ID);
        }
      } catch (error) {
        // Ignore missing assist edge.
      }
      try {
        if (graphRef.current.hasNode(LINK_ASSIST_NODE_ID)) {
          graphRef.current.dropNode(LINK_ASSIST_NODE_ID);
        }
      } catch (error) {
        // Ignore missing assist node.
      }
      sigmaRef.current?.refresh();
    };

    const buildGraph = (nextData: GraphData) => {
      const graph = new MultiDirectedGraph();
      (nextData.nodes ?? []).forEach((node) => {
        const id = String(node.id);
        if (graph.hasNode(id)) {
          return;
        }
        const color = getNodeColor(node.data?.type);
        graph.addNode(id, {
          label: node.data?.label ?? id,
          size: NODE_SIZE,
          color,
          type: 'circle',
          x: Math.random() * 200 - 100,
          y: Math.random() * 200 - 100,
          data: node.data,
        });
      });

      (nextData.edges ?? []).forEach((edge, index) => {
        const source = String(edge.source);
        const target = String(edge.target);
        const edgeId = edge.id ? String(edge.id) : `${source}-${target}-${index}`;
        if (!graph.hasNode(source) || !graph.hasNode(target)) {
          return;
        }
        if (graph.hasEdge(edgeId)) {
          return;
        }
        graph.addDirectedEdgeWithKey(edgeId, source, target, {
          label: edge.data?.label ?? '',
          size: 1.4,
          color: EDGE_COLOR,
          type: 'arrow',
          data: edge.data,
        });
      });

      if ((nextData.nodes ?? []).length > 1) {
        const settings = forceAtlas2.inferSettings(graph);
        forceAtlas2.assign(graph, {
          iterations: 120,
          settings: {
            ...settings,
            gravity: 1,
            scalingRatio: 2,
            slowDown: 10,
          },
        });
      }

      return graph;
    };

    const ensureLinkAssist = (sourceId: string) => {
      if (!graphRef.current) {
        return;
      }
      const graph = graphRef.current;
      const sourceAttributes = graph.getNodeAttributes(sourceId) as {
        x: number;
        y: number;
      };

      if (graph.hasNode(LINK_ASSIST_NODE_ID)) {
        graph.dropNode(LINK_ASSIST_NODE_ID);
      }
      if (graph.hasEdge(LINK_ASSIST_EDGE_ID)) {
        graph.dropEdge(LINK_ASSIST_EDGE_ID);
      }

      graph.addNode(LINK_ASSIST_NODE_ID, {
        label: '',
        size: 0.1,
        color: 'rgba(0,0,0,0)',
        type: 'circle',
        x: sourceAttributes.x,
        y: sourceAttributes.y,
        isAssist: true,
      });
      graph.addDirectedEdgeWithKey(LINK_ASSIST_EDGE_ID, sourceId, LINK_ASSIST_NODE_ID, {
        label: '',
        size: 1.2,
        color: HIGHLIGHT_COLOR,
        type: 'line',
        isAssist: true,
      });
      sigmaRef.current?.refresh();
    };

    const updateLinkAssistPosition = (point: { x: number; y: number }) => {
      if (!graphRef.current || !graphRef.current.hasNode(LINK_ASSIST_NODE_ID)) {
        return;
      }
      graphRef.current.setNodeAttribute(LINK_ASSIST_NODE_ID, 'x', point.x);
      graphRef.current.setNodeAttribute(LINK_ASSIST_NODE_ID, 'y', point.y);
      sigmaRef.current?.refresh();
    };

    const finalizeLink = (targetId: string) => {
      const sourceId = linkSourceRef.current;
      cleanupLinkAssist();
      linkSourceRef.current = null;
      linkPrimedRef.current = false;
      sigmaRef.current?.getCamera().enable();
      if (containerRef.current) {
        containerRef.current.style.cursor = 'default';
      }

      if (!sourceId || !graphRef.current) {
        return;
      }
      const edgeId = `link-${sourceId}-${targetId}-${Date.now()}`;
      try {
        graphRef.current.addDirectedEdgeWithKey(edgeId, sourceId, targetId, {
          label: '',
          size: 1.4,
          color: EDGE_COLOR,
          type: 'arrow',
        });
        sigmaRef.current?.refresh();
      } catch (error) {
        return;
      }
      onCreateEdgeRef.current?.({
        id: edgeId,
        source: sourceId,
        target: targetId,
      });
    };

    const cancelLink = () => {
      cleanupLinkAssist();
      linkSourceRef.current = null;
      linkPrimedRef.current = false;
      sigmaRef.current?.getCamera().enable();
      if (containerRef.current) {
        containerRef.current.style.cursor = 'default';
      }
    };

    useImperativeHandle(ref, () => ({
      removeEdge: (edgeId: string) => {
        if (!edgeId || !graphRef.current) {
          return;
        }
        try {
          if (!graphRef.current.hasEdge(edgeId)) {
            return;
          }
          graphRef.current.dropEdge(edgeId);
          sigmaRef.current?.refresh();
        } catch (error) {
          // Ignore missing edges or transient graph sync issues.
        }
      },
    }));

    useEffect(() => {
      dataRef.current = data;
      adjacencyRef.current = buildAdjacency(data);
      cancelLink();
      if (!sigmaRef.current) {
        return;
      }
      const graph = buildGraph(data);
      graphRef.current = graph;
      sigmaRef.current.setGraph(graph);
      sigmaRef.current.getCamera().animatedReset();
      clearStates();
    }, [data]);

    useEffect(() => {
      if (!containerRef.current || sigmaRef.current) {
        return;
      }

      const container = containerRef.current;
      const graph = buildGraph(dataRef.current);
      graphRef.current = graph;

      const sigma = new Sigma(graph, container, {
        renderLabels: true,
        renderEdgeLabels: true,
        labelFont: 'system-ui, -apple-system, Segoe UI, Roboto, sans-serif',
        labelSize: 12,
        labelWeight: '500',
        labelColor: { color: '#0f172a' },
        edgeLabelColor: { color: EDGE_LABEL_COLOR },
        defaultNodeColor: NODE_COLORS.default,
        defaultEdgeColor: EDGE_COLOR,
        enableEdgeClickEvents: true,
        nodeReducer: (node, data) => {
          const next = { ...data };
          if (next.isAssist) {
            next.color = 'rgba(0,0,0,0)';
            next.label = null;
            next.size = 0.1;
            return next;
          }
          const state = nodeStateRef.current.get(node);
          if (state === 'inactive') {
            next.color = '#e2e8f0';
            next.label = null;
            return next;
          }
          if (state === 'selected') {
            next.color = HIGHLIGHT_COLOR;
            next.size = NODE_SIZE * 1.25;
            next.zIndex = 2;
            return next;
          }
          if (state === 'active') {
            next.color = HIGHLIGHT_COLOR;
            next.size = NODE_SIZE * 1.05;
            next.zIndex = 1;
            return next;
          }
          return next;
        },
        edgeReducer: (edge, data) => {
          const next = { ...data };
          if (next.isAssist) {
            next.color = HIGHLIGHT_COLOR;
            next.size = 1.2;
            return next;
          }
          const state = edgeStateRef.current.get(edge);
          if (state === 'inactive') {
            next.color = '#e2e8f0';
            next.label = null;
            return next;
          }
          if (state === 'active') {
            next.color = HIGHLIGHT_COLOR;
            next.size = 2;
            return next;
          }
          return next;
        },
      });

      sigmaRef.current = sigma;
      sigma.getCamera().animatedReset();

      sigma.on('enterNode', (payload) => {
        hoverNodeRef.current = payload.node;
        if (linkSourceRef.current || linkModeRef.current) {
          return;
        }
        if (containerRef.current) {
          containerRef.current.style.cursor = 'pointer';
        }
      });
      sigma.on('leaveNode', (payload) => {
        if (hoverNodeRef.current === payload.node) {
          hoverNodeRef.current = null;
        }
        if (linkSourceRef.current || linkModeRef.current) {
          return;
        }
        if (containerRef.current) {
          containerRef.current.style.cursor = 'default';
        }
      });
      sigma.on('clickNode', (payload) => {
        const id = payload.node;
        if (linkModeRef.current && linkSourceRef.current) {
          if (linkPrimedRef.current && linkSourceRef.current === id) {
            linkPrimedRef.current = false;
            focusNode(id);
            onNodeClickRef.current?.(id);
            return;
          }
          finalizeLink(id);
          focusNode(id);
          onNodeClickRef.current?.(id);
          return;
        }
        focusNode(id);
        onNodeClickRef.current?.(id);
      });
      sigma.on('doubleClickNode', (payload) => {
        payload.preventSigmaDefault();
        const id = payload.node;
        onNodeDoubleClickRef.current?.(id);
      });
      sigma.on('clickEdge', (payload) => {
        onEdgeClickRef.current?.(payload.edge);
      });
      sigma.on('clickStage', () => {
        if (linkSourceRef.current) {
          cancelLink();
          return;
        }
        clearStates();
      });
      sigma.on('downNode', (payload) => {
        const id = payload.node;
        const isShift = !!payload.event.original?.shiftKey;
        if (linkModeRef.current && !isShift && !linkSourceRef.current) {
          linkSourceRef.current = id;
          linkPrimedRef.current = true;
          ensureLinkAssist(id);
          sigma.getCamera().disable();
          if (containerRef.current) {
            containerRef.current.style.cursor = 'crosshair';
          }
          return;
        }
        if (!linkModeRef.current || isShift) {
          draggingNodeRef.current = id;
          sigma.getCamera().disable();
        }
      });

      const mouseCaptor = sigma.getMouseCaptor();
      mouseCaptor.on('mousemovebody', (event) => {
        if (!sigmaRef.current) {
          return;
        }
        const point = sigmaRef.current.viewportToGraph({ x: event.x, y: event.y });
        if (draggingNodeRef.current && graphRef.current) {
          graphRef.current.setNodeAttribute(draggingNodeRef.current, 'x', point.x);
          graphRef.current.setNodeAttribute(draggingNodeRef.current, 'y', point.y);
          sigmaRef.current.refresh();
          return;
        }
        if (linkSourceRef.current) {
          updateLinkAssistPosition(point);
        }
      });
      mouseCaptor.on('mouseup', () => {
        if (draggingNodeRef.current) {
          draggingNodeRef.current = null;
          sigma.getCamera().enable();
        }
      });

      return () => {
        mouseCaptor.removeAllListeners();
        sigma.kill();
        sigmaRef.current = null;
        graphRef.current = null;
      };
    }, []);

    useEffect(() => {
      if (!containerRef.current) {
        return;
      }

      const observer = new ResizeObserver(() => {
        if (!sigmaRef.current) {
          return;
        }
        sigmaRef.current.resize();
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
