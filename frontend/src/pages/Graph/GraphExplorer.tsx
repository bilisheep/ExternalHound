import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Button,
  Card,
  Collapse,
  Descriptions,
  Drawer,
  Empty,
  Form,
  Input,
  Modal,
  Row,
  Col,
  Select,
  Space,
  Spin,
  Switch,
  message,
} from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import type { EdgeData, GraphData, NodeData } from '@/types/graph';
import {
  useAllAssets,
  useUpdateCertificate,
  useUpdateClientApplication,
  useUpdateCredential,
  useUpdateDomain,
  useUpdateIP,
  useUpdateNetblock,
  useUpdateOrganization,
  useUpdateService,
} from '@/hooks/useAssets';
import {
  useAllRelationships,
  useCreateRelationship,
  useDeleteRelationship,
  useUpdateRelationship,
} from '@/hooks/useRelationships';
import type {
  NodeType,
  RelationshipCreatePayload,
  RelationshipRecord,
  RelationshipType,
  RelationshipUpdatePayload,
} from '@/types/relationship';
import type {
  CertificateUpdatePayload,
  ClientApplicationUpdatePayload,
  CredentialUpdatePayload,
  DomainUpdatePayload,
  IPUpdatePayload,
  NetblockUpdatePayload,
  OrganizationUpdatePayload,
  ServiceUpdatePayload,
} from '@/types/asset';
import { nodeTypeOptions, relationshipRules, relationshipTypeOptions } from '@/constants/relationships';
import { useI18n } from '@/i18n';
import GraphCanvas, { type GraphCanvasHandle } from '@/components/Graph/GraphCanvas';
import { cleanPayload } from '@/utils/forms';
import { formatJson, safeParseJson } from '@/utils/json';

type EdgeDraft = {
  edgeId: string;
  sourceType: NodeType;
  sourceExternalId: string;
  targetType: NodeType;
  targetExternalId: string;
};

type NodeEditDraft = {
  nodeId: string;
  nodeType: NodeType;
  externalId: string;
  assetId: string;
  metadata: Record<string, unknown>;
};

