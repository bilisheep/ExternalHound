import { Card, Typography } from 'antd';
import { useI18n } from '@/i18n';

const Dashboard = () => {
  const { t } = useI18n();

  return (
    <Card>
      <Typography.Title level={4}>{t('dashboard.title')}</Typography.Title>
      <Typography.Paragraph>{t('dashboard.welcome')}</Typography.Paragraph>
    </Card>
  );
};

export default Dashboard;
