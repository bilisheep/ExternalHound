import { Button, Layout, Menu } from 'antd';
import { Link, Outlet, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  GlobalOutlined,
  DatabaseOutlined,
  ApiOutlined,
  TeamOutlined,
  BlockOutlined,
  SafetyCertificateOutlined,
  MobileOutlined,
  KeyOutlined,
  ShareAltOutlined,
  ApartmentOutlined,
  UploadOutlined,
} from '@ant-design/icons';
import { useI18n } from '@/i18n';

const { Header, Sider, Content } = Layout;

const AppLayout = () => {
  const location = useLocation();
  const { locale, setLocale, t } = useI18n();
  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: <Link to="/">{t('menu.dashboard')}</Link>,
    },
    {
      key: '/assets/ips',
      icon: <DatabaseOutlined />,
      label: <Link to="/assets/ips">{t('menu.ips')}</Link>,
    },
    {
      key: '/assets/organizations',
      icon: <TeamOutlined />,
      label: <Link to="/assets/organizations">{t('menu.organizations')}</Link>,
    },
    {
      key: '/assets/domains',
      icon: <GlobalOutlined />,
      label: <Link to="/assets/domains">{t('menu.domains')}</Link>,
    },
    {
      key: '/assets/netblocks',
      icon: <BlockOutlined />,
      label: <Link to="/assets/netblocks">{t('menu.netblocks')}</Link>,
    },
    {
      key: '/assets/services',
      icon: <ApiOutlined />,
      label: <Link to="/assets/services">{t('menu.services')}</Link>,
    },
    {
      key: '/assets/certificates',
      icon: <SafetyCertificateOutlined />,
      label: <Link to="/assets/certificates">{t('menu.certificates')}</Link>,
    },
    {
      key: '/assets/client-applications',
      icon: <MobileOutlined />,
      label: <Link to="/assets/client-applications">{t('menu.clientApps')}</Link>,
    },
    {
      key: '/assets/credentials',
      icon: <KeyOutlined />,
      label: <Link to="/assets/credentials">{t('menu.credentials')}</Link>,
    },
    {
      key: '/graph',
      icon: <ApartmentOutlined />,
      label: <Link to="/graph">{t('menu.graph')}</Link>,
    },
    {
      key: '/imports',
      icon: <UploadOutlined />,
      label: <Link to="/imports">{t('menu.imports')}</Link>,
    },
    {
      key: '/relationships',
      icon: <ShareAltOutlined />,
      label: <Link to="/relationships">{t('menu.relationships')}</Link>,
    },
  ];
  const matched = menuItems
    .filter(
      (item) =>
        location.pathname === item.key || location.pathname.startsWith(`${item.key}/`),
    )
    .sort((a, b) => b.key.length - a.key.length)[0];
  const selectedKey = matched ? matched.key : '/';
  const nextLocale = locale === 'zh' ? 'en' : 'zh';
  const switchLabel =
    locale === 'zh' ? t('i18n.switchToEnglish') : t('i18n.switchToChinese');

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={220} theme="light">
        <div style={{ padding: '16px', fontWeight: 600 }}>{t('app.title')}</div>
        <Menu mode="inline" selectedKeys={[selectedKey]} items={menuItems} />
      </Sider>
      <Layout>
        <Header
          style={{
            background: '#fff',
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
          }}
        >
          <Button type="text" icon={<GlobalOutlined />} onClick={() => setLocale(nextLocale)}>
            {switchLabel}
          </Button>
        </Header>
        <Content style={{ margin: '24px', background: '#fff', padding: 24 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default AppLayout;
