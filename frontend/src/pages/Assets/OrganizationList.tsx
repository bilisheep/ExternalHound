import { useState } from 'react';
import {
  Table,
  Button,
  Space,
  Tag,
  Select,
  InputNumber,
  Form,
  Modal,
  Input,
  Switch,
  Popconfirm,
  message,
} from 'antd';
import { ReloadOutlined, PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import {
  useOrganizationList,
  useCreateOrganization,
  useUpdateOrganization,
  useDeleteOrganization,
} from '@/hooks/useAssets';
import type {
  OrganizationAsset,
  OrganizationCreatePayload,
  OrganizationUpdatePayload,
  ScopePolicy,
} from '@/types/asset';
import { cleanPayload } from '@/utils/forms';
import { formatJson, safeParseJson } from '@/utils/json';
import { useI18n } from '@/i18n';

const scopeColors: Record<ScopePolicy, string> = {
  IN_SCOPE: 'green',
  OUT_OF_SCOPE: 'red',
};

const OrganizationList = () => {
  const { t } = useI18n();
  const [form] = Form.useForm();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [filters, setFilters] = useState({
    is_primary: undefined as boolean | undefined,
    tier: undefined as number | undefined,
    scope_policy: undefined as ScopePolicy | undefined,
  });
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingOrganization, setEditingOrganization] = useState<OrganizationAsset | null>(null);

  const { data, isLoading, refetch } = useOrganizationList({
    page,
    page_size: pageSize,
    ...filters,
  });

  const createMutation = useCreateOrganization();
  const updateMutation = useUpdateOrganization();
  const deleteMutation = useDeleteOrganization();
  const scopeLabel = (policy: ScopePolicy) =>
    policy === 'IN_SCOPE' ? t('scope.inScope') : t('scope.outOfScope');

  const openCreateModal = () => {
    setEditingOrganization(null);
    form.resetFields();
    setIsModalOpen(true);
  };

  const openEditModal = (record: OrganizationAsset) => {
    setEditingOrganization(record);
    form.setFieldsValue({
      name: record.name,
      full_name: record.full_name ?? undefined,
      credit_code: record.credit_code ?? undefined,
      is_primary: record.is_primary,
      tier: record.tier,
      asset_count: record.asset_count,
      risk_score: record.risk_score,
      scope_policy: record.scope_policy,
      metadata: formatJson(record.metadata),
    });
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingOrganization(null);
    form.resetFields();
  };

  const handleSubmit = (values: Record<string, unknown>) => {
    const { value: metadataValue, error } = safeParseJson(values.metadata as string | undefined);
    if (error) {
      message.error(t('errors.json.metadata'));
      return;
    }

    const payload = cleanPayload({
      ...values,
      metadata: metadataValue,
    });

    if (editingOrganization) {
      updateMutation.mutate(
        { id: editingOrganization.id, payload: payload as OrganizationUpdatePayload },
        {
          onSuccess: () => closeModal(),
        }
      );
      return;
    }

    createMutation.mutate(payload as OrganizationCreatePayload, {
      onSuccess: () => closeModal(),
    });
  };

  const columns = [
    {
      title: t('fields.name'),
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: t('fields.fullName'),
      dataIndex: 'full_name',
      key: 'full_name',
    },
    {
      title: t('fields.primary'),
      dataIndex: 'is_primary',
      key: 'is_primary',
      width: 90,
      render: (value: boolean) =>
        value ? <Tag color="green">{t('common.yes')}</Tag> : <Tag>{t('common.no')}</Tag>,
    },
    {
      title: t('fields.tier'),
      dataIndex: 'tier',
      key: 'tier',
      width: 70,
    },
    {
      title: t('fields.assets'),
      dataIndex: 'asset_count',
      key: 'asset_count',
      width: 90,
    },
    {
      title: t('fields.risk'),
      dataIndex: 'risk_score',
      key: 'risk_score',
      width: 80,
    },
    {
      title: t('common.scope'),
      dataIndex: 'scope_policy',
      key: 'scope_policy',
      width: 120,
      render: (policy: ScopePolicy) => (
        <Tag color={scopeColors[policy]}>{scopeLabel(policy)}</Tag>
      ),
    },
    {
      title: t('common.actions'),
      key: 'action',
      width: 120,
      render: (record: OrganizationAsset) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => openEditModal(record)}
          />
          <Popconfirm
            title={t('confirm.deleteItem', { item: t('entities.organization') })}
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
        <Select
          placeholder={t('fields.primary')}
          style={{ width: 140 }}
          allowClear
          onChange={(value) => setFilters({ ...filters, is_primary: value })}
        >
          <Select.Option value={true}>{t('common.yes')}</Select.Option>
          <Select.Option value={false}>{t('common.no')}</Select.Option>
        </Select>
        <InputNumber
          min={0}
          placeholder={t('fields.tier')}
          onChange={(value) => setFilters({ ...filters, tier: value ?? undefined })}
        />
        <Select
          placeholder={t('common.scope')}
          style={{ width: 160 }}
          allowClear
          onChange={(value) => setFilters({ ...filters, scope_policy: value })}
        >
          <Select.Option value="IN_SCOPE">{t('scope.inScope')}</Select.Option>
          <Select.Option value="OUT_OF_SCOPE">{t('scope.outOfScope')}</Select.Option>
        </Select>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>
          {t('actions.new', { item: t('entities.organization') })}
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
        title={
          editingOrganization
            ? t('actions.edit', { item: t('entities.organization') })
            : t('actions.create', { item: t('entities.organization') })
        }
        open={isModalOpen}
        onCancel={closeModal}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          {!editingOrganization && (
            <>
              <Form.Item
                name="external_id"
                label={t('fields.externalId')}
              >
                <Input placeholder="org:91110000XXXXXX" />
              </Form.Item>
            </>
          )}
          <Form.Item
            name="name"
            label={t('fields.name')}
            rules={[{ required: true, message: t('validation.required', { field: t('fields.name') }) }]}
          >
            <Input />
          </Form.Item>
          <Form.Item name="full_name" label={t('fields.fullName')}>
            <Input />
          </Form.Item>
          <Form.Item name="credit_code" label={t('fields.creditCode')}>
            <Input />
          </Form.Item>
          <Form.Item name="is_primary" label={t('fields.primary')} valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="tier" label={t('fields.tier')}>
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          {editingOrganization && (
            <>
              <Form.Item name="asset_count" label={t('fields.assetCount')}>
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item name="risk_score" label={t('fields.riskScore')}>
                <InputNumber min={0} max={10} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </>
          )}
          <Form.Item name="scope_policy" label={t('common.scopePolicy')}>
            <Select allowClear placeholder={t('placeholders.select', { item: t('common.scopePolicy') })}>
              <Select.Option value="IN_SCOPE">{t('scope.inScope')}</Select.Option>
              <Select.Option value="OUT_OF_SCOPE">{t('scope.outOfScope')}</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="metadata" label={t('common.metadataJson')}>
            <Input.TextArea rows={4} />
          </Form.Item>
          {!editingOrganization && (
            <Form.Item name="created_by" label={t('common.createdBy')}>
              <Input />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
};

export default OrganizationList;
