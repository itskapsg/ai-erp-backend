/**
 * Dashboard - Overview and Quick Actions
 * Responsive dashboard with key metrics and pending approvals
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Avatar,
  useTheme,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  Business,
  People,
  CheckCircle,
  Pending,
  TrendingUp,
  Notifications,
  Dashboard as DashboardIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { partnersAPI, tokenManager } from '../services/api';

const Dashboard = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const user = tokenManager.getUser();
  
  const [stats, setStats] = useState({
    totalPartners: 0,
    pendingApprovals: 0,
    approvedToday: 0,
    recentPartners: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const partners = await partnersAPI.getPartners();
      
      const totalPartners = partners.length;
      const pendingApprovals = partners.filter(p => p.workflow_stage === 'pending_approval').length;
      const approvedToday = partners.filter(p => {
        const today = new Date().toDateString();
        const updatedDate = new Date(p.updated_at).toDateString();
        return p.workflow_stage === 'approved' && updatedDate === today;
      }).length;
      
      const recentPartners = partners
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        .slice(0, 5);

      setStats({
        totalPartners,
        pendingApprovals,
        approvedToday,
        recentPartners
      });
      setError('');
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ title, value, icon, color, subtitle, onClick }) => (
    <Card 
      sx={{ 
        cursor: onClick ? 'pointer' : 'default',
        transition: 'transform 0.2s',
        '&:hover': onClick ? { transform: 'translateY(-2px)' } : {}
      }}
      onClick={onClick}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography color="textSecondary" gutterBottom variant="h6">
              {title}
            </Typography>
            <Typography variant="h4" component="div" fontWeight="bold">
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="textSecondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          <Avatar sx={{ bgcolor: color, width: 56, height: 56 }}>
            {icon}
          </Avatar>
        </Box>
      </CardContent>
    </Card>
  );

  const getStatusChip = (status) => {
    const statusConfig = {
      approved: { color: 'success', label: 'Approved' },
      pending_approval: { color: 'warning', label: 'Pending' },
      rejected: { color: 'error', label: 'Rejected' }
    };
    
    const config = statusConfig[status] || statusConfig.pending_approval;
    
    return (
      <Chip
        label={config.label}
        color={config.color}
        size="small"
        variant="outlined"
      />
    );
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* Welcome Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" fontWeight="bold" gutterBottom>
          Welcome back, {user?.username}! 👋
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Here's what's happening with your ERP system today.
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Partners"
            value={stats.totalPartners}
            icon={<Business />}
            color={theme.palette.primary.main}
            subtitle="Active partners"
            onClick={() => navigate('/partners')}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Pending Approvals"
            value={stats.pendingApprovals}
            icon={<Pending />}
            color={theme.palette.warning.main}
            subtitle="Awaiting review"
            onClick={() => navigate('/partners')}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Approved Today"
            value={stats.approvedToday}
            icon={<CheckCircle />}
            color={theme.palette.success.main}
            subtitle="Processed today"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="System Health"
            value="100%"
            icon={<TrendingUp />}
            color={theme.palette.info.main}
            subtitle="All systems operational"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Recent Partners */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <DashboardIcon sx={{ mr: 1 }} />
                <Typography variant="h6" component="h2">
                  Recent Partners
                </Typography>
              </Box>
              
              {stats.recentPartners.length > 0 ? (
                <List>
                  {stats.recentPartners.map((partner, index) => (
                    <ListItem key={partner.id} divider={index < stats.recentPartners.length - 1}>
                      <ListItemIcon>
                        <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32 }}>
                          {partner.name.charAt(0)}
                        </Avatar>
                      </ListItemIcon>
                      <ListItemText
                        primary={partner.name}
                        secondary={`${partner.type.toUpperCase()} • ₹${parseFloat(partner.credit_limit).toLocaleString()}`}
                      />
                      <Box sx={{ ml: 2 }}>
                        {getStatusChip(partner.workflow_stage)}
                      </Box>
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Business sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                  <Typography variant="body1" color="text.secondary">
                    No partners yet
                  </Typography>
                  <Button
                    variant="contained"
                    sx={{ mt: 2 }}
                    onClick={() => navigate('/partners')}
                  >
                    Create First Partner
                  </Button>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Notifications sx={{ mr: 1 }} />
                <Typography variant="h6" component="h2">
                  Quick Actions
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Button
                  variant="contained"
                  fullWidth
                  startIcon={<Business />}
                  onClick={() => navigate('/partners')}
                >
                  Manage Partners
                </Button>
                
                {(user?.role === 'admin' || user?.role === 'manager') && (
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<CheckCircle />}
                    onClick={() => navigate('/partners')}
                    color="success"
                  >
                    Review Approvals ({stats.pendingApprovals})
                  </Button>
                )}
                
                <Button
                  variant="outlined"
                  fullWidth
                  startIcon={<People />}
                  onClick={() => navigate('/users')}
                >
                  User Management
                </Button>
              </Box>

              {/* Role-based features */}
              <Box sx={{ mt: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Your Role: <strong>{user?.role?.toUpperCase()}</strong>
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {user?.role === 'admin' && 'Full system access with approval rights'}
                  {user?.role === 'manager' && 'Can approve partner requests'}
                  {user?.role === 'accountant' && 'Financial data access'}
                  {user?.role === 'salesman' && 'Partner creation and management'}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;