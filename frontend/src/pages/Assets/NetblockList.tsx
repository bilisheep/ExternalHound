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
  useNetblockList,
  useCreateNetblock,
  useUpdateNetblock,
  useDeleteNetblock,
} from '@/hooks/useAssets';
import type {
  NetblockAsset,
  NetblockCreatePayload,
  NetblockUpdatePayload,
  ScopePolicy,
} from '@/types/asset';
import { cleanPayload } from '@/utils/forms';
import { formatJson, safeParseJson } from '@/utils/json';
import { useI18n } from '@/i18n';

const scopeColors: Record<ScopePolicy, string> = {
  IN_SCOPE: 'green',
  OUT_OF_SCOPE: 'red',
};

const NetblockList = () => {
  const { t } = useI18n();
  const [form] = Form.useForm();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [filters, setFilters] = useState({
    asn_number: undefined as string | undefined,
    is_internal: undefined as boolean | undefined,
    scope_policy: undefined as ScopePolicy | undefined,
  });
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingNetblock, setEditingNetblock] = useState<NetblockAsset | null>(null);

  const { data, isLoading, refetch } = useNetblockList({
    page,
    page_size: pageSize,
    ...filters,
  });

  const createMutation = useCreateNetblock();
  const updateMutation = useUpdateNetblock();
  const deleteMutation = useDeleteNetblock();
  const scopeLabel = (policy: ScopePolicy) =>
    policy === 'IN_SCOPE' ? t('scope.inScope') : t('scope.outOfScope');

  const openCreateModal = () => {
    setEditingNetblock(null);
    form.resetFields();
    setIsModalOpen(true);
  };

  const openEditModal = (record: NetblockAsset) => {
    setEditingNetblock(record);
    form.setFieldsValue({
      asn_number: record.asn_number ?? undefined,
      live_count: record.live_count,
      risk_score: record.risk_score,
      is_internal: record.is_internal,
      scope_policy: record.scope_policy,
      metadata: formatJson(record.metadata),
    });
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingNetblock(null);
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

    if (editingNetblock) {
      updateMutation.mutate(
        { id: editingNetblock.id, payload: payload as NetblockUpdatePayload },
        {
          onSuccess: () => closeModal(),
        }
      );
      return;
    }

    createMutation.mutate(payload as NetblockCreatePayload, {
      onSuccess: () => closeModal(),
    });
  };

  const columns = [
    {
      title: t('fields.cidr'),
      dataIndex: 'cidr',
      key: 'cidr',
    },
    {
      title: t('fields.asn'),
      dataIndex: 'asn_number',
      key: 'asn_number',
      width: 120,
    },
    {
      title: t('fields.live'),
      dataIndex: 'live_count',
      key: 'live_count',
      width: 90,
    },
    {
      title: t('fields.risk'),
      dataIndex: 'risk_score',
      key: 'risk_score',
      width: 80,
    },
    {
      title: t('labels.internal'),
      dataIndex: 'is_internal',
      key: 'is_internal',
      width: 100,
      render: (value: boolean) =>
        value ? <Tag color="orange">{t('common.yes')}</Tag> : <Tag>{t('common.no')}</Tag>,
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
      render: (record: NetblockAsset) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => openEditModal(record)}
          />
          <Popconfirm
            title={t('confirm.deleteItem', { item: t('entities.netblock') })}
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
          placeholder={t('fields.asn')}
          style={{ width: 160 }}
          allowClear
          onChange={(event) =>
            setFilters({
              ...filters,
              asn_number: event.target.value || undefined,
            })
          }
        />
        <Select
          placeholder={t('labels.internal')}
          style={{ width: 140 }}
          allowClear
          onChange={(value) => setFilters({ ...filters, is_internal: value })}
        >
          <Select.Option value={true}>{t('common.yes')}</Select.Option>
          <Select.Option value={false}>{t('common.no')}</Select.Option>
        </Select>
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
          {t('actions.new', { item: t('entities.netblock') })}
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
          editingNetblock
            ? t('actions.edit', { item: t('entities.netblock') })
            : t('actions.create', { item: t('entities.netblock') })
        }
        open={isModalOpen}
        onCancel={closeModal}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          {!editingNetblock && (
            <>
              <Form.Item
                name="external_id"
                label={t('fields.externalId')}
              >
                <Input placeholder="cidr:47.100.0.0/16" />
              </Form.Item>
              <Form.Item
                name="cidr"
                label={t('fields.cidr')}
                rules={[{ required: true, message: t('validation.required', { field: t('fields.cidr') }) }]}
              >
                <Input placeholder="47.100.0.0/16" />
              </Form.Item>
            </>
          )}
          <Form.Item name="asn_number" label={t('fields.asn')}>
            <Input />
          </Form.Item>
          <Form.Item name="live_count" label={t('fields.liveCount')}>
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="risk_score" label={t('fields.riskScore')}>
            <InputNumber min={0} max={10} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="is_internal" label={t('labels.internal')} valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="scope_policy" label={t('common.scopePolicy')}>
            <Select allowClear placeholder={t('placeholders.select', { item: t('common.scopePolicy') })}>
              <Select.Option value="IN_SCOPE">{t('scope.inScope')}</Select.Option>
              <Select.Option value="OUT_OF_SCOPE">{t('scope.outOfScope')}</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="metadata" label={t('common.metadataJson')}>
            <Input.TextArea rows={4} />
          </Form.Item>
          {!editingNetblock && (
            <Form.Item name="created_by" label={t('common.createdBy')}>
              <Input />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
};

export default NetblockList;
