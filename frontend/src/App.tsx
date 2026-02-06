
/**
 * Main App Component
 * Handles routing, theme, and global state
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import theme from './theme';

// Components
import MainLayout from './layouts/MainLayout';
import ProtectedRoute from './components/ProtectedRoute';

// Pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Products from './pages/Products';
import Partners from './pages/Partners';
import Orders from './pages/Orders';
import Approvals from './pages/Approvals';
import Namaste from './pages/Namaste';
import Users from './pages/Users';

// New Modules
import OrderEntry from './pages/OrderEntry';
import Reconciliation from './pages/Reconciliation';
import Ledger from './pages/Ledger';

const Profile = () => <div>Profile Page - Coming Soon</div>;

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<Login />} />

            {/* Protected Routes */}
            <Route path="/" element={
              <ProtectedRoute>
                <MainLayout>
                  <Navigate to="/dashboard" replace />
                </MainLayout>
              </ProtectedRoute>
            } />

            <Route path="/dashboard" element={
              <ProtectedRoute>
                <MainLayout>
                  <Dashboard />
                </MainLayout>
              </ProtectedRoute>
            } />

            <Route path="/products" element={
              <ProtectedRoute>
                <MainLayout>
                  <Products />
                </MainLayout>
              </ProtectedRoute>
            } />

            <Route path="/partners" element={
              <ProtectedRoute>
                <MainLayout>
                  <Partners />
                </MainLayout>
              </ProtectedRoute>
            } />

            <Route path="/orders" element={
              <ProtectedRoute>
                <MainLayout>
                  <Orders />
                </MainLayout>
              </ProtectedRoute>
            } />

            {/* NEW MODULE: Salesman Order Entry */}
            <Route path="/sales/orders" element={
              <ProtectedRoute allowedRoles={['salesman', 'admin', 'manager']}>
                <MainLayout>
                  <OrderEntry />
                </MainLayout>
              </ProtectedRoute>
            } />

            {/* NEW MODULE: Reconciliation */}
            <Route path="/accounts/reconciliation" element={
              <ProtectedRoute allowedRoles={['accountant', 'admin', 'manager']}>
                <MainLayout>
                  <Reconciliation />
                </MainLayout>
              </ProtectedRoute>
            } />

            {/* NEW MODULE: Ledger */}
            <Route path="/owner/ledger" element={
              <ProtectedRoute allowedRoles={['admin', 'manager', 'owner']}>
                <MainLayout>
                  <Ledger />
                </MainLayout>
              </ProtectedRoute>
            } />

            <Route path="/users" element={
              <ProtectedRoute allowedRoles={['admin']}>
                <MainLayout>
                  <Users />
                </MainLayout>
              </ProtectedRoute>
            } />

            <Route path="/approvals" element={
              <ProtectedRoute allowedRoles={['admin', 'manager']}>
                <MainLayout>
                  <Approvals />
                </MainLayout>
              </ProtectedRoute>
            } />

            <Route path="/namaste" element={
              <ProtectedRoute>
                <MainLayout>
                  <Namaste />
                </MainLayout>
              </ProtectedRoute>
            } />

            <Route path="/profile" element={
              <ProtectedRoute>
                <MainLayout>
                  <Profile />
                </MainLayout>
              </ProtectedRoute>
            } />

            {/* Catch all route */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Router>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
