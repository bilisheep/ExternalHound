import { useEffect, useMemo, useState } from 'react';
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
import {
  useAllDomains,
  useCreateDomain,
  useDeleteDomain,
  useDomainList,
  useUpdateDomain,
} from '@/hooks/useAssets';
import type {
  DomainAsset,
  DomainCreatePayload,
  DomainUpdatePayload,
  ScopePolicy,
} from '@/types/asset';
import { assetsApi } from '@/services/api/assets';
import { relationshipsApi } from '@/services/api/relationships';
import { cleanPayload } from '@/utils/forms';
import { formatJson, safeParseJson } from '@/utils/json';
import { useI18n } from '@/i18n';

const scopeColors: Record<ScopePolicy, string> = {
  IN_SCOPE: 'green',
  OUT_OF_SCOPE: 'red',
};

const normalizeDomain = (value?: string) =>
  value?.trim().toLowerCase().replace(/\.+$/, '') ?? '';

const calculateTier = (name?: string, rootDomain?: string) => {
  const normalizedName = normalizeDomain(name);
  if (!normalizedName) {
    return undefined;
  }
  const nameParts = normalizedName.split('.').filter(Boolean);
  if (nameParts.length === 0) {
    return undefined;
  }
  let tier = Math.max(1, nameParts.length - 1);
  const normalizedRoot = normalizeDomain(rootDomain);
  if (normalizedRoot) {
    if (
      normalizedName === normalizedRoot ||
      normalizedName.endsWith(`.${normalizedRoot}`)
    ) {
      const rootParts = normalizedRoot.split('.').filter(Boolean);
      if (rootParts.length > 0) {
        tier = Math.max(1, nameParts.length - rootParts.length + 1);
      }
    }
  }
  return tier;
};

