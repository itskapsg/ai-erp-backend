import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  IconButton,
  Tooltip,
  useTheme,
  useMediaQuery,
  Divider,
  Avatar,
  Stack
} from '@mui/material';
import {
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
  Business as BusinessIcon,
  Person as PersonIcon,
  AccessTime as TimeIcon,
  Refresh as RefreshIcon,
  History as HistoryIcon,
  PendingActions as PendingIcon
} from '@mui/icons-material';
import { approvalsAPI } from '../services/api';
import { tokenManager } from '../services/api';
import { formatDistanceToNow } from 'date-fns';

const Approvals = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  // State management
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [approvalHistory, setApprovalHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [currentTab, setCurrentTab] = useState(0);
  
  // Dialog states
  const [rejectDialog, setRejectDialog] = useState({ open: false, partner: null });
  const [rejectReason, setRejectReason] = useState('');
  const [actionLoading, setActionLoading] = useState(null);
  
  // Alert state
  const [alert, setAlert] = useState({ show: false, message: '', severity: 'success' });
  
  // Get current user
  const currentUser = tokenManager.getUser();
  const canApprove = currentUser && ['admin', 'manager'].includes(currentUser.role);

  // Load data
  const loadPendingApprovals = async () => {
    try {
      const data = await approvalsAPI.fetchPendingApprovals();
      setPendingApprovals(data);
    } catch (error) {
      console.error('Error loading pending approvals:', error);
      showAlert('Failed to load pending approvals', 'error');
    }
  };

  const loadApprovalHistory = async () => {
    try {
      const data = await approvalsAPI.getApprovalHistory({ limit: 20 });
      setApprovalHistory(data);
    } catch (error) {
      console.error('Error loading approval history:', error);
      // Don't show error for history as it's not critical
    }
  };

  const loadData = async () => {
    setLoading(true);
    await Promise.all([
      loadPendingApprovals(),
      loadApprovalHistory()
    ]);
    setLoading(false);
  };

  const refreshData = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  useEffect(() => {
    loadData();
  }, []);

  // Helper functions
  const showAlert = (message, severity = 'success') => {
    setAlert({ show: true, message, severity });
    setTimeout(() => setAlert({ show: false, message: '', severity: 'success' }), 5000);
  };

  const getPartnerTypeIcon = (type) => {
    return type === 'customer' ? <PersonIcon /> : <BusinessIcon />;
  };

  const getPartnerTypeColor = (type) => {
    return type === 'customer' ? 'primary' : 'secondary';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending_approval': return 'warning';
      case 'approved': return 'success';
      case 'rejected': return 'error';
      default: return 'default';
    }
  };

  // Action handlers
  const handleApprove = async (partner) => {
    if (!canApprove) {
      showAlert('You do not have permission to approve items', 'error');
      return;
    }

    setActionLoading(partner.id);
    try {
      await approvalsAPI.approvePartner(partner.id);
      showAlert(`${partner.name} has been approved successfully!`, 'success');
      await loadPendingApprovals();
    } catch (error) {
      console.error('Error approving partner:', error);
      showAlert('Failed to approve partner', 'error');
    } finally {
      setActionLoading(null);
    }
  };

  const handleRejectClick = (partner) => {
    if (!canApprove) {
      showAlert('You do not have permission to reject items', 'error');
      return;
    }
    setRejectDialog({ open: true, partner });
    setRejectReason('');
  };

  const handleRejectConfirm = async () => {
    if (!rejectReason.trim()) {
      showAlert('Please provide a reason for rejection', 'error');
      return;
    }

    const partner = rejectDialog.partner;
    setActionLoading(partner.id);
    
    try {
      await approvalsAPI.rejectPartner(partner.id, rejectReason);
      showAlert(`${partner.name} has been rejected`, 'success');
      setRejectDialog({ open: false, partner: null });
      setRejectReason('');
      await loadPendingApprovals();
    } catch (error) {
      console.error('Error rejecting partner:', error);
      showAlert('Failed to reject partner', 'error');
    } finally {
      setActionLoading(null);
    }
  };

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  // Render components
  const renderPendingApprovalCard = (partner) => (
    <Card 
      key={partner.id} 
      sx={{ 
        mb: 2, 
        border: '1px solid',
        borderColor: 'warning.light',
        '&:hover': { 
          boxShadow: 4,
          borderColor: 'warning.main'
        }
      }}
    >
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            <Avatar sx={{ bgcolor: getPartnerTypeColor(partner.type) + '.main' }}>
              {getPartnerTypeIcon(partner.type)}
            </Avatar>
            <Box>
              <Typography variant="h6" component="div">
                {partner.name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {partner.gst_number || 'No GST Number'}
              </Typography>
            </Box>
          </Box>
          <Chip 
            label={partner.type.toUpperCase()} 
            color={getPartnerTypeColor(partner.type)}
            size="small"
          />
        </Box>

        <Grid container spacing={2} sx={{ mb: 2 }}>
          <Grid item xs={12} sm={6}>
            <Box display="flex" alignItems="center" gap={1}>
              <TimeIcon fontSize="small" color="action" />
              <Typography variant="body2" color="text.secondary">
                Created {formatDistanceToNow(new Date(partner.created_at))} ago
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" color="text.secondary">
              Credit Limit: ${partner.credit_limit || '0.00'}
            </Typography>
          </Grid>
        </Grid>

        <Chip 
          icon={<PendingIcon />}
          label="Pending Approval" 
          color="warning" 
          variant="outlined"
          size="small"
        />
      </CardContent>

      {canApprove && (
        <CardActions sx={{ justifyContent: 'flex-end', pt: 0 }}>
          <Button
            startIcon={<RejectIcon />}
            color="error"
            variant="outlined"
            size="small"
            onClick={() => handleRejectClick(partner)}
            disabled={actionLoading === partner.id}
          >
            Reject
          </Button>
          <Button
            startIcon={<ApproveIcon />}
            color="success"
            variant="contained"
            size="small"
            onClick={() => handleApprove(partner)}
            disabled={actionLoading === partner.id}
          >
            {actionLoading === partner.id ? <CircularProgress size={16} /> : 'Approve'}
          </Button>
        </CardActions>
      )}
    </Card>
  );

  const renderHistoryCard = (item) => (
    <Card key={item.id} sx={{ mb: 2, opacity: 0.8 }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box display="flex" alignItems="center" gap={1}>
            <Avatar sx={{ bgcolor: getPartnerTypeColor(item.type) + '.main' }}>
              {getPartnerTypeIcon(item.type)}
            </Avatar>
            <Box>
              <Typography variant="h6" component="div">
                {item.name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {item.approved_by ? `By ${item.approved_by}` : 'System'}
              </Typography>
            </Box>
          </Box>
          <Stack direction="row" spacing={1} alignItems="center">
            <Chip 
              label={item.workflow_stage.replace('_', ' ').toUpperCase()} 
              color={getStatusColor(item.workflow_stage)}
              size="small"
            />
            <Typography variant="caption" color="text.secondary">
              {formatDistanceToNow(new Date(item.updated_at))} ago
            </Typography>
          </Stack>
        </Box>
        
        {item.rejection_reason && (
          <Box mt={2}>
            <Typography variant="body2" color="error.main">
              Reason: {item.rejection_reason}
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );

  const renderEmptyState = () => (
    <Box 
      display="flex" 
      flexDirection="column" 
      alignItems="center" 
      justifyContent="center" 
      py={8}
      textAlign="center"
    >
      <CheckCircle sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
      <Typography variant="h5" gutterBottom>
        All caught up!
      </Typography>
      <Typography variant="body1" color="text.secondary" mb={3}>
        No pending approvals at the moment.
      </Typography>
      <Button 
        variant="outlined" 
        startIcon={<RefreshIcon />}
        onClick={refreshData}
        disabled={refreshing}
      >
        {refreshing ? 'Refreshing...' : 'Refresh'}
      </Button>
    </Box>
  );

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: isMobile ? 2 : 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Approvals
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage pending approvals and view approval history
          </Typography>
        </Box>
        <Tooltip title="Refresh">
          <IconButton onClick={refreshData} disabled={refreshing}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Alert */}
      {alert.show && (
        <Alert severity={alert.severity} sx={{ mb: 3 }} onClose={() => setAlert({ ...alert, show: false })}>
          {alert.message}
        </Alert>
      )}

      {/* Permission Warning */}
      {!canApprove && (
        <Alert severity="info" sx={{ mb: 3 }}>
          You have view-only access to approvals. Contact an admin or manager to approve/reject items.
        </Alert>
      )}

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={handleTabChange}>
          <Tab 
            icon={<PendingIcon />} 
            label={`Pending (${pendingApprovals.length})`} 
            iconPosition="start"
          />
          <Tab 
            icon={<HistoryIcon />} 
            label="History" 
            iconPosition="start"
          />
        </Tabs>
      </Box>

      {/* Tab Content */}
      {currentTab === 0 && (
        <Box>
          {pendingApprovals.length === 0 ? (
            renderEmptyState()
          ) : (
            <Grid container spacing={isMobile ? 2 : 3}>
              {pendingApprovals.map((partner) => (
                <Grid item xs={12} md={6} lg={4} key={partner.id}>
                  {renderPendingApprovalCard(partner)}
                </Grid>
              ))}
            </Grid>
          )}
        </Box>
      )}

      {currentTab === 1 && (
        <Box>
          {approvalHistory.length === 0 ? (
            <Box textAlign="center" py={4}>
              <Typography variant="body1" color="text.secondary">
                No approval history available
              </Typography>
            </Box>
          ) : (
            <Grid container spacing={isMobile ? 2 : 3}>
              {approvalHistory.map((item) => (
                <Grid item xs={12} md={6} lg={4} key={item.id}>
                  {renderHistoryCard(item)}
                </Grid>
              ))}
            </Grid>
          )}
        </Box>
      )}

      {/* Reject Dialog */}
      <Dialog 
        open={rejectDialog.open} 
        onClose={() => setRejectDialog({ open: false, partner: null })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Reject Partner: {rejectDialog.partner?.name}
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" mb={2}>
            Please provide a reason for rejecting this partner. This will be visible to the user who created it.
          </Typography>
          <TextField
            autoFocus
            margin="dense"
            label="Rejection Reason"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            placeholder="e.g., Incomplete documentation, Invalid GST number, etc."
          />
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setRejectDialog({ open: false, partner: null })}
            disabled={actionLoading}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleRejectConfirm} 
            color="error" 
            variant="contained"
            disabled={!rejectReason.trim() || actionLoading}
          >
            {actionLoading ? <CircularProgress size={16} /> : 'Reject'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Approvals;