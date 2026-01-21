import { useState } from 'react';
import {
  Table,
  Button,
  Space,
  Tag,
  Input,
  Select,
  Popconfirm,
  Form,
  Modal,
  InputNumber,
  Switch,
  message,
} from 'antd';
import { ReloadOutlined, DeleteOutlined, PlusOutlined, EditOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useCreateIP, useDeleteIP, useIPList, useUpdateIP } from '@/hooks/useAssets';
import type { IPAsset, IPCreatePayload, IPUpdatePayload, ScopePolicy } from '@/types/asset';
import { cleanPayload } from '@/utils/forms';
import { formatJson, safeParseJson } from '@/utils/json';
import { useI18n } from '@/i18n';

const scopeColors: Record<ScopePolicy, string> = {
  IN_SCOPE: 'green',
  OUT_OF_SCOPE: 'red',
};

const IPList = () => {
  const navigate = useNavigate();
  const { t } = useI18n();
  const [form] = Form.useForm();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [filters, setFilters] = useState({
    scope_policy: undefined as ScopePolicy | undefined,
    is_cloud: undefined as boolean | undefined,
    country_code: undefined as string | undefined,
  });
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingIP, setEditingIP] = useState<IPAsset | null>(null);

  const { data, isLoading, refetch } = useIPList({
    page,
    page_size: pageSize,
    ...filters,
  });

  const createMutation = useCreateIP();
  const updateMutation = useUpdateIP();
  const deleteMutation = useDeleteIP();
  const scopeLabel = (policy: ScopePolicy) =>
    policy === 'IN_SCOPE' ? t('scope.inScope') : t('scope.outOfScope');

  const openCreateModal = () => {
    setEditingIP(null);
    form.resetFields();
    setIsModalOpen(true);
  };

  const openEditModal = (record: IPAsset) => {
    setEditingIP(record);
    form.setFieldsValue({
      is_cloud: record.is_cloud,
      is_internal: record.is_internal,
      is_cdn: record.is_cdn,
      open_ports_count: record.open_ports_count,
      risk_score: record.risk_score,
      vuln_critical_count: record.vuln_critical_count,
      country_code: record.country_code ?? undefined,
      asn_number: record.asn_number ?? undefined,
      scope_policy: record.scope_policy,
      metadata: formatJson(record.metadata),
    });
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingIP(null);
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

    if (editingIP) {
      updateMutation.mutate(
        { id: editingIP.id, payload: payload as IPUpdatePayload },
        {
          onSuccess: () => closeModal(),
        }
      );
      return;
    }

    createMutation.mutate(payload as IPCreatePayload, {
      onSuccess: () => closeModal(),
    });
  };

  const columns = [
    {
      title: t('fields.address'),
      dataIndex: 'address',
      key: 'address',
      render: (address: string) => (
        <Button type="link" onClick={() => navigate(`/assets/ips/${encodeURIComponent(address)}`)}>
          {address}
        </Button>
      ),
    },
    {
      title: t('fields.version'),
      dataIndex: 'version',
      key: 'version',
      width: 90,
      render: (version: number) => `IPv${version}`,
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
      title: t('common.flags'),
      key: 'flags',
      width: 150,
      render: (record: IPAsset) => (
        <Space>
          {record.is_cloud && <Tag color="blue">{t('labels.cloud')}</Tag>}
          {record.is_cdn && <Tag color="purple">{t('labels.cdn')}</Tag>}
          {record.is_internal && <Tag>{t('labels.internal')}</Tag>}
        </Space>
      ),
    },
    {
      title: t('fields.country'),
      dataIndex: 'country_code',
      key: 'country_code',
      width: 90,
    },
    {
      title: t('fields.asn'),
      dataIndex: 'asn_number',
      key: 'asn_number',
      width: 120,
    },
    {
      title: t('common.actions'),
      key: 'action',
      width: 140,
      render: (record: IPAsset) => (
        <Space>
          <Button
            type="link"
            size="small"
            onClick={() => navigate(`/assets/ips/${encodeURIComponent(record.address)}`)}
          >
            {t('common.view')}
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => openEditModal(record)}
          />
          <Popconfirm
            title={t('confirm.deleteItem', { item: t('entities.ip') })}
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
          placeholder={t('common.scope')}
          style={{ width: 160 }}
          allowClear
          onChange={(value) => setFilters({ ...filters, scope_policy: value })}
        >
          <Select.Option value="IN_SCOPE">{t('scope.inScope')}</Select.Option>
          <Select.Option value="OUT_OF_SCOPE">{t('scope.outOfScope')}</Select.Option>
        </Select>

        <Select
          placeholder={t('filters.cloud')}
          style={{ width: 120 }}
          allowClear
          onChange={(value) => setFilters({ ...filters, is_cloud: value })}
        >
          <Select.Option value={true}>{t('filters.cloud')}</Select.Option>
          <Select.Option value={false}>{t('filters.nonCloud')}</Select.Option>
        </Select>

        <Input
          placeholder={t('fields.countryCode')}
          style={{ width: 160 }}
          allowClear
          onChange={(event) =>
            setFilters({
              ...filters,
              country_code: event.target.value || undefined,
            })
          }
        />

        <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>
          {t('actions.new', { item: t('entities.ip') })}
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
          editingIP
            ? t('actions.edit', { item: t('entities.ip') })
            : t('actions.create', { item: t('entities.ip') })
        }
        open={isModalOpen}
        onCancel={closeModal}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          {!editingIP && (
            <>
            <Form.Item
              name="external_id"
              label={t('fields.externalId')}
            >
              <Input placeholder="ip:47.100.1.15" />
            </Form.Item>
              <Form.Item
                name="address"
                label={t('fields.ipAddress')}
                rules={[
                  { required: true, message: t('validation.required', { field: t('fields.ipAddress') }) },
                ]}
              >
                <Input placeholder="47.100.1.15" />
              </Form.Item>
              <Form.Item name="version" label={t('fields.version')}>
                <Select allowClear placeholder={t('common.autoDetect')}>
                  <Select.Option value={4}>IPv4</Select.Option>
                  <Select.Option value={6}>IPv6</Select.Option>
                </Select>
              </Form.Item>
            </>
          )}

          <Form.Item name="is_cloud" label={t('labels.cloud')} valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="is_internal" label={t('labels.internal')} valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="is_cdn" label={t('labels.cdn')} valuePropName="checked">
            <Switch />
          </Form.Item>

          {editingIP && (
            <>
              <Form.Item name="open_ports_count" label={t('fields.openPortsCount')}>
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item name="risk_score" label={t('fields.riskScore')}>
                <InputNumber min={0} max={10} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item name="vuln_critical_count" label={t('fields.criticalVulns')}>
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </>
          )}

          <Form.Item name="country_code" label={t('fields.countryCode')}>
            <Input placeholder="CN" />
          </Form.Item>
          <Form.Item name="asn_number" label={t('fields.asn')}>
            <Input placeholder="AS37963" />
          </Form.Item>
          <Form.Item name="scope_policy" label={t('common.scopePolicy')}>
            <Select allowClear placeholder={t('placeholders.select', { item: t('common.scopePolicy') })}>
              <Select.Option value="IN_SCOPE">{t('scope.inScope')}</Select.Option>
              <Select.Option value="OUT_OF_SCOPE">{t('scope.outOfScope')}</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="metadata" label={t('common.metadataJson')}>
            <Input.TextArea rows={4} placeholder='{"os_info":{"name":"Ubuntu"}}' />
          </Form.Item>
          {!editingIP && (
            <Form.Item name="created_by" label={t('common.createdBy')}>
              <Input />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
};

export default IPList;
