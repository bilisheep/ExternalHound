import { Result, Button } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useI18n } from '@/i18n';

const NotFound = () => {
  const navigate = useNavigate();
  const { t } = useI18n();

  return (
    <Result
      status="404"
      title="404"
      subTitle={t('errors.notFound.subtitle')}
      extra={
        <Button type="primary" onClick={() => navigate('/')}>
          {t('errors.notFound.backHome')}
        </Button>
      }
    />
  );
};

export default NotFound;
