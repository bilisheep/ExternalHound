import { useParams } from 'react-router-dom';
import { Card, Descriptions, Tag, Empty, Tabs } from 'antd';
import { useServiceDetail } from '@/hooks/useAssets';
import type { ScopePolicy } from '@/types/asset';
import { useI18n } from '@/i18n';

const scopeColors: Record<ScopePolicy, string> = {
  IN_SCOPE: 'green',
  OUT_OF_SCOPE: 'red',
};

const ServiceDetail = () => {
  const { id } = useParams<{ id: string }>();
  const { data: service, isLoading } = useServiceDetail(id || '');
  const { t } = useI18n();
  const scopeLabel = (policy: ScopePolicy) =>
    policy === 'IN_SCOPE' ? t('scope.inScope') : t('scope.outOfScope');

  if (isLoading) {
    return <Card loading />;
  }

  if (!service) {
    return <Empty description={t('details.notFound', { item: t('entities.service') })} />;
  }

  return (
    <div>
      <Card
        title={t('details.title', {
          item: t('entities.service'),
          value: service.service_name || service.external_id,
        })}
      >
        <Descriptions column={2} size="middle">
          <Descriptions.Item label={t('fields.id')}>{service.id}</Descriptions.Item>
          <Descriptions.Item label={t('fields.protocol')}>
            {service.protocol} / {service.port}
          </Descriptions.Item>
          <Descriptions.Item label={t('fields.serviceName')}>{service.service_name}</Descriptions.Item>
          <Descriptions.Item label={t('fields.product')}>{service.product}</Descriptions.Item>
          <Descriptions.Item label={t('fields.version')}>{service.version}</Descriptions.Item>
          <Descriptions.Item label={t('fields.http')}>
            {service.is_http ? <Tag color="green">{t('common.yes')}</Tag> : <Tag>{t('common.no')}</Tag>}
          </Descriptions.Item>
          <Descriptions.Item label={t('fields.riskScore')}>{service.risk_score}</Descriptions.Item>
          <Descriptions.Item label={t('fields.category')}>{service.asset_category}</Descriptions.Item>
          <Descriptions.Item label={t('common.scope')}>
            <Tag color={scopeColors[service.scope_policy]}>{scopeLabel(service.scope_policy)}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label={t('common.createdAt')}>{service.created_at}</Descriptions.Item>
          <Descriptions.Item label={t('common.updatedAt')}>{service.updated_at}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card style={{ marginTop: 16 }}>
        <Tabs
          items={[
            {
              key: 'metadata',
              label: t('common.metadata'),
              children: <pre style={{ margin: 0 }}>{JSON.stringify(service.metadata, null, 2)}</pre>,
            },
          ]}
        />
      </Card>
    </div>
  );
};

export default ServiceDetail;
