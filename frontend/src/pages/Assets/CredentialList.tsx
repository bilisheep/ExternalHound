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
  useCredentialList,
  useCreateCredential,
  useUpdateCredential,
  useDeleteCredential,
} from '@/hooks/useAssets';
import type {
  CredentialAsset,
  CredentialCreatePayload,
  CredentialUpdatePayload,
  ScopePolicy,
} from '@/types/asset';
import { cleanPayload } from '@/utils/forms';
import { formatJson, safeParseJson } from '@/utils/json';
import { useI18n } from '@/i18n';

const scopeColors: Record<ScopePolicy, string> = {
  IN_SCOPE: 'green',
  OUT_OF_SCOPE: 'red',
};

const credTypeOptions = [
  'PASSWORD',
  'API_KEY',
  'TOKEN',
  'SSH_KEY',
  'CERTIFICATE',
  'COOKIE',
  'SESSION',
  'DATABASE',
  'AWS_KEY',
  'AZURE_KEY',
  'GCP_KEY',
  'OTHER',
];

const validationOptions = ['VALID', 'INVALID', 'UNKNOWN'];

const CredentialList = () => {
  const { t } = useI18n();
  const [form] = Form.useForm();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [filters, setFilters] = useState({
    cred_type: undefined as string | undefined,
    provider: undefined as string | undefined,
    validation_result: undefined as string | undefined,
    scope_policy: undefined as ScopePolicy | undefined,
  });
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCredential, setEditingCredential] = useState<CredentialAsset | null>(null);

  const { data, isLoading, refetch } = useCredentialList({
    page,
    page_size: pageSize,
    ...filters,
  });

  const createMutation = useCreateCredential();
  const updateMutation = useUpdateCredential();
  const deleteMutation = useDeleteCredential();
  const scopeLabel = (policy: ScopePolicy) =>
    policy === 'IN_SCOPE' ? t('scope.inScope') : t('scope.outOfScope');
  const credentialLabel = (value: string) => t(`credType.${value}`);
  const validationLabel = (value: string) => t(`validation.${value}`);

  const openCreateModal = () => {
    setEditingCredential(null);
    form.resetFields();
    setIsModalOpen(true);
  };

  const openEditModal = (record: CredentialAsset) => {
    setEditingCredential(record);
    form.setFieldsValue({
      cred_type: record.cred_type,
      provider: record.provider ?? undefined,
      username: record.username ?? undefined,
      email: record.email ?? undefined,
      phone: record.phone ?? undefined,
      leaked_count: record.leaked_count,
      content: formatJson(record.content),
      validation_result: record.validation_result ?? undefined,
      scope_policy: record.scope_policy,
      metadata: formatJson(record.metadata),
    });
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingCredential(null);
    form.resetFields();
  };

  const handleSubmit = (values: Record<string, unknown>) => {
    const { value: contentValue, error: contentError } = safeParseJson(
      values.content as string | undefined
    );
    if (contentError) {
      message.error(t('errors.json.content'));
      return;
    }

    const { value: metadataValue, error: metadataError } = safeParseJson(
      values.metadata as string | undefined
    );
    if (metadataError) {
      message.error(t('errors.json.metadata'));
      return;
    }

    const payload = cleanPayload({
      ...values,
      content: contentValue,
      metadata: metadataValue,
    });

    if (editingCredential) {
      updateMutation.mutate(
        { id: editingCredential.id, payload: payload as CredentialUpdatePayload },
        {
          onSuccess: () => closeModal(),
        }
      );
      return;
    }

    createMutation.mutate(payload as CredentialCreatePayload, {
      onSuccess: () => closeModal(),
    });
  };

  const columns = [
    {
      title: t('fields.type'),
      dataIndex: 'cred_type',
      key: 'cred_type',
      width: 140,
      render: (value: string) => credentialLabel(value),
    },
    {
      title: t('fields.provider'),
      dataIndex: 'provider',
      key: 'provider',
    },
    {
      title: t('fields.user'),
      key: 'user',
      render: (record: CredentialAsset) => record.username || record.email || t('common.empty'),
    },
    {
      title: t('fields.leaked'),
      dataIndex: 'leaked_count',
      key: 'leaked_count',
      width: 90,
    },
    {
      title: t('fields.validation'),
      dataIndex: 'validation_result',
      key: 'validation_result',
      width: 120,
      render: (value: string | null) =>
        value ? <Tag>{validationLabel(value)}</Tag> : t('common.empty'),
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
      render: (record: CredentialAsset) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => openEditModal(record)}
          />
          <Popconfirm
            title={t('confirm.deleteItem', { item: t('entities.credential') })}
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
          placeholder={t('fields.credentialType')}
          style={{ width: 200 }}
          allowClear
          onChange={(value) => setFilters({ ...filters, cred_type: value })}
        >
          {credTypeOptions.map((credType) => (
            <Select.Option key={credType} value={credType}>
              {credentialLabel(credType)}
            </Select.Option>
          ))}
        </Select>
        <Input
          placeholder={t('fields.provider')}
          style={{ width: 180 }}
          allowClear
          onChange={(event) =>
            setFilters({
              ...filters,
              provider: event.target.value || undefined,
            })
          }
        />
        <Select
          placeholder={t('fields.validation')}
          style={{ width: 160 }}
          allowClear
          onChange={(value) => setFilters({ ...filters, validation_result: value })}
        >
          {validationOptions.map((option) => (
            <Select.Option key={option} value={option}>
              {validationLabel(option)}
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
          {t('actions.new', { item: t('entities.credential') })}
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
          editingCredential
            ? t('actions.edit', { item: t('entities.credential') })
            : t('actions.create', { item: t('entities.credential') })
        }
        open={isModalOpen}
        onCancel={closeModal}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          {!editingCredential && (
            <Form.Item
              name="external_id"
              label={t('fields.externalId')}
            >
              <Input placeholder="cred:PASSWORD:sha256:abcd1234" />
            </Form.Item>
          )}
          <Form.Item
            name="cred_type"
            label={t('fields.credentialType')}
            rules={[
              {
                required: true,
                message: t('validation.required', { field: t('fields.credentialType') }),
              },
            ]}
          >
            <Select placeholder={t('placeholders.select', { item: t('fields.credentialType') })}>
              {credTypeOptions.map((credType) => (
                <Select.Option key={credType} value={credType}>
                  {credentialLabel(credType)}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="provider" label={t('fields.provider')}>
            <Input />
          </Form.Item>
          <Form.Item name="username" label={t('fields.username')}>
            <Input />
          </Form.Item>
          <Form.Item name="email" label={t('fields.email')}>
            <Input />
          </Form.Item>
          <Form.Item name="phone" label={t('fields.phone')}>
            <Input />
          </Form.Item>
          <Form.Item name="leaked_count" label={t('fields.leakedCount')}>
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="content" label={t('fields.contentJson')}>
            <Input.TextArea rows={4} />
          </Form.Item>
          <Form.Item name="validation_result" label={t('fields.validationResult')}>
            <Select allowClear placeholder={validationLabel('UNKNOWN')}>
              {validationOptions.map((option) => (
                <Select.Option key={option} value={option}>
                  {validationLabel(option)}
                </Select.Option>
              ))}
            </Select>
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
          {!editingCredential && (
            <Form.Item name="created_by" label={t('common.createdBy')}>
              <Input />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
};

export default CredentialList;
