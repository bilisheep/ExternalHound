import { Button, Layout, Menu } from 'antd';
import type { MenuProps } from 'antd';
import { useEffect, useState } from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  AppstoreOutlined,
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
  SettingOutlined,
} from '@ant-design/icons';
import { useI18n } from '@/i18n';

const { Header, Sider, Content } = Layout;

type MenuEntry = {
  key: string;
  parentKey?: string;
};

const collectMenuEntries = (
  items: MenuProps['items'],
  parentKey?: string,
): MenuEntry[] => {
  if (!items) return [];
  const entries: MenuEntry[] = [];
  items.forEach((item) => {
    if (!item || typeof item !== 'object') return;
    if (!('key' in item) || item.key === undefined || item.key === null) return;
    const key = String(item.key);
    entries.push({ key, parentKey });
    if ('children' in item && item.children) {
      entries.push(...collectMenuEntries(item.children, key));
    }
  });
  return entries;
};

const AppLayout = () => {
  const location = useLocation();
  const { locale, setLocale, t } = useI18n();
  const [openKeys, setOpenKeys] = useState<string[]>([]);
  const menuItems: MenuProps['items'] = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: <Link to="/">{t('menu.dashboard')}</Link>,
    },
    {
      key: '/crud',
      icon: <AppstoreOutlined />,
      label: t('menu.crud'),
      children: [
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
          key: '/imports',
          icon: <UploadOutlined />,
          label: <Link to="/imports">{t('menu.imports')}</Link>,
        },
        {
          key: '/relationships',
          icon: <ShareAltOutlined />,
          label: <Link to="/relationships">{t('menu.relationships')}</Link>,
        },
      ],
    },
    {
      key: '/graph',
      icon: <ApartmentOutlined />,
      label: <Link to="/graph">{t('menu.graph')}</Link>,
    },
    {
      key: '/projects',
      icon: <SettingOutlined />,
      label: <Link to="/projects">{t('projects.manage')}</Link>,
    },
  ];
  const menuEntries = collectMenuEntries(menuItems);
  const matched = menuEntries
    .filter(
      (item) =>
        location.pathname === item.key || location.pathname.startsWith(`${item.key}/`),
    )
    .sort((a, b) => b.key.length - a.key.length)[0];
  const selectedKey = matched ? matched.key : '/';
  useEffect(() => {
    if (!matched?.parentKey) return;
    setOpenKeys((prev) =>
      prev.includes(matched.parentKey) ? prev : [matched.parentKey],
    );
  }, [matched?.parentKey]);
  const nextLocale = locale === 'zh' ? 'en' : 'zh';
  const switchLabel =
    locale === 'zh' ? t('i18n.switchToEnglish') : t('i18n.switchToChinese');

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={220} theme="light">
        <div style={{ padding: '16px', fontWeight: 600 }}>{t('app.title')}</div>
        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          openKeys={openKeys}
          onOpenChange={(keys) => setOpenKeys(keys as string[])}
          items={menuItems}
        />
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
