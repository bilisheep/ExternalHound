import { useParams } from 'react-router-dom';
import { Card, Descriptions, Tag, Empty, Tabs } from 'antd';
import { useDomainDetail } from '@/hooks/useAssets';
import type { ScopePolicy } from '@/types/asset';
import { useI18n } from '@/i18n';

const scopeColors: Record<ScopePolicy, string> = {
  IN_SCOPE: 'green',
  OUT_OF_SCOPE: 'red',
};

const DomainDetail = () => {
  const { name } = useParams<{ name: string }>();
  const domainName = name ? decodeURIComponent(name) : '';
  const { data: domain, isLoading } = useDomainDetail(domainName);
  const { t } = useI18n();
  const scopeLabel = (policy: ScopePolicy) =>
    policy === 'IN_SCOPE' ? t('scope.inScope') : t('scope.outOfScope');

  if (isLoading) {
    return <Card loading />;
  }

  if (!domain) {
    return <Empty description={t('details.notFound', { item: t('entities.domain') })} />;
  }

  return (
    <div>
      <Card title={t('details.title', { item: t('entities.domain'), value: domain.name })}>
        <Descriptions column={2} size="middle">
          <Descriptions.Item label={t('fields.domain')}>{domain.name}</Descriptions.Item>
          <Descriptions.Item label={t('fields.rootDomain')}>{domain.root_domain}</Descriptions.Item>
          <Descriptions.Item label={t('fields.tier')}>{domain.tier}</Descriptions.Item>
          <Descriptions.Item label={t('fields.resolved')}>
            {domain.is_resolved ? <Tag color="green">{t('common.yes')}</Tag> : <Tag>{t('common.no')}</Tag>}
          </Descriptions.Item>
          <Descriptions.Item label={t('fields.wildcard')}>
            {domain.is_wildcard ? (
              <Tag color="orange">{t('common.yes')}</Tag>
            ) : (
              <Tag>{t('common.no')}</Tag>
            )}
          </Descriptions.Item>
          <Descriptions.Item label={t('labels.internal')}>
            {domain.is_internal ? <Tag>{t('common.yes')}</Tag> : <Tag>{t('common.no')}</Tag>}
          </Descriptions.Item>
          <Descriptions.Item label={t('fields.waf')}>
            {domain.has_waf ? <Tag color="blue">{t('common.yes')}</Tag> : <Tag>{t('common.no')}</Tag>}
          </Descriptions.Item>
          <Descriptions.Item label={t('common.scope')}>
            <Tag color={scopeColors[domain.scope_policy]}>{scopeLabel(domain.scope_policy)}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label={t('common.createdAt')}>{domain.created_at}</Descriptions.Item>
          <Descriptions.Item label={t('common.updatedAt')}>{domain.updated_at}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card style={{ marginTop: 16 }}>
        <Tabs
          items={[
            {
              key: 'metadata',
              label: t('common.metadata'),
              children: <pre style={{ margin: 0 }}>{JSON.stringify(domain.metadata, null, 2)}</pre>,
            },
          ]}
        />
      </Card>
    </div>
  );
};

export default DomainDetail;
