import { Route, Routes } from 'react-router-dom';
import AppLayout from '@/components/Layout/AppLayout';
import Dashboard from '@/pages/Dashboard';
import IPList from '@/pages/Assets/IPList';
import IPDetail from '@/pages/Assets/IPDetail';
import DomainList from '@/pages/Assets/DomainList';
import DomainDetail from '@/pages/Assets/DomainDetail';
import ServiceList from '@/pages/Assets/ServiceList';
import ServiceDetail from '@/pages/Assets/ServiceDetail';
import OrganizationList from '@/pages/Assets/OrganizationList';
import NetblockList from '@/pages/Assets/NetblockList';
import CertificateList from '@/pages/Assets/CertificateList';
import ClientApplicationList from '@/pages/Assets/ClientApplicationList';
import CredentialList from '@/pages/Assets/CredentialList';
import RelationshipList from '@/pages/Relationships/RelationshipList';
import GraphExplorer from '@/pages/Graph/GraphExplorer';
import ImportManager from '@/pages/Imports/ImportManager';
import NotFound from '@/pages/Errors/NotFound';

const AppRouter = () => {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/assets/ips" element={<IPList />} />
        <Route path="/assets/ips/:address" element={<IPDetail />} />
        <Route path="/assets/domains" element={<DomainList />} />
        <Route path="/assets/domains/:name" element={<DomainDetail />} />
        <Route path="/assets/services" element={<ServiceList />} />
        <Route path="/assets/services/:id" element={<ServiceDetail />} />
        <Route path="/assets/organizations" element={<OrganizationList />} />
        <Route path="/assets/netblocks" element={<NetblockList />} />
        <Route path="/assets/certificates" element={<CertificateList />} />
        <Route path="/assets/client-applications" element={<ClientApplicationList />} />
        <Route path="/assets/credentials" element={<CredentialList />} />
        <Route path="/graph" element={<GraphExplorer />} />
        <Route path="/imports" element={<ImportManager />} />
        <Route path="/relationships" element={<RelationshipList />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
};

export default AppRouter;
