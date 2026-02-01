import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LoginPage } from '@/app/components/LoginPage';
import { Layout } from '@/app/components/Layout';
import { Dashboard } from '@/app/components/Dashboard';
import { ComponentsPage } from '@/app/components/ComponentsPage';
import { ComponentDetails } from '@/app/components/ComponentDetails';
import { AlertsPage } from '@/app/components/AlertsPage';
import { AnalyticsPage } from '@/app/components/AnalyticsPage';
import { LogsPage } from '@/app/components/LogsPage';
import { NotificationsPage } from '@/app/components/NotificationsPage';
import { DemoControlPanel } from '@/app/components/DemoControlPanel';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Login without auth */}
        <Route path="/" element={<LoginPage />} />

        {/* Protected routes with Layout */}
        <Route path="/overview" element={
          <Layout>
            <Dashboard />
          </Layout>
        } />
        <Route path="/machines" element={
          <Layout>
            <ComponentsPage />
          </Layout>
        } />
        <Route path="/plant/:plantId" element={
          <Layout>
            <ComponentsPage />
          </Layout>
        } />
        <Route path="/component/:componentId" element={
          <Layout>
            <ComponentDetails />
          </Layout>
        } />
        <Route path="/alerts" element={
          <Layout>
            <AlertsPage />
          </Layout>
        } />
        <Route path="/analytics" element={
          <Layout>
            <AnalyticsPage />
          </Layout>
        } />
        <Route path="/logs" element={
          <Layout>
            <LogsPage />
          </Layout>
        } />
        <Route path="/notifications" element={
          <Layout>
            <NotificationsPage />
          </Layout>
        } />

        {/* Hidden demo control panel - open in separate window */}
        <Route path="/control" element={<DemoControlPanel />} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
