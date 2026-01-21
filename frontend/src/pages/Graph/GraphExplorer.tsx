import { useCallback, useMemo, useRef, useState } from 'react';
import {
  Button,
  Card,
  Descriptions,
  Empty,
  Form,
  Input,
  Modal,
  Select,
  Space,
  Spin,
  Switch,
  message,
} from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import type { EdgeData, GraphData, NodeData } from '@antv/g6';
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
  const [filters, setFilters] = useState({
    source_external_id: undefined as string | undefined,
    source_type: undefined as NodeType | undefined,
    target_external_id: undefined as string | undefined,
    target_type: undefined as NodeType | undefined,
    relation_type: undefined as RelationshipType | undefined,
    edge_key: undefined as string | undefined,
    include_deleted: undefined as boolean | undefined,
  });
  const [draftEdge, setDraftEdge] = useState<EdgeDraft | null>(null);
  const [isCreateRelationshipOpen, setIsCreateRelationshipOpen] = useState(false);
  const [editingRelationship, setEditingRelationship] = useState<RelationshipRecord | null>(null);
  const [isEditRelationshipOpen, setIsEditRelationshipOpen] = useState(false);
  const [editingNode, setEditingNode] = useState<NodeEditDraft | null>(null);
  const [isEditNodeOpen, setIsEditNodeOpen] = useState(false);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

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

  const graphData = useMemo<GraphData>(() => {
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
          service.service_name || `${service.port}/${service.protocol}` || service.external_id;
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

  return (
    <Space direction="vertical" size={24} style={{ width: '100%' }}>
      <Card>
        <Space wrap>
          <Input
            placeholder={t('fields.sourceExternalId')}
            style={{ width: 180 }}
            allowClear
            value={filters.source_external_id ?? ''}
            onChange={(event) =>
              updateFilters({
                source_external_id: event.target.value || undefined,
              })
            }
          />
          <Select
            placeholder={t('fields.sourceType')}
            style={{ width: 160 }}
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
          <Input
            placeholder={t('fields.targetExternalId')}
            style={{ width: 180 }}
            allowClear
            value={filters.target_external_id ?? ''}
            onChange={(event) =>
              updateFilters({
                target_external_id: event.target.value || undefined,
              })
            }
          />
          <Select
            placeholder={t('fields.targetType')}
            style={{ width: 160 }}
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
          <Select
            placeholder={t('fields.relationType')}
            style={{ width: 180 }}
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
          <Input
            placeholder={t('fields.edgeKey')}
            style={{ width: 160 }}
            allowClear
            value={filters.edge_key ?? ''}
            onChange={(event) =>
              updateFilters({
                edge_key: event.target.value || undefined,
              })
            }
          />
          <Select
            placeholder={t('fields.includeDeleted')}
            style={{ width: 160 }}
            allowClear
            value={filters.include_deleted}
            onChange={(value) => updateFilters({ include_deleted: value })}
          >
            <Select.Option value={true}>{t('common.yes')}</Select.Option>
            <Select.Option value={false}>{t('common.no')}</Select.Option>
          </Select>
          <Space size={6}>
            <span>{t(isLinkMode ? 'graph.linkMode' : 'graph.dragMode')}</span>
            <Switch checked={isLinkMode} onChange={setIsLinkMode} />
          </Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => {
              refetchRelationships();
              refetchAssets();
            }}
          >
            {t('common.refresh')}
          </Button>
        </Space>
      </Card>
      <Card title={t('menu.graph')} bodyStyle={{ padding: 0 }}>
        <Spin spinning={relationshipsLoading || relationshipsFetching || assetsLoading || assetsFetching}>
          <div style={{ display: 'flex', height: 640 }}>
            <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
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
            {selectedNodeInfo && (
              <div
                style={{
                  width: 320,
                  borderLeft: '1px solid #f0f0f0',
                  padding: 16,
                  overflowY: 'auto',
                  backgroundColor: '#fff',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16, alignItems: 'center' }}>
                  <h3 style={{ margin: 0, fontSize: 16 }}>{t('common.details')}</h3>
                  <Button size="small" onClick={() => setSelectedNodeId(null)}>
                    X
                  </Button>
                </div>
                <Descriptions column={1} size="small" bordered>
                  <Descriptions.Item label={t('fields.type')}>
                    {t(`nodeType.${selectedNodeInfo.nodeType}`)}
                  </Descriptions.Item>
                  <Descriptions.Item label={t('fields.externalId')}>
                    <span style={{ wordBreak: 'break-all' }}>{selectedNodeInfo.externalId}</span>
                  </Descriptions.Item>
                </Descriptions>
                {selectedNodeInfo.metadata && Object.keys(selectedNodeInfo.metadata).length > 0 && (
                  <div style={{ marginTop: 16 }}>
                    <h4 style={{ marginBottom: 8, fontSize: 14 }}>{t('common.metadata')}</h4>
                    <pre
                      style={{
                        fontSize: 11,
                        overflowX: 'auto',
                        backgroundColor: '#f5f5f5',
                        padding: 8,
                        borderRadius: 4,
                        border: '1px solid #d9d9d9',
                      }}
                    >
                      {JSON.stringify(selectedNodeInfo.metadata, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        </Spin>
      </Card>

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
    </Space>
  );
};

export default GraphExplorer;
