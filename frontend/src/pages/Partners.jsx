/**
 * Partners Page - Responsive Data Management
 * Desktop: Full DataGrid with all columns
 * Mobile: Simplified card view with essential info
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Alert,
  CircularProgress,
  Fab,
  useTheme,
  useMediaQuery,
  Grid,
  IconButton,
  Tooltip,
  Stack
} from '@mui/material';
import {
  Add as AddIcon,
  CheckCircle,
  Cancel,
  Pending,
  Business,
  Phone,
  Email,
  Refresh
} from '@mui/icons-material';
import { DataGrid } from '@mui/x-data-grid';
import { partnersAPI, tokenManager } from '../services/api';

const Partners = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const user = tokenManager.getUser();
  
  const [partners, setPartners] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [openApprovalDialog, setOpenApprovalDialog] = useState(false);
  const [selectedPartner, setSelectedPartner] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    type: 'customer',
    gst_number: '',
    credit_limit: ''
  });

  useEffect(() => {
    loadPartners();
  }, []);

  const loadPartners = async () => {
    try {
      setLoading(true);
      const data = await partnersAPI.getPartners();
      setPartners(data);
      setError('');
    } catch (err) {
      setError('Failed to load partners');
      console.error('Load partners error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePartner = async () => {
    try {
      await partnersAPI.createPartner({
        ...formData,
        credit_limit: parseFloat(formData.credit_limit)
      });
      setOpenDialog(false);
      setFormData({ name: '', type: 'customer', gst_number: '', credit_limit: '' });
      loadPartners();
    } catch (err) {
      setError('Failed to create partner');
      console.error('Create partner error:', err);
    }
  };

  const handleApproval = async (action) => {
    try {
      await partnersAPI.approvePartner(selectedPartner.id, action);
      setOpenApprovalDialog(false);
      setSelectedPartner(null);
      loadPartners();
    } catch (err) {
      setError(`Failed to ${action} partner`);
      console.error('Approval error:', err);
    }
  };

  const getStatusChip = (status) => {
    const statusConfig = {
      approved: { color: 'success', icon: <CheckCircle />, label: 'Approved' },
      pending_approval: { color: 'warning', icon: <Pending />, label: 'Pending' },
      rejected: { color: 'error', icon: <Cancel />, label: 'Rejected' }
    };
    
    const config = statusConfig[status] || statusConfig.pending_approval;
    
    return (
      <Chip
        icon={config.icon}
        label={config.label}
        color={config.color}
        size="small"
        variant="outlined"
      />
    );
  };

  const canApprove = user?.role === 'admin' || user?.role === 'manager';

  // Desktop DataGrid columns
  const columns = [
    { field: 'name', headerName: 'Name', width: 200, flex: 1 },
    { 
      field: 'type', 
      headerName: 'Type', 
      width: 120,
      renderCell: (params) => (
        <Chip 
          label={params.value.toUpperCase()} 
          size="small" 
          color={params.value === 'customer' ? 'primary' : 'secondary'}
        />
      )
    },
    { 
      field: 'gst_number', 
      headerName: 'GST Number', 
      width: 150,
      hide: isMobile 
    },
    { 
      field: 'credit_limit', 
      headerName: 'Credit Limit', 
      width: 130,
      renderCell: (params) => `₹${parseFloat(params.value).toLocaleString()}`,
      hide: isMobile
    },
    { 
      field: 'workflow_stage', 
      headerName: 'Status', 
      width: 130,
      renderCell: (params) => getStatusChip(params.value)
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 120,
      sortable: false,
      hide: !canApprove,
      renderCell: (params) => (
        params.row.workflow_stage === 'pending_approval' && canApprove ? (
          <Button
            size="small"
            variant="outlined"
            onClick={() => {
              setSelectedPartner(params.row);
              setOpenApprovalDialog(true);
            }}
          >
            Review
          </Button>
        ) : null
      )
    }
  ];

  // Mobile Card View
  const MobilePartnerCard = ({ partner }) => (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
          <Typography variant="h6" component="div">
            {partner.name}
          </Typography>
          {getStatusChip(partner.workflow_stage)}
        </Box>
        
        <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
          <Chip 
            label={partner.type.toUpperCase()} 
            size="small" 
            color={partner.type === 'customer' ? 'primary' : 'secondary'}
          />
          <Typography variant="body2" color="text.secondary">
            ₹{parseFloat(partner.credit_limit).toLocaleString()}
          </Typography>
        </Stack>

        {partner.workflow_stage === 'pending_approval' && canApprove && (
          <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
            <Button
              size="small"
              variant="contained"
              color="success"
              onClick={() => handleApproval('approve')}
            >
              Approve
            </Button>
            <Button
              size="small"
              variant="outlined"
              color="error"
              onClick={() => handleApproval('reject')}
            >
              Reject
            </Button>
          </Box>
        )}
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" fontWeight="bold">
          Partners
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Refresh">
            <IconButton onClick={loadPartners}>
              <Refresh />
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setOpenDialog(true)}
            sx={{ display: { xs: 'none', sm: 'flex' } }}
          >
            Add Partner
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Content */}
      {isMobile ? (
        // Mobile Card View
        <Box>
          {partners.map((partner) => (
            <MobilePartnerCard key={partner.id} partner={partner} />
          ))}
          {partners.length === 0 && (
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 4 }}>
                <Business sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  No partners found
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Create your first partner to get started
                </Typography>
              </CardContent>
            </Card>
          )}
        </Box>
      ) : (
        // Desktop DataGrid
        <Card>
          <Box sx={{ height: 600, width: '100%' }}>
            <DataGrid
              rows={partners}
              columns={columns}
              pageSize={10}
              rowsPerPageOptions={[10, 25, 50]}
              disableSelectionOnClick
              sx={{
                '& .MuiDataGrid-cell': {
                  borderBottom: `1px solid ${theme.palette.divider}`,
                },
                '& .MuiDataGrid-columnHeaders': {
                  backgroundColor: theme.palette.grey[50],
                  borderBottom: `2px solid ${theme.palette.divider}`,
                },
              }}
            />
          </Box>
        </Card>
      )}

      {/* Mobile FAB */}
      {isMobile && (
        <Fab
          color="primary"
          aria-label="add partner"
          sx={{ position: 'fixed', bottom: 80, right: 16 }}
          onClick={() => setOpenDialog(true)}
        >
          <AddIcon />
        </Fab>
      )}

      {/* Create Partner Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Partner</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Partner Name"
            fullWidth
            variant="outlined"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            select
            margin="dense"
            label="Type"
            fullWidth
            variant="outlined"
            value={formData.type}
            onChange={(e) => setFormData({ ...formData, type: e.target.value })}
            sx={{ mb: 2 }}
          >
            <MenuItem value="customer">Customer</MenuItem>
            <MenuItem value="supplier">Supplier</MenuItem>
          </TextField>
          <TextField
            margin="dense"
            label="GST Number"
            fullWidth
            variant="outlined"
            value={formData.gst_number}
            onChange={(e) => setFormData({ ...formData, gst_number: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Credit Limit"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.credit_limit}
            onChange={(e) => setFormData({ ...formData, credit_limit: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button onClick={handleCreatePartner} variant="contained">
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* Approval Dialog */}
      <Dialog open={openApprovalDialog} onClose={() => setOpenApprovalDialog(false)}>
        <DialogTitle>Review Partner</DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Partner: <strong>{selectedPartner?.name}</strong>
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Type: {selectedPartner?.type?.toUpperCase()}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Credit Limit: ₹{parseFloat(selectedPartner?.credit_limit || 0).toLocaleString()}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenApprovalDialog(false)}>Cancel</Button>
          <Button onClick={() => handleApproval('reject')} color="error">
            Reject
          </Button>
          <Button onClick={() => handleApproval('approve')} variant="contained" color="success">
            Approve
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Partners;