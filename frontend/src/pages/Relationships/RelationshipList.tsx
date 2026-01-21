import { useMemo, useState } from 'react';
import {
  Table,
  Button,
  Space,
  Tag,
  Select,
  Form,
  Modal,
  Input,
  Popconfirm,
  message,
  Descriptions,
} from 'antd';
import { ReloadOutlined, PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import {
  useRelationshipList,
  useCreateRelationship,
  useUpdateRelationship,
  useDeleteRelationship,
} from '@/hooks/useRelationships';
import type {
  NodeType,
  RelationshipType,
  RelationshipRecord,
  RelationshipCreatePayload,
  RelationshipUpdatePayload,
} from '@/types/relationship';
import { cleanPayload } from '@/utils/forms';
import { formatJson, safeParseJson } from '@/utils/json';
import { useI18n } from '@/i18n';
import { nodeTypeOptions, relationshipRules, relationshipTypeOptions } from '@/constants/relationships';
import { useAllAssets } from '@/hooks/useAssets';

type AssetSelectOption = {
  value: string;
  label: string;
  nodeType: NodeType;
  search: string;
};

const RelationshipList = () => {
  const { t } = useI18n();
  const [createForm] = Form.useForm();
  const [editForm] = Form.useForm();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [filters, setFilters] = useState({
    source_external_id: undefined as string | undefined,
    source_type: undefined as NodeType | undefined,
    target_external_id: undefined as string | undefined,
    target_type: undefined as NodeType | undefined,
    relation_type: undefined as RelationshipType | undefined,
    include_deleted: undefined as boolean | undefined,
  });
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [editingRelationship, setEditingRelationship] = useState<RelationshipRecord | null>(null);
  const [selectedRelationType, setSelectedRelationType] = useState<RelationshipType | null>(null);
  const sourceType = Form.useWatch('source_type', createForm) as NodeType | undefined;
  const targetType = Form.useWatch('target_type', createForm) as NodeType | undefined;

  const { data, isLoading, refetch } = useRelationshipList({
    page,
    page_size: pageSize,
    ...filters,
  });

  const createMutation = useCreateRelationship();
  const updateMutation = useUpdateRelationship();
  const deleteMutation = useDeleteRelationship();
  const { data: allAssets, isLoading: assetsLoading } = useAllAssets();
  const nodeTypeLabel = (value: NodeType) => t(`nodeType.${value}`);
  const relationshipTypeLabel = (value: RelationshipType) => t(`relationshipType.${value}`);

  const assetOptions = useMemo(() => {
    const byType: Record<NodeType, AssetSelectOption[]> = {
      Organization: [],
      Domain: [],
      IP: [],
      Netblock: [],
      Service: [],
      Certificate: [],
      ClientApplication: [],
      Credential: [],
    };
    const all: AssetSelectOption[] = [];

    if (!allAssets) {
      return { all, byType };
    }

    const toDisplayText = (parts: Array<string | number | null | undefined>) =>
      parts
        .map((part) => (part === null || part === undefined ? '' : String(part).trim()))
        .filter((part) => part.length > 0)
        .join(' ');

    const addOption = (
      nodeType: NodeType,
      externalId: string,
      displayParts: Array<string | number | null | undefined>
    ) => {
      const typeLabel = t(`nodeType.${nodeType}`);
      const detail = toDisplayText(displayParts);
      const label = detail
        ? `${typeLabel} - ${externalId} (${detail})`
        : `${typeLabel} - ${externalId}`;
      const option: AssetSelectOption = {
        value: externalId,
        label,
        nodeType,
        search: `${typeLabel} ${nodeType} ${externalId} ${detail}`.toLowerCase(),
      };
      byType[nodeType].push(option);
      all.push(option);
    };

    allAssets.organizations.forEach((org) =>
      addOption('Organization', org.external_id, [org.name, org.full_name])
    );
    allAssets.domains.forEach((domain) => addOption('Domain', domain.external_id, [domain.name]));
    allAssets.ips.forEach((ip) => addOption('IP', ip.external_id, [ip.address]));
    allAssets.netblocks.forEach((netblock) =>
      addOption('Netblock', netblock.external_id, [netblock.cidr])
    );
    allAssets.services.forEach((service) =>
      addOption('Service', service.external_id, [
        service.service_name,
        `${service.port}/${service.protocol}`,
      ])
    );
    allAssets.certificates.forEach((certificate) =>
      addOption('Certificate', certificate.external_id, [
        certificate.subject_cn ?? certificate.issuer_cn ?? certificate.issuer_org,
      ])
    );
    allAssets.clientApplications.forEach((clientApp) =>
      addOption('ClientApplication', clientApp.external_id, [
        clientApp.app_name,
        clientApp.package_name,
      ])
    );
    allAssets.credentials.forEach((credential) =>
      addOption('Credential', credential.external_id, [
        credential.username,
        credential.email,
        credential.phone,
        credential.cred_type,
      ])
    );

    return { all, byType };
  }, [allAssets, t]);

  const assetFilterOption = (input: string, option?: { search?: string }) =>
    (option?.search ?? '').includes(input.toLowerCase());
  const sourceAssetOptions = sourceType ? assetOptions.byType[sourceType] : assetOptions.all;
  const targetAssetOptions = targetType ? assetOptions.byType[targetType] : assetOptions.all;

  const openCreateModal = () => {
    setIsCreateOpen(true);
    setSelectedRelationType(null);
    createForm.resetFields();
  };

  const openEditModal = (record: RelationshipRecord) => {
    setEditingRelationship(record);
    editForm.setFieldsValue({
      properties: formatJson(record.properties),
    });
    setIsEditOpen(true);
  };

  const closeCreateModal = () => {
    setIsCreateOpen(false);
    createForm.resetFields();
  };

  const closeEditModal = () => {
    setIsEditOpen(false);
    setEditingRelationship(null);
    editForm.resetFields();
  };

  const handleRelationTypeChange = (value?: RelationshipType) => {
    setSelectedRelationType(value ?? null);
    if (!value) {
      return;
    }
    const rule = relationshipRules[value];
    if (rule) {
      createForm.setFieldsValue({
        source_type: rule.source,
        target_type: rule.target,
      });
    }
  };

  const handleCreate = (values: Record<string, unknown>) => {
    const { value: propertiesValue, error } = safeParseJson(values.properties as string | undefined);
    if (error) {
      message.error(t('errors.json.properties'));
      return;
    }

    const payload = cleanPayload({
      ...values,
      properties: propertiesValue,
    });

    createMutation.mutate(payload as RelationshipCreatePayload, {
      onSuccess: () => closeCreateModal(),
    });
  };

  const handleUpdate = (values: Record<string, unknown>) => {
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

    updateMutation.mutate(
      { id: editingRelationship.id, payload: payload as RelationshipUpdatePayload },
      {
        onSuccess: () => closeEditModal(),
      }
    );
  };

  const columns = [
    {
      title: t('fields.source'),
      dataIndex: 'source_external_id',
      key: 'source_external_id',
    },
    {
      title: t('fields.sourceType'),
      dataIndex: 'source_type',
      key: 'source_type',
      width: 130,
      render: (value: NodeType) => nodeTypeLabel(value),
    },
    {
      title: t('fields.relation'),
      dataIndex: 'relation_type',
      key: 'relation_type',
      width: 160,
      render: (value: RelationshipType) => relationshipTypeLabel(value),
    },
    {
      title: t('fields.target'),
      dataIndex: 'target_external_id',
      key: 'target_external_id',
    },
    {
      title: t('fields.targetType'),
      dataIndex: 'target_type',
      key: 'target_type',
      width: 130,
      render: (value: NodeType) => nodeTypeLabel(value),
    },
    {
      title: t('fields.edgeKey'),
      dataIndex: 'edge_key',
      key: 'edge_key',
      width: 120,
    },
    {
      title: t('fields.deleted'),
      dataIndex: 'is_deleted',
      key: 'is_deleted',
      width: 90,
      render: (value: boolean) =>
        value ? <Tag color="red">{t('common.yes')}</Tag> : <Tag>{t('common.no')}</Tag>,
    },
    {
      title: t('common.actions'),
      key: 'action',
      width: 120,
      render: (record: RelationshipRecord) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => openEditModal(record)}
          />
          <Popconfirm
            title={t('confirm.deleteItem', { item: t('entities.relationship') })}
            onConfirm={() => deleteMutation.mutate(record.id)}
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }} wrap>
        <Input
          placeholder={t('fields.sourceExternalId')}
          style={{ width: 180 }}
          allowClear
          onChange={(event) =>
            setFilters({
              ...filters,
              source_external_id: event.target.value || undefined,
            })
          }
        />
        <Select
          placeholder={t('fields.sourceType')}
          style={{ width: 160 }}
          allowClear
          onChange={(value) => setFilters({ ...filters, source_type: value })}
        >
          {nodeTypeOptions.map((option) => (
            <Select.Option key={option} value={option}>
              {nodeTypeLabel(option)}
            </Select.Option>
          ))}
        </Select>
        <Input
          placeholder={t('fields.targetExternalId')}
          style={{ width: 180 }}
          allowClear
          onChange={(event) =>
            setFilters({
              ...filters,
              target_external_id: event.target.value || undefined,
            })
          }
        />
        <Select
          placeholder={t('fields.targetType')}
          style={{ width: 160 }}
          allowClear
          onChange={(value) => setFilters({ ...filters, target_type: value })}
        >
          {nodeTypeOptions.map((option) => (
            <Select.Option key={option} value={option}>
              {nodeTypeLabel(option)}
            </Select.Option>
          ))}
        </Select>
        <Select
          placeholder={t('fields.relationType')}
          style={{ width: 180 }}
          allowClear
          onChange={(value) => setFilters({ ...filters, relation_type: value })}
        >
          {relationshipTypeOptions.map((option) => (
            <Select.Option key={option} value={option}>
              {relationshipTypeLabel(option)}
            </Select.Option>
          ))}
        </Select>
        <Select
          placeholder={t('fields.includeDeleted')}
          style={{ width: 160 }}
          allowClear
          onChange={(value) => setFilters({ ...filters, include_deleted: value })}
        >
          <Select.Option value={true}>{t('common.yes')}</Select.Option>
          <Select.Option value={false}>{t('common.no')}</Select.Option>
        </Select>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>
          {t('actions.new', { item: t('entities.relationship') })}
        </Button>
        <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
          {t('common.refresh')}
        </Button>
      </Space>

      <Table
        columns={columns}
        dataSource={data?.items || []}
        loading={isLoading}
        rowKey="id"
        pagination={{
          current: page,
          pageSize,
          total: data?.total || 0,
          showSizeChanger: true,
          showTotal: (total) => t('common.total', { total }),
          onChange: (nextPage, nextPageSize) => {
            setPage(nextPage);
            setPageSize(nextPageSize);
          },
        }}
      />

      <Modal
        title={t('actions.create', { item: t('entities.relationship') })}
        open={isCreateOpen}
        onCancel={closeCreateModal}
        onOk={() => createForm.submit()}
        confirmLoading={createMutation.isPending}
        destroyOnClose
      >
        <Form form={createForm} layout="vertical" onFinish={handleCreate}>
          <Form.Item
            name="source_external_id"
            label={t('fields.sourceExternalId')}
            rules={[
              {
                required: true,
                message: t('validation.required', { field: t('fields.sourceExternalId') }),
              },
            ]}
          >
            <Select
              showSearch
              allowClear
              placeholder={t('placeholders.select', { item: t('fields.sourceExternalId') })}
              options={sourceAssetOptions}
              filterOption={assetFilterOption}
              loading={assetsLoading}
              onChange={(_, option) => {
                const selectedType = (option as AssetSelectOption | undefined)?.nodeType;
                if (!selectedType) {
                  return;
                }
                const currentType = createForm.getFieldValue('source_type') as NodeType | undefined;
                if (!currentType) {
                  createForm.setFieldsValue({ source_type: selectedType });
                }
              }}
            />
          </Form.Item>
          <Form.Item
            name="relation_type"
            label={t('fields.relationType')}
            rules={[
              { required: true, message: t('validation.required', { field: t('fields.relationType') }) },
            ]}
          >
            <Select
              placeholder={t('placeholders.select', { item: t('fields.relationType') })}
              onChange={handleRelationTypeChange}
            >
              {relationshipTypeOptions.map((option) => (
                <Select.Option key={option} value={option}>
                  {relationshipTypeLabel(option)}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="source_type"
            label={t('fields.sourceType')}
            rules={[
              { required: true, message: t('validation.required', { field: t('fields.sourceType') }) },
            ]}
          >
            <Select
              placeholder={t('placeholders.select', { item: t('fields.sourceType') })}
              disabled={!!selectedRelationType}
            >
              {nodeTypeOptions.map((option) => (
                <Select.Option key={option} value={option}>
                  {nodeTypeLabel(option)}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="target_external_id"
            label={t('fields.targetExternalId')}
            rules={[
              {
                required: true,
                message: t('validation.required', { field: t('fields.targetExternalId') }),
              },
            ]}
          >
            <Select
              showSearch
              allowClear
              placeholder={t('placeholders.select', { item: t('fields.targetExternalId') })}
              options={targetAssetOptions}
              filterOption={assetFilterOption}
              loading={assetsLoading}
              onChange={(_, option) => {
                const selectedType = (option as AssetSelectOption | undefined)?.nodeType;
                if (!selectedType) {
                  return;
                }
                const currentType = createForm.getFieldValue('target_type') as NodeType | undefined;
                if (!currentType) {
                  createForm.setFieldsValue({ target_type: selectedType });
                }
              }}
            />
          </Form.Item>
          <Form.Item
            name="target_type"
            label={t('fields.targetType')}
            rules={[
              { required: true, message: t('validation.required', { field: t('fields.targetType') }) },
            ]}
          >
            <Select
              placeholder={t('placeholders.select', { item: t('fields.targetType') })}
              disabled={!!selectedRelationType}
            >
              {nodeTypeOptions.map((option) => (
                <Select.Option key={option} value={option}>
                  {nodeTypeLabel(option)}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="edge_key" label={t('fields.edgeKey')}>
            <Input placeholder="default" />
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
        open={isEditOpen}
        onCancel={closeEditModal}
        onOk={() => editForm.submit()}
        confirmLoading={updateMutation.isPending}
        destroyOnClose
      >
        {editingRelationship && (
          <Descriptions column={1} size="small" style={{ marginBottom: 16 }}>
            <Descriptions.Item label={t('fields.source')}>
              {nodeTypeLabel(editingRelationship.source_type)} / {editingRelationship.source_external_id}
            </Descriptions.Item>
            <Descriptions.Item label={t('fields.relation')}>
              {relationshipTypeLabel(editingRelationship.relation_type)}
            </Descriptions.Item>
            <Descriptions.Item label={t('fields.target')}>
              {nodeTypeLabel(editingRelationship.target_type)} / {editingRelationship.target_external_id}
            </Descriptions.Item>
            <Descriptions.Item label={t('fields.edgeKey')}>
              {editingRelationship.edge_key}
            </Descriptions.Item>
          </Descriptions>
        )}
        <Form form={editForm} layout="vertical" onFinish={handleUpdate}>
          <Form.Item name="properties" label={t('fields.propertiesJson')}>
            <Input.TextArea rows={4} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default RelationshipList;
