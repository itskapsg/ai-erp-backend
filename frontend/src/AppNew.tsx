
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@mui/material/styles';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import theme from './theme';
import DashboardLayout from './layout/DashboardLayout';

// Placeholder Pages (will implement soon)
import OrderEntry from '@/pages/OrderEntry';
import Reconciliation from '@/pages/Reconciliation';
import Ledger from '@/pages/Ledger';

const Dashboard = () => <div><h1>Dashboard</h1><p>Welcome to JGandhi Tex ERP.</p></div>;
const Login = () => <div><h1>Login</h1></div>;

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />

            <Route path="/" element={<DashboardLayout />}>
              <Route index element={<Dashboard />} />
              <Route path="sales/orders" element={<OrderEntry />} />
              <Route path="accounts/reconciliation" element={<Reconciliation />} />
              <Route path="owner/ledger" element={<Ledger />} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
