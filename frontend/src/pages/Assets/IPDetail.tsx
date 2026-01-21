import { useParams } from 'react-router-dom';
import { Card, Descriptions, Tag, Space, Tabs, Empty } from 'antd';
import { useIPDetail } from '@/hooks/useAssets';
import type { ScopePolicy } from '@/types/asset';
import { useI18n } from '@/i18n';

const scopeColors: Record<ScopePolicy, string> = {
  IN_SCOPE: 'green',
  OUT_OF_SCOPE: 'red',
};

const IPDetail = () => {
  const { address } = useParams<{ address: string }>();
  const ipAddress = address ? decodeURIComponent(address) : '';
  const { data: ipAsset, isLoading } = useIPDetail(ipAddress);
  const { t } = useI18n();
  const scopeLabel = (policy: ScopePolicy) =>
    policy === 'IN_SCOPE' ? t('scope.inScope') : t('scope.outOfScope');

  if (isLoading) {
    return <Card loading />;
  }

  if (!ipAsset) {
    return <Empty description={t('details.notFound', { item: t('entities.ip') })} />;
  }

  return (
    <div>
      <Card title={t('details.title', { item: t('entities.ip'), value: ipAsset.address })}>
        <Descriptions column={2} size="middle">
          <Descriptions.Item label={t('fields.ipAddress')}>{ipAsset.address}</Descriptions.Item>
          <Descriptions.Item label={t('fields.version')}>IPv{ipAsset.version}</Descriptions.Item>
          <Descriptions.Item label={t('common.scope')}>
            <Tag color={scopeColors[ipAsset.scope_policy]}>{scopeLabel(ipAsset.scope_policy)}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label={t('common.flags')}>
            <Space>
              {ipAsset.is_cloud && <Tag color="blue">{t('labels.cloud')}</Tag>}
              {ipAsset.is_cdn && <Tag color="purple">{t('labels.cdn')}</Tag>}
              {ipAsset.is_internal && <Tag>{t('labels.internal')}</Tag>}
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label={t('fields.country')}>{ipAsset.country_code}</Descriptions.Item>
          <Descriptions.Item label={t('fields.asn')}>{ipAsset.asn_number}</Descriptions.Item>
          <Descriptions.Item label={t('fields.openPorts')}>{ipAsset.open_ports_count}</Descriptions.Item>
          <Descriptions.Item label={t('fields.riskScore')}>{ipAsset.risk_score}</Descriptions.Item>
          <Descriptions.Item label={t('fields.criticalVulns')}>
            {ipAsset.vuln_critical_count}
          </Descriptions.Item>
          <Descriptions.Item label={t('common.createdAt')}>{ipAsset.created_at}</Descriptions.Item>
          <Descriptions.Item label={t('common.updatedAt')}>{ipAsset.updated_at}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card style={{ marginTop: 16 }}>
        <Tabs
          items={[
            {
              key: 'metadata',
              label: t('common.metadata'),
              children: (
                <pre style={{ margin: 0 }}>{JSON.stringify(ipAsset.metadata, null, 2)}</pre>
              ),
            },
          ]}
        />
      </Card>
    </div>
  );
};

export default IPDetail;
