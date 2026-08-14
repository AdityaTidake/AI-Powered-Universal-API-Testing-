import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { useAuthStore } from './store/authStore';

// Pages
import LoginPage      from './pages/LoginPage';
import RegisterPage   from './pages/RegisterPage';
import DashboardPage  from './pages/DashboardPage';
import ProjectsPage   from './pages/ProjectsPage';
import TestRunsPage   from './pages/TestRunsPage';
import AnalyticsPage  from './pages/AnalyticsPage';
import AIInsightsPage from './pages/AIInsightsPage';
import SettingsPage   from './pages/SettingsPage';
import OrgsPage       from './pages/OrgsPage';
import RunDetailsPage from './pages/RunDetailsPage';

// Guards
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  const init = useAuthStore(s => s.init);

  // Re-hydrate user profile from stored token on every page load
  useEffect(() => {
    init();
  }, [init]);

  return (
    <BrowserRouter>
      {/* Global toast notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#fff',
            color: '#0F172A',
            border: '1px solid #E2E8F0',
            borderRadius: '10px',
            fontSize: '0.875rem',
            fontFamily: 'Inter, sans-serif',
            boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.08)',
          },
          success: {
            iconTheme: { primary: '#10B981', secondary: '#fff' },
          },
          error: {
            iconTheme: { primary: '#EF4444', secondary: '#fff' },
          },
        }}
      />

      <Routes>
        {/* Public routes */}
        <Route path="/login"    element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected routes */}
        <Route path="/dashboard" element={
          <ProtectedRoute><DashboardPage /></ProtectedRoute>
        } />
        <Route path="/projects" element={
          <ProtectedRoute><ProjectsPage /></ProtectedRoute>
        } />
        <Route path="/runs" element={
          <ProtectedRoute><TestRunsPage /></ProtectedRoute>
        } />
        <Route path="/runs/:id" element={
          <ProtectedRoute><RunDetailsPage /></ProtectedRoute>
        } />
        <Route path="/orgs" element={
          <ProtectedRoute><OrgsPage /></ProtectedRoute>
        } />
        <Route path="/analytics" element={
          <ProtectedRoute><AnalyticsPage /></ProtectedRoute>
        } />
        <Route path="/ai-insights" element={
          <ProtectedRoute><AIInsightsPage /></ProtectedRoute>
        } />
        <Route path="/settings" element={
          <ProtectedRoute><SettingsPage /></ProtectedRoute>
        } />

        {/* Default redirects */}
        <Route path="/"   element={<Navigate to="/dashboard" replace />} />
        <Route path="*"   element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
