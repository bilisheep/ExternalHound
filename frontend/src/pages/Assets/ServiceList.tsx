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
import { useNavigate } from 'react-router-dom';
import { useCreateService, useDeleteService, useServiceList, useUpdateService } from '@/hooks/useAssets';
import type {
  ServiceAsset,
  ServiceCreatePayload,
  ServiceUpdatePayload,
  ScopePolicy,
} from '@/types/asset';
import { cleanPayload } from '@/utils/forms';
import { formatJson, safeParseJson } from '@/utils/json';
import { useI18n } from '@/i18n';

const scopeColors: Record<ScopePolicy, string> = {
  IN_SCOPE: 'green',
  OUT_OF_SCOPE: 'red',
};

const ServiceList = () => {
  const navigate = useNavigate();
  const { t } = useI18n();
  const [form] = Form.useForm();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [filters, setFilters] = useState({
    port: undefined as number | undefined,
    protocol: undefined as 'TCP' | 'UDP' | undefined,
    is_http: undefined as boolean | undefined,
    scope_policy: undefined as ScopePolicy | undefined,
  });
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingService, setEditingService] = useState<ServiceAsset | null>(null);

  const { data, isLoading, refetch } = useServiceList({
    page,
    page_size: pageSize,
    ...filters,
  });

  const createMutation = useCreateService();
  const updateMutation = useUpdateService();
  const deleteMutation = useDeleteService();
  const scopeLabel = (policy: ScopePolicy) =>
    policy === 'IN_SCOPE' ? t('scope.inScope') : t('scope.outOfScope');

  const openCreateModal = () => {
    setEditingService(null);
    form.resetFields();
    setIsModalOpen(true);
  };

  const openEditModal = (record: ServiceAsset) => {
    setEditingService(record);
    form.setFieldsValue({
      service_name: record.service_name ?? undefined,
      port: record.port,
      protocol: record.protocol,
      product: record.product ?? undefined,
      version: record.version ?? undefined,
      banner: record.banner ?? undefined,
      is_http: record.is_http,
      risk_score: record.risk_score,
      asset_category: record.asset_category ?? undefined,
      scope_policy: record.scope_policy,
      metadata: formatJson(record.metadata),
    });
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingService(null);
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

    if (editingService) {
      updateMutation.mutate(
        { id: editingService.id, payload: payload as ServiceUpdatePayload },
        {
          onSuccess: () => closeModal(),
        }
      );
      return;
    }

    createMutation.mutate(payload as ServiceCreatePayload, {
      onSuccess: () => closeModal(),
    });
  };

  const columns = [
    {
      title: t('fields.service'),
      dataIndex: 'service_name',
      key: 'service_name',
      render: (_: string, record: ServiceAsset) => (
        <Button type="link" onClick={() => navigate(`/assets/services/${record.id}`)}>
          {record.service_name || record.product || record.external_id}
        </Button>
      ),
    },
    {
      title: t('fields.port'),
      dataIndex: 'port',
      key: 'port',
      width: 90,
    },
    {
      title: t('fields.protocol'),
      dataIndex: 'protocol',
      key: 'protocol',
      width: 100,
    },
    {
      title: t('fields.product'),
      dataIndex: 'product',
      key: 'product',
    },
    {
      title: t('fields.http'),
      dataIndex: 'is_http',
      key: 'is_http',
      width: 90,
      render: (value: boolean) =>
        value ? <Tag color="green">{t('common.yes')}</Tag> : <Tag>{t('common.no')}</Tag>,
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
      width: 140,
      render: (record: ServiceAsset) => (
        <Space>
          <Button type="link" size="small" onClick={() => navigate(`/assets/services/${record.id}`)}>
            {t('common.view')}
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => openEditModal(record)}
          />
          <Popconfirm
            title={t('confirm.deleteItem', { item: t('entities.service') })}
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
        <InputNumber
          min={1}
          max={65535}
          placeholder={t('fields.port')}
          onChange={(value) => setFilters({ ...filters, port: value ?? undefined })}
        />
        <Select
          placeholder={t('fields.protocol')}
          style={{ width: 140 }}
          allowClear
          onChange={(value) => setFilters({ ...filters, protocol: value })}
        >
          <Select.Option value="TCP">TCP</Select.Option>
          <Select.Option value="UDP">UDP</Select.Option>
        </Select>
        <Select
          placeholder={t('fields.http')}
          style={{ width: 120 }}
          allowClear
          onChange={(value) => setFilters({ ...filters, is_http: value })}
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
          {t('actions.new', { item: t('entities.service') })}
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
          editingService
            ? t('actions.edit', { item: t('entities.service') })
            : t('actions.create', { item: t('entities.service') })
        }
        open={isModalOpen}
        onCancel={closeModal}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          {!editingService && (
            <Form.Item
              name="external_id"
              label={t('fields.externalId')}
            >
              <Input placeholder="svc:192.168.1.1:80:TCP" />
            </Form.Item>
          )}
          <Form.Item name="service_name" label={t('fields.serviceName')}>
            <Input placeholder="http" />
          </Form.Item>
          <Form.Item
            name="port"
            label={t('fields.port')}
            rules={[{ required: true, message: t('validation.required', { field: t('fields.port') }) }]}
          >
            <InputNumber min={1} max={65535} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="protocol" label={t('fields.protocol')}>
            <Select allowClear placeholder="TCP">
              <Select.Option value="TCP">TCP</Select.Option>
              <Select.Option value="UDP">UDP</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="product" label={t('fields.product')}>
            <Input />
          </Form.Item>
          <Form.Item name="version" label={t('fields.version')}>
            <Input />
          </Form.Item>
          <Form.Item name="banner" label={t('fields.banner')}>
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="is_http" label={t('fields.http')} valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="risk_score" label={t('fields.riskScore')}>
            <InputNumber min={0} max={10} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="asset_category" label={t('fields.assetCategory')}>
            <Input placeholder="WEB" />
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
          {!editingService && (
            <Form.Item name="created_by" label={t('common.createdBy')}>
              <Input />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
};

export default ServiceList;
