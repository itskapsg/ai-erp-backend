import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  Chip,
  IconButton,
  Stepper,
  Step,
  StepLabel,
  Card,
  CardContent,
  CardActions,
  Fab,
  Alert,
  CircularProgress,
  Tooltip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  InputAdornment,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction
} from '@mui/material';
import {
  DataGrid,
  GridToolbarContainer,
  GridToolbarFilterButton,
  GridToolbarExport,
  GridToolbarColumnsButton
} from '@mui/x-data-grid';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  CheckCircle as ApprovedIcon,
  Schedule as PendingIcon,
  Cancel as RejectedIcon,
  Inventory as InventoryIcon,
  ColorLens as ColorIcon,
  Style as FabricIcon,
  AttachMoney as PriceIcon,
  Close as CloseIcon
} from '@mui/icons-material';
import { productsAPI, partnersAPI } from '../services/api';

// Status chip component
const StatusChip = ({ status }) => {
  const getStatusConfig = (status) => {
    switch (status?.toLowerCase()) {
      case 'approved':
        return { color: 'success', icon: <ApprovedIcon />, label: 'Approved' };
      case 'pending_approval':
        return { color: 'warning', icon: <PendingIcon />, label: 'Pending' };
      case 'rejected':
        return { color: 'error', icon: <RejectedIcon />, label: 'Rejected' };
      case 'draft':
        return { color: 'default', icon: <EditIcon />, label: 'Draft' };
      default:
        return { color: 'default', icon: null, label: status || 'Unknown' };
    }
  };

  const config = getStatusConfig(status);
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

// Attribute chip component for variants
const AttributeChip = ({ attribute, value, onDelete }) => {
  const getAttributeIcon = (attr) => {
    switch (attr.toLowerCase()) {
      case 'color':
        return <ColorIcon />;
      case 'fabric':
        return <FabricIcon />;
      default:
        return null;
    }
  };

  return (
    <Chip
      icon={getAttributeIcon(attribute)}
      label={`${attribute}: ${value}`}
      onDelete={onDelete}
      size="small"
      variant="outlined"
      sx={{ m: 0.5 }}
    />
  );
};

// Custom toolbar for DataGrid
const CustomToolbar = ({ onCreateProduct }) => {
  return (
    <GridToolbarContainer>
      <Button
        startIcon={<AddIcon />}
        onClick={onCreateProduct}
        variant="contained"
        size="small"
        sx={{ mr: 1 }}
      >
        Create Product
      </Button>
      <GridToolbarFilterButton />
      <GridToolbarColumnsButton />
      <GridToolbarExport />
    </GridToolbarContainer>
  );
};

// Variant builder component
const VariantBuilder = ({ variants, onVariantsChange }) => {
  const [newVariant, setNewVariant] = useState({
    attributes: {},
    price_adjustment: 0,
    stock_quantity: 0
  });
  const [attributeKey, setAttributeKey] = useState('');
  const [attributeValue, setAttributeValue] = useState('');

  const addAttribute = () => {
    if (attributeKey && attributeValue) {
      setNewVariant(prev => ({
        ...prev,
        attributes: {
          ...prev.attributes,
          [attributeKey]: attributeValue
        }
      }));
      setAttributeKey('');
      setAttributeValue('');
    }
  };

  const removeAttribute = (key) => {
    setNewVariant(prev => {
      const newAttributes = { ...prev.attributes };
      delete newAttributes[key];
      return {
        ...prev,
        attributes: newAttributes
      };
    });
  };

  const addVariant = () => {
    if (Object.keys(newVariant.attributes).length > 0) {
      onVariantsChange([...variants, { ...newVariant, id: Date.now() }]);
      setNewVariant({
        attributes: {},
        price_adjustment: 0,
        stock_quantity: 0
      });
    }
  };

  const removeVariant = (id) => {
    onVariantsChange(variants.filter(v => v.id !== id));
  };

  const commonAttributes = [
    'Color', 'Fabric', 'Size', 'Gold_Work', 'Border', 'Length', 'Pattern', 'Design'
  ];

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Product Variants
      </Typography>

      {/* Add new variant */}
      <Card variant="outlined" sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle1" gutterBottom>
            Add New Variant
          </Typography>

          {/* Attributes */}
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Attributes
            </Typography>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} sm={4}>
                <FormControl fullWidth size="small">
                  <InputLabel>Attribute</InputLabel>
                  <Select
                    value={attributeKey}
                    onChange={(e) => setAttributeKey(e.target.value)}
                    label="Attribute"
                  >
                    {commonAttributes.map(attr => (
                      <MenuItem key={attr} value={attr}>{attr}</MenuItem>
                    ))}
                    <MenuItem value="custom">Custom...</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              {attributeKey === 'custom' && (
                <Grid item xs={12} sm={3}>
                  <TextField
                    size="small"
                    fullWidth
                    label="Custom Attribute"
                    value={attributeKey}
                    onChange={(e) => setAttributeKey(e.target.value)}
                  />
                </Grid>
              )}
              <Grid item xs={12} sm={4}>
                <TextField
                  size="small"
                  fullWidth
                  label="Value"
                  value={attributeValue}
                  onChange={(e) => setAttributeValue(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addAttribute()}
                />
              </Grid>
              <Grid item xs={12} sm={2}>
                <Button
                  variant="outlined"
                  onClick={addAttribute}
                  disabled={!attributeKey || !attributeValue}
                  fullWidth
                >
                  Add
                </Button>
              </Grid>
            </Grid>

            {/* Current attributes */}
            <Box sx={{ mt: 1 }}>
              {Object.entries(newVariant.attributes).map(([key, value]) => (
                <AttributeChip
                  key={key}
                  attribute={key}
                  value={value}
                  onDelete={() => removeAttribute(key)}
                />
              ))}
            </Box>
          </Box>

          {/* Price and stock */}
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                size="small"
                fullWidth
                label="Price Adjustment"
                type="number"
                value={newVariant.price_adjustment}
                onChange={(e) => setNewVariant(prev => ({
                  ...prev,
                  price_adjustment: parseFloat(e.target.value) || 0
                }))}
                InputProps={{
                  startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                }}
                helperText="Positive for premium, negative for discount"
              />
            </Grid>
          </Grid>

        </CardContent>
        <CardActions>
          <Button
            variant="contained"
            onClick={addVariant}
            disabled={Object.keys(newVariant.attributes).length === 0}
            startIcon={<AddIcon />}
          >
            Add Variant
          </Button>
        </CardActions>
      </Card>

      {/* Existing variants */}
      {
        variants.length > 0 && (
          <Box>
            <Typography variant="subtitle1" gutterBottom>
              Variants ({variants.length})
            </Typography>
            <List>
              {variants.map((variant, index) => (
                <ListItem key={variant.id || index} divider>
                  <ListItemText
                    primary={
                      <Box>
                        {Object.entries(variant.attributes).map(([key, value]) => (
                          <Chip
                            key={key}
                            label={`${key}: ${value}`}
                            size="small"
                            sx={{ mr: 0.5, mb: 0.5 }}
                          />
                        ))}
                      </Box>
                    }
                    secondary={
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="body2" component="span">
                          Price Adj: ₹{variant.price_adjustment}
                        </Typography>
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    <IconButton
                      edge="end"
                      onClick={() => removeVariant(variant.id)}
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          </Box>
        )
      }
    </Box >
  );
};

// Main Products component
const Products = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [productForm, setProductForm] = useState({
    name: "",
    description: "",
    base_price: "",
    category: "",
    seller_id: "",
    design_number: "",
    quality: ""
  });
  const [suppliers, setSuppliers] = useState([]);
  const [variants, setVariants] = useState([]);
  const [submitting, setSubmitting] = useState(false);

  const steps = ['Basic Information', 'Product Variants', 'Review & Submit'];

  // Load products
  const loadProducts = async () => {
    try {
      setLoading(true);
      const data = await productsAPI.fetchProducts({ include_variants: false });
      setProducts(data);
      setError(null);
    } catch (err) {
      console.error('Error loading products:', err);
      setError('Failed to load products');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
  }, []);

  // DataGrid columns
  const columns = [
    {
      field: 'name',
      headerName: 'Product / Design',
      flex: 1,
      minWidth: 200,
      renderCell: (params) => (
        <Box>
          <Typography variant="body2" fontWeight="bold">{params.value}</Typography>
          {params.row.design_number && (
            <Typography variant="caption" color="text.secondary">
              Design: {params.row.design_number}
            </Typography>
          )}
        </Box>
      )
    },
    {
      field: 'quality',
      headerName: 'Quality',
      width: 150,
    },
    {
      field: 'category',
      headerName: 'Category',
      width: 120,
    },
    {
      field: 'base_price',
      headerName: 'Base Price',
      width: 120,
      renderCell: (params) => `₹${params.value}`,
    },
    {
      field: 'variant_count',
      headerName: 'Variants',
      width: 100,
      renderCell: (params) => (
        <Chip
          label={params.value || 0}
          size="small"
          color={params.value > 0 ? 'primary' : 'default'}
        />
      ),
    },
    {
      field: 'workflow_stage',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => <StatusChip status={params.value} />,
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 120,
      sortable: false,
      renderCell: (params) => (
        <Box>
          <Tooltip title="View Details">
            <IconButton size="small" onClick={() => handleViewProduct(params.row.id)}>
              <ViewIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Edit">
            <IconButton size="small" onClick={() => handleEditProduct(params.row.id)}>
              <EditIcon />
            </IconButton>
          </Tooltip>
        </Box>
      ),
    },
  ];

  // Handle product creation
  const handleCreateProduct = () => {
    setCreateDialogOpen(true);
    setActiveStep(0);
    setProductForm({
      name: '',
      description: '',
      base_price: '',
      category: '',
      seller_id: '',
      design_number: '',
      quality: ''
    });
    setVariants([]);
    loadSuppliers();
  };

  const loadSuppliers = async () => {
    try {
      const data = await partnersAPI.fetchPartners('supplier');
      setSuppliers(data);
    } catch (err) {
      console.error("Failed to load suppliers");
    }
  };

  const handleCloseDialog = () => {
    setCreateDialogOpen(false);
    setActiveStep(0);
  };

  const handleNext = () => {
    setActiveStep((prevStep) => prevStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  const handleSubmit = async () => {
    try {
      setSubmitting(true);

      // Create the product
      const productData = {
        ...productForm,
        base_price: parseFloat(productForm.base_price)
      };

      const createdProduct = await productsAPI.createProduct(productData);

      // Add variants if any
      for (const variant of variants) {
        await productsAPI.addVariant(createdProduct.id, {
          attributes: variant.attributes,
          price_adjustment: variant.price_adjustment,
          stock_quantity: 0 // Agency: No stock tracking
        });
      }

      // Refresh products list
      await loadProducts();

      // Close dialog
      handleCloseDialog();

      setError(null);
    } catch (err) {
      console.error('Error creating product:', err);
      setError('Failed to create product: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSubmitting(false);
    }
  };

  const handleViewProduct = (id) => {
    // TODO: Implement product detail view
    console.log('View product:', id);
  };

  const handleEditProduct = (id) => {
    // TODO: Implement product editing
    console.log('Edit product:', id);
  };

  // Form validation
  const isStepValid = (step) => {
    switch (step) {
      case 0:
        return productForm.name && productForm.base_price && productForm.category && productForm.seller_id;
      case 1:
        return true; // Variants are optional
      case 2:
        return true;
      default:
        return false;
    }
  };

  // Render step content
  const renderStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Product Name"
                value={productForm.name}
                onChange={(e) => setProductForm(prev => ({ ...prev, name: e.target.value }))}
                placeholder="e.g., Banarasi Saree Design 101"
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                multiline
                rows={3}
                value={productForm.description}
                onChange={(e) => setProductForm(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Detailed product description..."
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Base Price"
                type="number"
                value={productForm.base_price}
                onChange={(e) => setProductForm(prev => ({ ...prev, base_price: e.target.value }))}
                InputProps={{
                  startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                }}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth required>
                <InputLabel>Category</InputLabel>
                <Select
                  value={productForm.category}
                  onChange={(e) => setProductForm(prev => ({ ...prev, category: e.target.value }))}
                  label="Category"
                >
                  <MenuItem value="Sarees">Sarees</MenuItem>
                  <MenuItem value="Suits">Suits</MenuItem>
                  <MenuItem value="Lehengas">Lehengas</MenuItem>
                  <MenuItem value="Fabrics">Fabrics</MenuItem>
                  <MenuItem value="Accessories">Accessories</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth required>
                <InputLabel>Supplier</InputLabel>
                <Select
                  value={productForm.seller_id}
                  onChange={(e) => setProductForm(prev => ({ ...prev, seller_id: e.target.value }))}
                  label="Supplier"
                >
                  {suppliers.map(s => (
                    <MenuItem key={s.id} value={s.id}>{s.name}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Design Number"
                value={productForm.design_number}
                onChange={(e) => setProductForm(prev => ({ ...prev, design_number: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Fabric Quality"
                value={productForm.quality}
                onChange={(e) => setProductForm(prev => ({ ...prev, quality: e.target.value }))}
                placeholder="e.g. 60Gs Cotton"
              />
            </Grid>
          </Grid >
        );

      case 1:
        return (
          <VariantBuilder
            variants={variants}
            onVariantsChange={setVariants}
          />
        );

      case 2:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Review Product Details
            </Typography>

            <Card variant="outlined" sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>
                  Basic Information
                </Typography>
                <Typography><strong>Name:</strong> {productForm.name}</Typography>
                <Typography><strong>Design:</strong> {productForm.design_number}</Typography>
                <Typography><strong>Quality:</strong> {productForm.quality}</Typography>
                <Typography><strong>Category:</strong> {productForm.category}</Typography>
                <Typography><strong>Base Price:</strong> ₹{productForm.base_price}</Typography>
                {productForm.description && (
                  <Typography><strong>Description:</strong> {productForm.description}</Typography>
                )}
              </CardContent>
            </Card>

            {variants.length > 0 && (
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>
                    Variants ({variants.length})
                  </Typography>
                  {variants.map((variant, index) => (
                    <Box key={index} sx={{ mb: 1, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                      <Box sx={{ mb: 1 }}>
                        {Object.entries(variant.attributes).map(([key, value]) => (
                          <Chip
                            key={key}
                            label={`${key}: ${value}`}
                            size="small"
                            sx={{ mr: 0.5 }}
                          />
                        ))}
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        Price Adjustment: ₹{variant.price_adjustment} | Stock: {variant.stock_quantity}
                      </Typography>
                    </Box>
                  ))}
                </CardContent>
              </Card>
            )}
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Products
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreateProduct}
          size="large"
        >
          Create Product
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Paper sx={{ height: 600, width: '100%' }}>
        <DataGrid
          rows={products}
          columns={columns}
          loading={loading}
          pageSize={25}
          rowsPerPageOptions={[25, 50, 100]}
          disableSelectionOnClick
          components={{
            Toolbar: () => <CustomToolbar onCreateProduct={handleCreateProduct} />,
          }}
          sx={{
            '& .MuiDataGrid-cell:focus': {
              outline: 'none',
            },
          }}
        />
      </Paper>

      {/* Create Product Dialog */}
      <Dialog
        open={createDialogOpen}
        onClose={handleCloseDialog}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: { minHeight: '70vh' }
        }}
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            Create New Product
            <IconButton onClick={handleCloseDialog}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>

        <DialogContent>
          <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

          {renderStepContent(activeStep)}
        </DialogContent>

        <DialogActions sx={{ p: 2 }}>
          <Button
            disabled={activeStep === 0}
            onClick={handleBack}
          >
            Back
          </Button>
          <Box sx={{ flex: '1 1 auto' }} />
          {activeStep === steps.length - 1 ? (
            <Button
              variant="contained"
              onClick={handleSubmit}
              disabled={submitting || !isStepValid(activeStep)}
              startIcon={submitting ? <CircularProgress size={20} /> : <AddIcon />}
            >
              {submitting ? 'Creating...' : 'Create Product'}
            </Button>
          ) : (
            <Button
              variant="contained"
              onClick={handleNext}
              disabled={!isStepValid(activeStep)}
            >
              Next
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Products;