import { Card } from 'antd';
import { useI18n } from '@/i18n';
import ProjectSwitcher from '@/components/Layout/ProjectSwitcher';

const ProjectManagementPanel = () => {
  const { t } = useI18n();

  return (
    <Card
      title={t('projects.manage')}
      size="small"
      style={{ borderRadius: 12, borderColor: '#e2e8f0' }}
      styles={{ body: { padding: '12px 16px' } }}
    >
      <ProjectSwitcher />
    </Card>
  );
};

export default ProjectManagementPanel;