const GraphExplorer = () => {
  const { t } = useI18n();
  const graphRef = useRef<GraphCanvasHandle | null>(null);
  const [createRelationshipForm] = Form.useForm();
  const [editRelationshipForm] = Form.useForm();
  const [editNodeForm] = Form.useForm();
  const [isLinkMode, setIsLinkMode] = useState(false);

  const defaultRelationshipFilters = {
    source_external_id: undefined as string | undefined,
    source_type: undefined as NodeType | undefined,
    target_external_id: undefined as string | undefined,
    target_type: undefined as NodeType | undefined,
    relation_type: undefined as RelationshipType | undefined,
    edge_key: undefined as string | undefined,
    include_deleted: undefined as boolean | undefined,
  };
  const [filters, setFilters] = useState(defaultRelationshipFilters);
  const [draftEdge, setDraftEdge] = useState<EdgeDraft | null>(null);
  const [isFilterDrawerOpen, setIsFilterDrawerOpen] = useState(false);
  const [isCreateRelationshipOpen, setIsCreateRelationshipOpen] = useState(false);
  const [editingRelationship, setEditingRelationship] = useState<RelationshipRecord | null>(null);
  const [isEditRelationshipOpen, setIsEditRelationshipOpen] = useState(false);
  const [editingNode, setEditingNode] = useState<NodeEditDraft | null>(null);
  const [isEditNodeOpen, setIsEditNodeOpen] = useState(false);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [relatedNodeId, setRelatedNodeId] = useState<string | null>(null);
  const [pathStartNodeId, setPathStartNodeId] = useState<string | null>(null);
  const [pathEndNodeId, setPathEndNodeId] = useState<string | null>(null);

  const updateFilters = (next: Partial<typeof filters>) => {
    setFilters((prev) => ({ ...prev, ...next }));
  };

  const {
    data: allRelationships,
    isLoading: relationshipsLoading,
    isFetching: relationshipsFetching,
    refetch: refetchRelationships,
  } = useAllRelationships(filters);
  const {
    data: allAssets,
    isLoading: assetsLoading,
    isFetching: assetsFetching,
    refetch: refetchAssets,
  } = useAllAssets();
  const createRelationshipMutation = useCreateRelationship();
  const updateRelationshipMutation = useUpdateRelationship();
  const deleteRelationshipMutation = useDeleteRelationship();
  const updateIPMutation = useUpdateIP();
  const updateDomainMutation = useUpdateDomain();
  const updateServiceMutation = useUpdateService();
  const updateOrganizationMutation = useUpdateOrganization();
  const updateNetblockMutation = useUpdateNetblock();
  const updateCertificateMutation = useUpdateCertificate();
  const updateClientApplicationMutation = useUpdateClientApplication();
  const updateCredentialMutation = useUpdateCredential();

  const relationshipTypeLabel = useCallback(
    (value: RelationshipType) => t(`relationshipType.${value}`),
    [t]
  );
  const relationshipTypeOptionsForEdge = useMemo(() => {
    if (!draftEdge) {
      return relationshipTypeOptions;
    }
    return relationshipTypeOptions.filter((option) => {
      const rule = relationshipRules[option];
      if (!rule) {
        return false;
      }
      return rule.source === draftEdge.sourceType && rule.target === draftEdge.targetType;
    });
  }, [draftEdge]);

  const relationshipById = useMemo(() => {
    const map = new Map<string, RelationshipRecord>();
    (allRelationships ?? []).forEach((relationship) => {
      map.set(relationship.id, relationship);
    });
    return map;
  }, [allRelationships]);

  const assetByNodeId = useMemo(() => {
    const map = new Map<string, NodeEditDraft>();
    if (!allAssets) {
      return map;
    }

    const addAsset = (
      nodeType: NodeType,
      asset: { id: string; external_id: string; metadata: Record<string, unknown> }
    ) => {
      const nodeId = `${nodeType}:${asset.external_id}`;
      map.set(nodeId, {
        nodeId,
        nodeType,
        externalId: asset.external_id,
        assetId: asset.id,
        metadata: asset.metadata,
      });
    };

    allAssets.organizations.forEach((asset) => addAsset('Organization', asset));
    allAssets.domains.forEach((asset) => addAsset('Domain', asset));
    allAssets.ips.forEach((asset) => addAsset('IP', asset));
    allAssets.netblocks.forEach((asset) => addAsset('Netblock', asset));
    allAssets.services.forEach((asset) => addAsset('Service', asset));
    allAssets.certificates.forEach((asset) => addAsset('Certificate', asset));
    allAssets.clientApplications.forEach((asset) => addAsset('ClientApplication', asset));
    allAssets.credentials.forEach((asset) => addAsset('Credential', asset));

    return map;
  }, [allAssets]);

  const parseNodeId = (nodeId: string) => {
    const [type, ...rest] = nodeId.split(':');
    if (!type || rest.length === 0) {
      return null;
    }
    return { type: type as NodeType, externalId: rest.join(':') };
  };

  const selectedNodeInfo = useMemo(() => {
    if (!selectedNodeId) {
      return null;
    }
    const assetNode = assetByNodeId.get(selectedNodeId);
    if (assetNode) return assetNode;

    const parsed = parseNodeId(selectedNodeId);
    if (parsed) {
      return {
        nodeId: selectedNodeId,
        nodeType: parsed.type,
        externalId: parsed.externalId,
        assetId: '',
        metadata: {},
      } as NodeEditDraft;
    }
    return null;
  }, [selectedNodeId, assetByNodeId]);

  const handleNodeClick = (nodeId: string) => {
    setSelectedNodeId(nodeId);
  };

  const updateRelatedNode = (value?: string) => {
    const nextValue = value ?? null;
    setRelatedNodeId(nextValue);
    if (nextValue) {
      setPathStartNodeId(null);
      setPathEndNodeId(null);
    }
  };

  const updatePathStartNode = (value?: string) => {
    const nextValue = value ?? null;
    setPathStartNodeId(nextValue);
    if (nextValue) {
      setRelatedNodeId(null);
    }
  };

  const updatePathEndNode = (value?: string) => {
    const nextValue = value ?? null;
    setPathEndNodeId(nextValue);
    if (nextValue) {
      setRelatedNodeId(null);
    }
  };

  const clearRelationshipFilters = () => {
    setFilters({ ...defaultRelationshipFilters });
  };

  const clearViewFilters = () => {
    setRelatedNodeId(null);
    setPathStartNodeId(null);
    setPathEndNodeId(null);
  };


  const closeCreateRelationship = () => {
    const edgeId = draftEdge?.edgeId;
    setDraftEdge(null);
    setIsCreateRelationshipOpen(false);
    createRelationshipForm.resetFields();
    if (!edgeId) {
      return;
    }
    try {
      graphRef.current?.removeEdge(edgeId);
    } catch (error) {
      // Ignore cleanup errors to avoid blocking the modal close.
    }
  };

  const closeEditRelationship = () => {
    setEditingRelationship(null);
    setIsEditRelationshipOpen(false);
    editRelationshipForm.resetFields();
  };

  const closeEditNode = () => {
    setEditingNode(null);
    setIsEditNodeOpen(false);
    editNodeForm.resetFields();
  };

  const getNodeUpdateMutation = (nodeType: NodeType) => {
    switch (nodeType) {
      case 'IP':
        return updateIPMutation;
      case 'Domain':
        return updateDomainMutation;
      case 'Service':
        return updateServiceMutation;
      case 'Organization':
        return updateOrganizationMutation;
      case 'Netblock':
        return updateNetblockMutation;
      case 'Certificate':
        return updateCertificateMutation;
      case 'ClientApplication':
        return updateClientApplicationMutation;
      case 'Credential':
        return updateCredentialMutation;
      default:
        return updateIPMutation;
    }
  };

  const handleCreateEdge = (edge: EdgeData) => {
    const edgeId = edge.id ? String(edge.id) : '';
    const sourceId = String(edge.source);
    const targetId = String(edge.target);
    const source = parseNodeId(sourceId);
    const target = parseNodeId(targetId);

    if (!edgeId || !source || !target) {
      message.error(t('errors.graph.invalidLink'));
      if (edgeId) {
        graphRef.current?.removeEdge(edgeId);
      }
      return;
    }

    if (sourceId === targetId) {
      message.warning(t('errors.graph.selfLink'));
      graphRef.current?.removeEdge(edgeId);
      return;
    }

    setDraftEdge({
      edgeId,
      sourceType: source.type,
      sourceExternalId: source.externalId,
      targetType: target.type,
      targetExternalId: target.externalId,
    });
    createRelationshipForm.resetFields();
    setIsCreateRelationshipOpen(true);
  };

  const handleEdgeClick = (edgeId: string) => {
    const relationship = relationshipById.get(edgeId);
    if (!relationship) {
      return;
    }
    setEditingRelationship(relationship);
    editRelationshipForm.setFieldsValue({
      properties: formatJson(relationship.properties),
    });
    setIsEditRelationshipOpen(true);
  };

  const handleNodeDoubleClick = (nodeId: string) => {
    const node = assetByNodeId.get(nodeId);
    if (!node) {
      message.warning(t('errors.graph.nodeMissing'));
      return;
    }
    setEditingNode(node);
    editNodeForm.setFieldsValue({
      metadata: formatJson(node.metadata),
    });
    setIsEditNodeOpen(true);
  };

  const handleCreateRelationship = (values: Record<string, unknown>) => {
    if (!draftEdge) {
      return;
    }

    const { value: propertiesValue, error } = safeParseJson(values.properties as string | undefined);
    if (error) {
      message.error(t('errors.json.properties'));
      return;
    }

    const payload = cleanPayload({
      source_external_id: draftEdge.sourceExternalId,
      source_type: draftEdge.sourceType,
      target_external_id: draftEdge.targetExternalId,
      target_type: draftEdge.targetType,
      relation_type: values.relation_type,
      edge_key: values.edge_key,
      properties: propertiesValue,
      created_by: values.created_by,
    });

    createRelationshipMutation.mutate(payload as RelationshipCreatePayload, {
      onSuccess: () => {
        closeCreateRelationship();
        refetchRelationships();
      },
    });
  };

  const handleUpdateRelationship = (values: Record<string, unknown>) => {
    if (!editingRelationship) {
      return;
    }

    const { value: propertiesValue, error } = safeParseJson(values.properties as string | undefined);
    if (error) {
      message.error(t('errors.json.properties'));
      return;
    }

    const payload = cleanPayload({
      properties: propertiesValue,
    });

    updateRelationshipMutation.mutate(
      { id: editingRelationship.id, payload: payload as RelationshipUpdatePayload },
      {
        onSuccess: () => {
          closeEditRelationship();
          refetchRelationships();
        },
      }
    );
  };

  const handleDeleteRelationship = () => {
    if (!editingRelationship) {
      return;
    }
    deleteRelationshipMutation.mutate(editingRelationship.id, {
      onSuccess: () => {
        closeEditRelationship();
        refetchRelationships();
      },
    });
  };

  const handleUpdateNode = (values: Record<string, unknown>) => {
    if (!editingNode) {
      return;
    }

    const { value: metadataValue, error } = safeParseJson(values.metadata as string | undefined);
    if (error) {
      message.error(t('errors.json.metadata'));
      return;
    }

    const payload = cleanPayload({
      metadata: metadataValue,
    });
    const mutation = getNodeUpdateMutation(editingNode.nodeType);

    mutation.mutate(
      {
        id: editingNode.assetId,
        payload: payload as
          | IPUpdatePayload
          | DomainUpdatePayload
          | ServiceUpdatePayload
          | OrganizationUpdatePayload
          | NetblockUpdatePayload
          | CertificateUpdatePayload
          | ClientApplicationUpdatePayload
          | CredentialUpdatePayload,
      },
      {
        onSuccess: () => {
          closeEditNode();
          refetchAssets();
        },
      }
    );
  };

  const activeNodeMutation = editingNode ? getNodeUpdateMutation(editingNode.nodeType) : null;

  const baseGraphData = useMemo<GraphData>(() => {
    const nodes = new Map<string, NodeData>();
    const edges: EdgeData[] = [];
    const addNode = (type: NodeType, externalId: string, label: string) => {
      const id = `${type}:${externalId}`;
      if (nodes.has(id)) {
        return;
      }
      nodes.set(id, {
        id,
        data: {
          type,
          external_id: externalId,
          label,
        },
      });
    };

    if (allAssets) {
      allAssets.organizations.forEach((organization) => {
        addNode(
          'Organization',
          organization.external_id,
          organization.name || organization.external_id
        );
      });
      allAssets.domains.forEach((domain) => {
        addNode('Domain', domain.external_id, domain.name || domain.external_id);
      });
      allAssets.ips.forEach((ip) => {
        addNode('IP', ip.external_id, ip.address || ip.external_id);
      });
      allAssets.netblocks.forEach((netblock) => {
        addNode('Netblock', netblock.external_id, netblock.cidr || netblock.external_id);
      });
      allAssets.services.forEach((service) => {
        const label =
          service.product ||
          service.service_name ||
          `${service.port}/${service.protocol}` ||
          service.external_id;
        addNode('Service', service.external_id, label);
      });
      allAssets.certificates.forEach((certificate) => {
        addNode(
          'Certificate',
          certificate.external_id,
          certificate.subject_cn || certificate.external_id
        );
      });
      allAssets.clientApplications.forEach((clientApp) => {
        addNode(
          'ClientApplication',
          clientApp.external_id,
          clientApp.app_name || clientApp.package_name || clientApp.external_id
        );
      });
      allAssets.credentials.forEach((credential) => {
        addNode(
          'Credential',
          credential.external_id,
          credential.username ||
            credential.email ||
            credential.phone ||
            credential.external_id
        );
      });
    }

    (allRelationships ?? []).forEach((relationship) => {
      addNode(
        relationship.source_type,
        relationship.source_external_id,
        relationship.source_external_id
      );
      addNode(
        relationship.target_type,
        relationship.target_external_id,
        relationship.target_external_id
      );

      edges.push({
        id: relationship.id,
        source: `${relationship.source_type}:${relationship.source_external_id}`,
        target: `${relationship.target_type}:${relationship.target_external_id}`,
        data: {
          relation_type: relationship.relation_type,
          edge_key: relationship.edge_key,
          label: relationshipTypeLabel(relationship.relation_type),
        },
      });
    });

    return {
      nodes: Array.from(nodes.values()),
      edges,
    };
  }, [allAssets, allRelationships, relationshipTypeLabel]);

  const nodeSelectOptions = useMemo(() => {
    return (baseGraphData.nodes ?? [])
      .map((node) => {
        const nodeType = node.data?.type as NodeType | undefined;
        const typeLabel = nodeType ? t(`nodeType.${nodeType}`) : nodeType ?? 'Unknown';
        const label = node.data?.label ?? String(node.id);
        return {
          value: String(node.id),
          label: `${typeLabel} / ${label}`,
          search: `${typeLabel} ${label} ${String(node.id)}`.toLowerCase(),
        };
      })
      .sort((a, b) => a.label.localeCompare(b.label));
  }, [baseGraphData.nodes, t]);

  const filterNodeOption = (input: string, option?: { search?: string }) =>
    (option?.search ?? '').includes(input.toLowerCase());

  const graphData = useMemo<GraphData>(() => {
    const nodes = baseGraphData.nodes ?? [];
    const edges = baseGraphData.edges ?? [];
    if (!nodes.length) {
      return baseGraphData;
    }

    if (relatedNodeId) {
      const relatedEdges = edges.filter(
        (edge) => String(edge.source) === relatedNodeId || String(edge.target) === relatedNodeId
      );
      const relatedNodeIds = new Set<string>([relatedNodeId]);
      relatedEdges.forEach((edge) => {
        relatedNodeIds.add(String(edge.source));
        relatedNodeIds.add(String(edge.target));
      });
      return {
        nodes: nodes.filter((node) => relatedNodeIds.has(String(node.id))),
        edges: relatedEdges,
      };
    }

    if (pathStartNodeId && pathEndNodeId) {
      if (pathStartNodeId === pathEndNodeId) {
        return {
          nodes: nodes.filter((node) => String(node.id) === pathStartNodeId),
          edges: [],
        };
      }

      const getEdgeKey = (edge: EdgeData) =>
        edge.id ? String(edge.id) : `${String(edge.source)}-${String(edge.target)}`;
      const adjacency = new Map<string, Array<{ target: string; edgeId: string }>>();
      edges.forEach((edge) => {
        const source = String(edge.source);
        const target = String(edge.target);
        const edgeId = getEdgeKey(edge);
        const list = adjacency.get(source) ?? [];
        list.push({ target, edgeId });
        adjacency.set(source, list);
      });

      const queue: string[] = [pathStartNodeId];
      const visited = new Set<string>([pathStartNodeId]);
      const previous = new Map<string, { nodeId: string; edgeId: string }>();
      let found = false;

      while (queue.length > 0 && !found) {
        const current = queue.shift();
        if (!current) {
          continue;
        }
        const neighbors = adjacency.get(current) ?? [];
        for (const { target, edgeId } of neighbors) {
          if (visited.has(target)) {
            continue;
          }
          visited.add(target);
          previous.set(target, { nodeId: current, edgeId });
          if (target === pathEndNodeId) {
            found = true;
            break;
          }
          queue.push(target);
        }
      }

      if (!found) {
        return { nodes: [], edges: [] };
      }

      const pathNodeIds = new Set<string>([pathEndNodeId]);
      const pathEdgeIds = new Set<string>();
      let cursor = pathEndNodeId;
      while (cursor !== pathStartNodeId) {
        const step = previous.get(cursor);
        if (!step) {
          return { nodes: [], edges: [] };
        }
        pathEdgeIds.add(step.edgeId);
        pathNodeIds.add(step.nodeId);
        cursor = step.nodeId;
      }

      return {
        nodes: nodes.filter((node) => pathNodeIds.has(String(node.id))),
        edges: edges.filter((edge) => pathEdgeIds.has(getEdgeKey(edge))),
      };
    }

    return baseGraphData;
  }, [baseGraphData, relatedNodeId, pathStartNodeId, pathEndNodeId]);

  useEffect(() => {
    if (!selectedNodeId) {
      return;
    }
    const exists = (graphData.nodes ?? []).some((node) => String(node.id) === selectedNodeId);
    if (!exists) {
      setSelectedNodeId(null);
    }
  }, [graphData.nodes, selectedNodeId]);

  // Styles
  const filterLabelStyle = {
    fontSize: 12,
    fontWeight: 500,
    color: '#64748b',
  };

  const detailLabelStyle = {
    color: '#64748b',
    fontSize: 12,
  };

  const detailContentStyle = {
    color: '#0f172a',
    fontSize: 13,
  };

  return (
    <div style={{ width: '100%', height: '100vh', padding: 24, boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 16 }}>
        {/* Toolbar */}
        <Card
          size="small"
          style={{
            borderRadius: 12,
            borderColor: '#e2e8f0',
          }}
          styles={{
            body: { padding: '8px 16px' },
          }}
        >
          <Row align="middle" justify="space-between" style={{ width: '100%' }} wrap gutter={[12, 8]}>
            <Col>
              <Space size={12} wrap>
                <Button size="small" onClick={() => setIsFilterDrawerOpen(true)}>
                  {t('graph.filters')}
                </Button>
              </Space>
            </Col>
            <Col>
              <Space size={12} wrap>
                <Space size={8}>
                  <span style={filterLabelStyle}>
                    {t(isLinkMode ? 'graph.linkMode' : 'graph.dragMode')}
                  </span>
                  <Switch checked={isLinkMode} onChange={setIsLinkMode} />
                </Space>
                <Button
                  size="small"
                  icon={<ReloadOutlined />}
                  onClick={() => {
                    refetchRelationships();
                    refetchAssets();
                  }}
                >
                  {t('common.refresh')}
                </Button>
              </Space>
            </Col>
          </Row>
        </Card>

        {/* Graph Card */}
        <Card
          title={t('menu.graph')}
          className="graph-card"
          style={{ flex: 1, minHeight: 0 }}
          styles={{ body: { padding: 0 } }}
        >
          <div style={{ height: '100%', position: 'relative' }}>
            <Spin
              spinning={relationshipsLoading || relationshipsFetching || assetsLoading || assetsFetching}
              wrapperClassName="graph-spin-wrapper"
            >
              <div style={{ height: '100%' }}>
                {graphData.nodes && graphData.nodes.length > 0 ? (
                  <GraphCanvas
                    ref={graphRef}
                    data={graphData}
                    linkMode={isLinkMode}
                    onCreateEdge={handleCreateEdge}
                    onEdgeClick={handleEdgeClick}
                    onNodeDoubleClick={handleNodeDoubleClick}
                    onNodeClick={handleNodeClick}
                  />
                ) : (
                  <Empty style={{ padding: 32 }} />
                )}
              </div>
            </Spin>
          </div>
        </Card>
      </div>

      {/* Filter Drawer */}
      <Drawer
        title={t('graph.filters')}
        placement="left"
        width={400}
        open={isFilterDrawerOpen}
        onClose={() => setIsFilterDrawerOpen(false)}
        styles={{ body: { padding: 16 } }}
      >
        <Form layout="vertical" requiredMark={false} colon={false} size="small">
          <Collapse
            bordered={false}
            defaultActiveKey={['relationship', 'view']}
            items={[
              {
                key: 'relationship',
                label: t('graph.relationshipFilters'),
                children: (
                  <Space direction="vertical" size={12} style={{ width: '100%' }}>
                    <Form.Item
                      label={<span style={filterLabelStyle}>{t('fields.sourceExternalId')}</span>}
                      style={{ marginBottom: 0 }}
                    >
                      <Input
                        placeholder={t('fields.sourceExternalId')}
                        allowClear
                        value={filters.source_external_id ?? ''}
                        onChange={(event) =>
                          updateFilters({
                            source_external_id: event.target.value || undefined,
                          })
                        }
                      />
                    </Form.Item>
                    <Form.Item
                      label={<span style={filterLabelStyle}>{t('fields.sourceType')}</span>}
                      style={{ marginBottom: 0 }}
                    >
                      <Select
                        placeholder={t('fields.sourceType')}
                        allowClear
                        value={filters.source_type}
                        onChange={(value) => updateFilters({ source_type: value })}
                      >
                        {nodeTypeOptions.map((option) => (
                          <Select.Option key={option} value={option}>
                            {t(`nodeType.${option}`)}
                          </Select.Option>
                        ))}
                      </Select>
                    </Form.Item>
                    <Form.Item
                      label={<span style={filterLabelStyle}>{t('fields.targetExternalId')}</span>}
                      style={{ marginBottom: 0 }}
                    >
                      <Input
                        placeholder={t('fields.targetExternalId')}
                        allowClear
                        value={filters.target_external_id ?? ''}
                        onChange={(event) =>
                          updateFilters({
                            target_external_id: event.target.value || undefined,
                          })
                        }
                      />
                    </Form.Item>
                    <Form.Item
                      label={<span style={filterLabelStyle}>{t('fields.targetType')}</span>}
                      style={{ marginBottom: 0 }}
                    >
                      <Select
                        placeholder={t('fields.targetType')}
                        allowClear
                        value={filters.target_type}
                        onChange={(value) => updateFilters({ target_type: value })}
                      >
                        {nodeTypeOptions.map((option) => (
                          <Select.Option key={option} value={option}>
                            {t(`nodeType.${option}`)}
                          </Select.Option>
                        ))}
                      </Select>
                    </Form.Item>
                    <Form.Item
                      label={<span style={filterLabelStyle}>{t('fields.relationType')}</span>}
                      style={{ marginBottom: 0 }}
                    >
                      <Select
                        placeholder={t('fields.relationType')}
                        allowClear
                        value={filters.relation_type}
                        onChange={(value) => updateFilters({ relation_type: value })}
                      >
                        {relationshipTypeOptions.map((option) => (
                          <Select.Option key={option} value={option}>
                            {relationshipTypeLabel(option)}
                          </Select.Option>
                        ))}
                      </Select>
                    </Form.Item>
                    <Form.Item
                      label={<span style={filterLabelStyle}>{t('fields.edgeKey')}</span>}
                      style={{ marginBottom: 0 }}
                    >
                      <Input
                        placeholder={t('fields.edgeKey')}
                        allowClear
                        value={filters.edge_key ?? ''}
                        onChange={(event) =>
                          updateFilters({
                            edge_key: event.target.value || undefined,
                          })
                        }
                      />
                    </Form.Item>
                    <Form.Item
                      label={<span style={filterLabelStyle}>{t('fields.includeDeleted')}</span>}
                      style={{ marginBottom: 0 }}
                    >
                      <Select
                        placeholder={t('fields.includeDeleted')}
                        allowClear
                        value={filters.include_deleted}
                        onChange={(value) => updateFilters({ include_deleted: value })}
                      >
                        <Select.Option value={true}>{t('common.yes')}</Select.Option>
                        <Select.Option value={false}>{t('common.no')}</Select.Option>
                      </Select>
                    </Form.Item>
                    <Button size="small" block onClick={clearRelationshipFilters}>
                      {t('graph.clearRelationshipFilters')}
                    </Button>
                  </Space>
                ),
              },
              {
                key: 'view',
                label: t('graph.viewFilters'),
                children: (
                  <Space direction="vertical" size={12} style={{ width: '100%' }}>
                    <Form.Item
                      label={<span style={filterLabelStyle}>{t('graph.relatedNode')}</span>}
                      style={{ marginBottom: 0 }}
                    >
                      <Select
                        placeholder={t('graph.relatedNode')}
                        allowClear
                        showSearch
                        value={relatedNodeId ?? undefined}
                        options={nodeSelectOptions}
                        filterOption={filterNodeOption}
                        onChange={(value) => updateRelatedNode(value)}
                      />
                    </Form.Item>
                    <Form.Item
                      label={<span style={filterLabelStyle}>{t('graph.pathStartNode')}</span>}
                      style={{ marginBottom: 0 }}
                    >
                      <Select
                        placeholder={t('graph.pathStartNode')}
                        allowClear
                        showSearch
                        value={pathStartNodeId ?? undefined}
                        options={nodeSelectOptions}
                        filterOption={filterNodeOption}
                        onChange={(value) => updatePathStartNode(value)}
                      />
                    </Form.Item>
                    <Form.Item
                      label={<span style={filterLabelStyle}>{t('graph.pathEndNode')}</span>}
                      style={{ marginBottom: 0 }}
                    >
                      <Select
                        placeholder={t('graph.pathEndNode')}
                        allowClear
                        showSearch
                        value={pathEndNodeId ?? undefined}
                        options={nodeSelectOptions}
                        filterOption={filterNodeOption}
                        onChange={(value) => updatePathEndNode(value)}
                      />
                    </Form.Item>
                    <Button size="small" block onClick={clearViewFilters}>
                      {t('graph.clearViewFilters')}
                    </Button>
                  </Space>
                ),
              },
            ]}
          />
        </Form>
      </Drawer>

      {/* Detail Drawer */}
      <Drawer
        title={t('common.details')}
        placement="right"
        width={400}
        open={!!selectedNodeInfo}
        onClose={() => setSelectedNodeId(null)}
        destroyOnClose
        styles={{ body: { padding: 16, backgroundColor: '#f8fafc' } }}
        extra={
          selectedNodeInfo ? (
            <Space size={6} wrap>
              <Button
                size="small"
                type="text"
                onClick={() => selectedNodeId && updateRelatedNode(selectedNodeId)}
              >
                {t('graph.filterRelated')}
              </Button>
              <Button
                size="small"
                type="text"
                onClick={() => selectedNodeId && updatePathStartNode(selectedNodeId)}
              >
                {t('graph.setAsStart')}
              </Button>
              <Button
                size="small"
                type="text"
                onClick={() => selectedNodeId && updatePathEndNode(selectedNodeId)}
              >
                {t('graph.setAsEnd')}
              </Button>
            </Space>
          ) : null
        }
      >
        {selectedNodeInfo && (
          <>
            <Descriptions
              column={1}
              size="small"
              bordered={false}
              labelStyle={detailLabelStyle}
              contentStyle={detailContentStyle}
            >
              <Descriptions.Item label={t('fields.type')}>
                {t(`nodeType.${selectedNodeInfo.nodeType}`)}
              </Descriptions.Item>
              <Descriptions.Item label={t('fields.externalId')}>
                <span style={{ wordBreak: 'break-all' }}>{selectedNodeInfo.externalId}</span>
              </Descriptions.Item>
            </Descriptions>
            {selectedNodeInfo.metadata && Object.keys(selectedNodeInfo.metadata).length > 0 && (
              <div style={{ marginTop: 16 }}>
                <h4 style={{ marginBottom: 8, fontSize: 13, color: '#475569' }}>
                  {t('common.metadata')}
                </h4>
                <pre
                  style={{
                    fontSize: 12,
                    overflowX: 'auto',
                    backgroundColor: '#eef2f6',
                    padding: 10,
                    borderRadius: 8,
                    border: '1px solid #e2e8f0',
                    color: '#0f172a',
                  }}
                >
                  {JSON.stringify(selectedNodeInfo.metadata, null, 2)}
                </pre>
              </div>
            )}
          </>
        )}
      </Drawer>

      <Modal
        title={t('actions.create', { item: t('entities.relationship') })}
        open={isCreateRelationshipOpen}
        onCancel={closeCreateRelationship}
        onOk={() => createRelationshipForm.submit()}
        confirmLoading={createRelationshipMutation.isPending}
        destroyOnClose
      >
        {draftEdge && (
          <Descriptions column={1} size="small" style={{ marginBottom: 16 }}>
            <Descriptions.Item label={t('fields.source')}>
              {t(`nodeType.${draftEdge.sourceType}`)} / {draftEdge.sourceExternalId}
            </Descriptions.Item>
            <Descriptions.Item label={t('fields.target')}>
              {t(`nodeType.${draftEdge.targetType}`)} / {draftEdge.targetExternalId}
            </Descriptions.Item>
          </Descriptions>
        )}
        <Form form={createRelationshipForm} layout="vertical" onFinish={handleCreateRelationship}>
          <Form.Item
            name="relation_type"
            label={t('fields.relationType')}
            rules={[
              { required: true, message: t('validation.required', { field: t('fields.relationType') }) },
            ]}
          >
            <Select placeholder={t('placeholders.select', { item: t('fields.relationType') })}>
              {relationshipTypeOptionsForEdge.map((option) => (
                <Select.Option key={option} value={option}>
                  {relationshipTypeLabel(option)}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="edge_key" label={t('fields.edgeKey')}>
            <Input />
          </Form.Item>
          <Form.Item name="properties" label={t('fields.propertiesJson')}>
            <Input.TextArea rows={4} />
          </Form.Item>
          <Form.Item name="created_by" label={t('common.createdBy')}>
            <Input />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={t('actions.update', { item: t('entities.relationship') })}
        open={isEditRelationshipOpen}
        onCancel={closeEditRelationship}
        onOk={() => editRelationshipForm.submit()}
        confirmLoading={updateRelationshipMutation.isPending}
        destroyOnClose
        footer={[
          <Button key="delete" danger onClick={handleDeleteRelationship}>
            {t('actions.delete', { item: t('entities.relationship') })}
          </Button>,
          <Button key="cancel" onClick={closeEditRelationship}>
            {t('common.cancel')}
          </Button>,
          <Button
            key="submit"
            type="primary"
            loading={updateRelationshipMutation.isPending}
            onClick={() => editRelationshipForm.submit()}
          >
            {t('common.save')}
          </Button>,
        ]}
      >
        {editingRelationship && (
          <Descriptions column={1} size="small" style={{ marginBottom: 16 }}>
            <Descriptions.Item label={t('fields.source')}>
              {t(`nodeType.${editingRelationship.source_type}`)} / {editingRelationship.source_external_id}
            </Descriptions.Item>
            <Descriptions.Item label={t('fields.relation')}>
              {relationshipTypeLabel(editingRelationship.relation_type)}
            </Descriptions.Item>
            <Descriptions.Item label={t('fields.target')}>
              {t(`nodeType.${editingRelationship.target_type}`)} / {editingRelationship.target_external_id}
            </Descriptions.Item>
            <Descriptions.Item label={t('fields.edgeKey')}>
              {editingRelationship.edge_key}
            </Descriptions.Item>
          </Descriptions>
        )}
        <Form form={editRelationshipForm} layout="vertical" onFinish={handleUpdateRelationship}>
          <Form.Item name="properties" label={t('fields.propertiesJson')}>
            <Input.TextArea rows={4} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={
          editingNode
            ? t('actions.edit', { item: t(`nodeType.${editingNode.nodeType}`) })
            : t('actions.edit', { item: t('common.metadata') })
        }
        open={isEditNodeOpen}
        onCancel={closeEditNode}
        onOk={() => editNodeForm.submit()}
        confirmLoading={activeNodeMutation?.isPending}
        destroyOnClose
      >
        {editingNode && (
          <Descriptions column={1} size="small" style={{ marginBottom: 16 }}>
            <Descriptions.Item label={t('fields.sourceType')}>
              {t(`nodeType.${editingNode.nodeType}`)}
            </Descriptions.Item>
            <Descriptions.Item label={t('fields.sourceExternalId')}>
              {editingNode.externalId}
            </Descriptions.Item>
          </Descriptions>
        )}
        <Form form={editNodeForm} layout="vertical" onFinish={handleUpdateNode}>
          <Form.Item name="metadata" label={t('common.metadataJson')}>
            <Input.TextArea rows={6} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default GraphExplorer;