const DomainList = () => {
  const navigate = useNavigate();
  const { t } = useI18n();
  const [form] = Form.useForm();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [filters, setFilters] = useState({
    root_domain: undefined as string | undefined,
    tier: undefined as number | undefined,
    is_resolved: undefined as boolean | undefined,
    has_waf: undefined as boolean | undefined,
    scope_policy: undefined as ScopePolicy | undefined,
  });
  const [rootDomainSearch, setRootDomainSearch] = useState('');
  const [isRootDomainOpen, setIsRootDomainOpen] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingDomain, setEditingDomain] = useState<DomainAsset | null>(null);
  const nameValue = Form.useWatch('name', form) as string | undefined;
  const rootDomainValue = Form.useWatch('root_domain', form) as string | undefined;

  const { data, isLoading, refetch } = useDomainList({
    page,
    page_size: pageSize,
    ...filters,
  });
  const { data: allDomains, isLoading: rootDomainLoading } = useAllDomains();

  const createMutation = useCreateDomain();
  const updateMutation = useUpdateDomain();
  const deleteMutation = useDeleteDomain();
  const scopeLabel = (policy: ScopePolicy) =>
    policy === 'IN_SCOPE' ? t('scope.inScope') : t('scope.outOfScope');

  const rootDomainOptions = useMemo(() => {
    if (!allDomains) {
      return [];
    }
    const seen = new Set<string>();
    const options = allDomains.reduce<{ value: string; label: string }[]>((acc, domain) => {
      const value = normalizeDomain(domain.root_domain ?? domain.name);
      if (!value || seen.has(value)) {
        return acc;
      }
      seen.add(value);
      acc.push({ value, label: value });
      return acc;
    }, []);
    options.sort((a, b) => a.label.localeCompare(b.label));
    return options;
  }, [allDomains]);

  const filteredRootDomainOptions = useMemo(() => {
    const keyword = rootDomainSearch.trim().toLowerCase();
    if (!keyword) {
      return rootDomainOptions;
    }
    return rootDomainOptions.filter((option) =>
      option.label.toLowerCase().includes(keyword)
    );
  }, [rootDomainOptions, rootDomainSearch]);

  useEffect(() => {
    if (editingDomain) {
      return;
    }
    const nextTier = calculateTier(nameValue, rootDomainValue);
    if (!nextTier) {
      return;
    }
    const currentTier = form.getFieldValue('tier');
    if (currentTier !== nextTier) {
      form.setFieldsValue({ tier: nextTier });
    }
  }, [editingDomain, form, nameValue, rootDomainValue]);

  const openCreateModal = () => {
    setEditingDomain(null);
    form.resetFields();
    setIsModalOpen(true);
  };

  const openEditModal = (record: DomainAsset) => {
    setEditingDomain(record);
    form.setFieldsValue({
      name: record.name,
      root_domain: record.root_domain ?? undefined,
      tier: record.tier,
      is_resolved: record.is_resolved,
      is_wildcard: record.is_wildcard,
      is_internal: record.is_internal,
      has_waf: record.has_waf,
      scope_policy: record.scope_policy,
      metadata: formatJson(record.metadata),
    });
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingDomain(null);
    form.resetFields();
  };

  const linkToRootDomain = async (domain: DomainAsset) => {
    const rootDomainName = domain.root_domain ?? undefined;
    const normalizedRoot = normalizeDomain(rootDomainName);
    if (!normalizedRoot) {
      return;
    }
    const normalizedName = normalizeDomain(domain.name);
    if (!normalizedName || normalizedRoot === normalizedName) {
      return;
    }
    try {
      const rootDomain = await assetsApi.getDomainByNameOptional(rootDomainName);
      if (!rootDomain) {
        return;
      }
      await relationshipsApi.createRelationshipIfMissing({
        source_external_id: rootDomain.external_id,
        source_type: 'Domain',
        target_external_id: domain.external_id,
        target_type: 'Domain',
        relation_type: 'SUBDOMAIN',
      });
    } catch (error) {
      message.error(t('errors.domain.subdomainLink'));
    }
  };

  const promptAutoLinkSubdomains = async (domain: DomainAsset) => {
    try {
      const subdomains = await assetsApi.getDomainSubdomains(domain.name);
      const candidates = subdomains.filter((item) => item.name !== domain.name);
      if (candidates.length === 0) {
        return;
      }

      Modal.confirm({
        title: t('confirm.autoLinkSubdomainsTitle'),
        content: t('confirm.autoLinkSubdomainsContent', {
          count: candidates.length,
          domain: domain.name,
        }),
        okText: t('common.yes'),
        cancelText: t('common.no'),
        onOk: async () => {
          const results = await Promise.allSettled(
            candidates.map((subdomain) =>
              relationshipsApi.createRelationship({
                source_external_id: domain.external_id,
                source_type: 'Domain',
                target_external_id: subdomain.external_id,
                target_type: 'Domain',
                relation_type: 'SUBDOMAIN',
              })
            )
          );
          const successCount = results.filter((result) => result.status === 'fulfilled').length;
          const failedCount = results.length - successCount;
          if (successCount > 0) {
            message.success(t('messages.subdomainLinked', { count: successCount }));
          }
          if (failedCount > 0) {
            message.warning(t('messages.subdomainLinkPartial', { count: failedCount }));
          }
        },
      });
    } catch (error) {
      message.error(t('errors.domain.subdomainFetch'));
    }
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

    if (editingDomain) {
      updateMutation.mutate(
        { id: editingDomain.id, payload: payload as DomainUpdatePayload },
        {
          onSuccess: () => closeModal(),
        }
      );
      return;
    }

    createMutation.mutate(payload as DomainCreatePayload, {
      onSuccess: (createdDomain) => {
        closeModal();
        void linkToRootDomain(createdDomain);
        const isRootDomain =
          !createdDomain.root_domain ||
          normalizeDomain(createdDomain.root_domain) === normalizeDomain(createdDomain.name);
        if (isRootDomain) {
          void promptAutoLinkSubdomains(createdDomain);
        }
      },
    });
  };

  const columns = [
    {
      title: t('fields.domain'),
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => (
        <Button type="link" onClick={() => navigate(`/assets/domains/${encodeURIComponent(name)}`)}>
          {name}
        </Button>
      ),
    },
    {
      title: t('fields.rootDomain'),
      dataIndex: 'root_domain',
      key: 'root_domain',
    },
    {
      title: t('fields.tier'),
      dataIndex: 'tier',
      key: 'tier',
      width: 80,
    },
    {
      title: t('fields.resolved'),
      dataIndex: 'is_resolved',
      key: 'is_resolved',
      width: 110,
      render: (value: boolean) =>
        value ? <Tag color="green">{t('common.yes')}</Tag> : <Tag>{t('common.no')}</Tag>,
    },
    {
      title: t('fields.waf'),
      dataIndex: 'has_waf',
      key: 'has_waf',
      width: 90,
      render: (value: boolean) =>
        value ? <Tag color="blue">{t('common.yes')}</Tag> : <Tag>{t('common.no')}</Tag>,
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
      render: (record: DomainAsset) => (
        <Space>
          <Button
            type="link"
            size="small"
            onClick={() => navigate(`/assets/domains/${encodeURIComponent(record.name)}`)}
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
            title={t('confirm.deleteItem', { item: t('entities.domain') })}
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
          showSearch
          allowClear
          placeholder={t('fields.rootDomain')}
          style={{ width: 220 }}
          options={filteredRootDomainOptions}
          loading={rootDomainLoading}
          value={filters.root_domain}
          open={isRootDomainOpen}
          filterOption={false}
          onDropdownVisibleChange={(open) => {
            setIsRootDomainOpen(open);
            if (!open) {
              setRootDomainSearch('');
            }
          }}
          onSearch={(value) => {
            setRootDomainSearch(value);
            if (!isRootDomainOpen) {
              setIsRootDomainOpen(true);
            }
          }}
          onChange={(value) => {
            setFilters({
              ...filters,
              root_domain: value || undefined,
            });
            setRootDomainSearch('');
            setIsRootDomainOpen(false);
          }}
        />
        <InputNumber
          min={1}
          placeholder={t('fields.tier')}
          onChange={(value) => setFilters({ ...filters, tier: value ?? undefined })}
        />
        <Select
          placeholder={t('fields.resolved')}
          style={{ width: 140 }}
          allowClear
          onChange={(value) => setFilters({ ...filters, is_resolved: value })}
        >
          <Select.Option value={true}>{t('common.yes')}</Select.Option>
          <Select.Option value={false}>{t('common.no')}</Select.Option>
        </Select>
        <Select
          placeholder={t('fields.waf')}
          style={{ width: 120 }}
          allowClear
          onChange={(value) => setFilters({ ...filters, has_waf: value })}
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
          {t('actions.new', { item: t('entities.domain') })}
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
          editingDomain
            ? t('actions.edit', { item: t('entities.domain') })
            : t('actions.create', { item: t('entities.domain') })
        }
        open={isModalOpen}
        onCancel={closeModal}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          {!editingDomain && (
            <>
              <Form.Item
                name="external_id"
                label={t('fields.externalId')}
              >
                <Input placeholder="domain:api.target.com" />
              </Form.Item>
            </>
          )}
          <Form.Item
            name="name"
            label={t('fields.domain')}
            rules={[
              { required: true, message: t('validation.required', { field: t('fields.domain') }) },
            ]}
          >
            <Input placeholder="api.target.com" />
          </Form.Item>
          <Form.Item name="root_domain" label={t('fields.rootDomain')}>
            <Input placeholder="target.com" />
          </Form.Item>
          <Form.Item name="tier" label={t('fields.tier')}>
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="is_resolved" label={t('fields.resolved')} valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="is_wildcard" label={t('fields.wildcard')} valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="is_internal" label={t('labels.internal')} valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="has_waf" label={t('fields.hasWaf')} valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="scope_policy" label={t('common.scopePolicy')}>
            <Select allowClear placeholder={t('placeholders.select', { item: t('common.scopePolicy') })}>
              <Select.Option value="IN_SCOPE">{t('scope.inScope')}</Select.Option>
              <Select.Option value="OUT_OF_SCOPE">{t('scope.outOfScope')}</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="metadata" label={t('common.metadataJson')}>
            <Input.TextArea rows={4} placeholder='{"records":{"A":["1.2.3.4"]}}' />
          </Form.Item>
          {!editingDomain && (
            <Form.Item name="created_by" label={t('common.createdBy')}>
              <Input />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
};

export default DomainList;
