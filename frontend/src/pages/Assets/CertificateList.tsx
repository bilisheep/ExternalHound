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
  useCertificateList,
  useCreateCertificate,
  useUpdateCertificate,
  useDeleteCertificate,
} from '@/hooks/useAssets';
import type {
  CertificateAsset,
  CertificateCreatePayload,
  CertificateUpdatePayload,
  ScopePolicy,
} from '@/types/asset';
import { cleanPayload } from '@/utils/forms';
import { formatJson, safeParseJson } from '@/utils/json';
import { useI18n } from '@/i18n';

const scopeColors: Record<ScopePolicy, string> = {
  IN_SCOPE: 'green',
  OUT_OF_SCOPE: 'red',
};

const CertificateList = () => {
  const { t } = useI18n();
  const [form] = Form.useForm();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [filters, setFilters] = useState({
    is_expired: undefined as boolean | undefined,
    is_self_signed: undefined as boolean | undefined,
    is_revoked: undefined as boolean | undefined,
    scope_policy: undefined as ScopePolicy | undefined,
  });
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCertificate, setEditingCertificate] = useState<CertificateAsset | null>(null);

  const { data, isLoading, refetch } = useCertificateList({
    page,
    page_size: pageSize,
    ...filters,
  });

  const createMutation = useCreateCertificate();
  const updateMutation = useUpdateCertificate();
  const deleteMutation = useDeleteCertificate();
  const scopeLabel = (policy: ScopePolicy) =>
    policy === 'IN_SCOPE' ? t('scope.inScope') : t('scope.outOfScope');

  const openCreateModal = () => {
    setEditingCertificate(null);
    form.resetFields();
    setIsModalOpen(true);
  };

  const openEditModal = (record: CertificateAsset) => {
    setEditingCertificate(record);
    form.setFieldsValue({
      subject_cn: record.subject_cn ?? undefined,
      issuer_cn: record.issuer_cn ?? undefined,
      issuer_org: record.issuer_org ?? undefined,
      valid_from: record.valid_from ?? undefined,
      valid_to: record.valid_to ?? undefined,
      days_to_expire: record.days_to_expire ?? undefined,
      is_expired: record.is_expired,
      is_self_signed: record.is_self_signed,
      is_revoked: record.is_revoked,
      san_count: record.san_count,
      scope_policy: record.scope_policy,
      metadata: formatJson(record.metadata),
    });
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingCertificate(null);
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

    if (editingCertificate) {
      updateMutation.mutate(
        { id: editingCertificate.id, payload: payload as CertificateUpdatePayload },
        {
          onSuccess: () => closeModal(),
        }
      );
      return;
    }

    createMutation.mutate(payload as CertificateCreatePayload, {
      onSuccess: () => closeModal(),
    });
  };

  const columns = [
    {
      title: t('fields.subjectCn'),
      dataIndex: 'subject_cn',
      key: 'subject_cn',
    },
    {
      title: t('fields.issuerCn'),
      dataIndex: 'issuer_cn',
      key: 'issuer_cn',
    },
    {
      title: t('fields.validTo'),
      dataIndex: 'valid_to',
      key: 'valid_to',
      width: 110,
    },
    {
      title: t('fields.expired'),
      dataIndex: 'is_expired',
      key: 'is_expired',
      width: 100,
      render: (value: boolean) =>
        value ? <Tag color="red">{t('common.yes')}</Tag> : <Tag>{t('common.no')}</Tag>,
    },
    {
      title: t('fields.revoked'),
      dataIndex: 'is_revoked',
      key: 'is_revoked',
      width: 100,
      render: (value: boolean) =>
        value ? <Tag color="volcano">{t('common.yes')}</Tag> : <Tag>{t('common.no')}</Tag>,
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
      render: (record: CertificateAsset) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => openEditModal(record)}
          />
          <Popconfirm
            title={t('confirm.deleteItem', { item: t('entities.certificate') })}
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
          placeholder={t('fields.expired')}
          style={{ width: 140 }}
          allowClear
          onChange={(value) => setFilters({ ...filters, is_expired: value })}
        >
          <Select.Option value={true}>{t('common.yes')}</Select.Option>
          <Select.Option value={false}>{t('common.no')}</Select.Option>
        </Select>
        <Select
          placeholder={t('fields.selfSigned')}
          style={{ width: 160 }}
          allowClear
          onChange={(value) => setFilters({ ...filters, is_self_signed: value })}
        >
          <Select.Option value={true}>{t('common.yes')}</Select.Option>
          <Select.Option value={false}>{t('common.no')}</Select.Option>
        </Select>
        <Select
          placeholder={t('fields.revoked')}
          style={{ width: 140 }}
          allowClear
          onChange={(value) => setFilters({ ...filters, is_revoked: value })}
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
          {t('actions.new', { item: t('entities.certificate') })}
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
          editingCertificate
            ? t('actions.edit', { item: t('entities.certificate') })
            : t('actions.create', { item: t('entities.certificate') })
        }
        open={isModalOpen}
        onCancel={closeModal}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          {!editingCertificate && (
            <Form.Item
              name="external_id"
              label={t('fields.externalId')}
            >
              <Input placeholder="cert:sha256:abcd1234" />
            </Form.Item>
          )}
          <Form.Item name="subject_cn" label={t('fields.subjectCn')}>
            <Input />
          </Form.Item>
          <Form.Item name="issuer_cn" label={t('fields.issuerCn')}>
            <Input />
          </Form.Item>
          <Form.Item name="issuer_org" label={t('fields.issuerOrg')}>
            <Input />
          </Form.Item>
          <Form.Item name="valid_from" label={t('fields.validFrom')}>
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="valid_to" label={t('fields.validTo')}>
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="days_to_expire" label={t('fields.daysToExpire')}>
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="is_expired" label={t('fields.expired')} valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="is_self_signed" label={t('fields.selfSigned')} valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="is_revoked" label={t('fields.revoked')} valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="san_count" label={t('fields.sanCount')}>
            <InputNumber min={0} style={{ width: '100%' }} />
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
          {!editingCertificate && (
            <Form.Item name="created_by" label={t('common.createdBy')}>
              <Input />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
};

export default CertificateList;
