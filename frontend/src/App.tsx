import { ConfigProvider } from 'antd';
import enUS from 'antd/locale/en_US';
import zhCN from 'antd/locale/zh_CN';
import AppRouter from './router/AppRouter';
import { useI18n } from '@/i18n';

const App = () => {
  const { locale } = useI18n();

  return (
    <ConfigProvider locale={locale === 'zh' ? zhCN : enUS}>
      <AppRouter />
    </ConfigProvider>
  );
};

export default App;
