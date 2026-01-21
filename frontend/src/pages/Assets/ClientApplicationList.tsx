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
  Popconfirm,
  message,
} from 'antd';
import { ReloadOutlined, PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import {
  useClientApplicationList,
  useCreateClientApplication,
  useUpdateClientApplication,
  useDeleteClientApplication,
} from '@/hooks/useAssets';
import type {
  ClientApplicationAsset,
  ClientApplicationCreatePayload,
  ClientApplicationUpdatePayload,
  ScopePolicy,
} from '@/types/asset';
import { cleanPayload } from '@/utils/forms';
import { formatJson, safeParseJson } from '@/utils/json';
import { useI18n } from '@/i18n';

const scopeColors: Record<ScopePolicy, string> = {
  IN_SCOPE: 'green',
  OUT_OF_SCOPE: 'red',
};

const platformOptions = ['Android', 'iOS', 'Windows', 'macOS', 'Linux'];

const ClientApplicationList = () => {
  const { t } = useI18n();
  const [form] = Form.useForm();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [filters, setFilters] = useState({
    platform: undefined as string | undefined,
    scope_policy: undefined as ScopePolicy | undefined,
  });
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingApp, setEditingApp] = useState<ClientApplicationAsset | null>(null);

  const { data, isLoading, refetch } = useClientApplicationList({
    page,
    page_size: pageSize,
    ...filters,
  });

  const createMutation = useCreateClientApplication();
  const updateMutation = useUpdateClientApplication();
  const deleteMutation = useDeleteClientApplication();
  const scopeLabel = (policy: ScopePolicy) =>
    policy === 'IN_SCOPE' ? t('scope.inScope') : t('scope.outOfScope');

  const openCreateModal = () => {
    setEditingApp(null);
    form.resetFields();
    setIsModalOpen(true);
  };

  const openEditModal = (record: ClientApplicationAsset) => {
    setEditingApp(record);
    form.setFieldsValue({
      app_name: record.app_name,
      package_name: record.package_name,
      version: record.version ?? undefined,
      platform: record.platform,
      bundle_id: record.bundle_id ?? undefined,
      risk_score: record.risk_score,
      scope_policy: record.scope_policy,
      metadata: formatJson(record.metadata),
    });
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingApp(null);
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

    if (editingApp) {
      updateMutation.mutate(
        { id: editingApp.id, payload: payload as ClientApplicationUpdatePayload },
        {
          onSuccess: () => closeModal(),
        }
      );
      return;
    }

    createMutation.mutate(payload as ClientApplicationCreatePayload, {
      onSuccess: () => closeModal(),
    });
  };

  const columns = [
    {
      title: t('fields.appName'),
      dataIndex: 'app_name',
      key: 'app_name',
    },
    {
      title: t('fields.package'),
      dataIndex: 'package_name',
      key: 'package_name',
    },
    {
      title: t('fields.platform'),
      dataIndex: 'platform',
      key: 'platform',
      width: 120,
    },
    {
      title: t('fields.version'),
      dataIndex: 'version',
      key: 'version',
      width: 100,
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
      render: (record: ClientApplicationAsset) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => openEditModal(record)}
          />
          <Popconfirm
            title={t('confirm.deleteItem', { item: t('entities.clientApp') })}
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
          placeholder={t('fields.platform')}
          style={{ width: 160 }}
          allowClear
          onChange={(value) => setFilters({ ...filters, platform: value })}
        >
          {platformOptions.map((platform) => (
            <Select.Option key={platform} value={platform}>
              {platform}
            </Select.Option>
          ))}
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
          {t('actions.new', { item: t('entities.clientApp') })}
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
          editingApp
            ? t('actions.edit', { item: t('entities.clientApp') })
            : t('actions.create', { item: t('entities.clientApp') })
        }
        open={isModalOpen}
        onCancel={closeModal}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          {!editingApp && (
            <Form.Item
              name="external_id"
              label={t('fields.externalId')}
            >
              <Input placeholder="app:Android:com.example.app" />
            </Form.Item>
          )}
          <Form.Item
            name="app_name"
            label={t('fields.appName')}
            rules={[{ required: true, message: t('validation.required', { field: t('fields.appName') }) }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="package_name"
            label={t('fields.packageName')}
            rules={[
              { required: true, message: t('validation.required', { field: t('fields.packageName') }) },
            ]}
          >
            <Input />
          </Form.Item>
          <Form.Item name="version" label={t('fields.version')}>
            <Input />
          </Form.Item>
          <Form.Item
            name="platform"
            label={t('fields.platform')}
            rules={[{ required: true, message: t('validation.required', { field: t('fields.platform') }) }]}
          >
            <Select placeholder={t('placeholders.select', { item: t('fields.platform') })}>
              {platformOptions.map((platform) => (
                <Select.Option key={platform} value={platform}>
                  {platform}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="bundle_id" label={t('fields.bundleId')}>
            <Input />
          </Form.Item>
          <Form.Item name="risk_score" label={t('fields.riskScore')}>
            <InputNumber min={0} max={10} step={0.1} style={{ width: '100%' }} />
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
          {!editingApp && (
            <Form.Item name="created_by" label={t('common.createdBy')}>
              <Input />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
};

export default ClientApplicationList;
