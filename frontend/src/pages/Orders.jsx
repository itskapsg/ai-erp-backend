/**
 * Orders Page - Agency Order Management with Credit Limit Approval
 * 
 * Features:
 * - Order List with status color coding
 * - Multi-step Order Creation Wizard
 * - Shopping Cart functionality
 * - Credit limit validation with approval workflow
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Stepper,
  Step,
  StepLabel,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Chip,
  Alert,
  IconButton,
  Card,
  CardContent,
  Grid,
  Divider,
  CircularProgress,
  Tooltip
} from '@mui/material';
import {
  Add as AddIcon,
  ShoppingCart as CartIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  Pending as PendingIcon,
  Cancel as CancelIcon,
  Person as PersonIcon,
  Store as StoreIcon,
  Inventory as InventoryIcon,
  PictureAsPdf as PdfIcon,
  Download as DownloadIcon
} from '@mui/icons-material';
import { ordersAPI, partnersAPI, productsAPI } from '../services/api';

const Orders = () => {
  // State management
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  
  // Form data
  const [selectedBuyer, setSelectedBuyer] = useState('');
  const [selectedSeller, setSelectedSeller] = useState('');
  const [selectedProduct, setSelectedProduct] = useState('');
  const [selectedVariant, setSelectedVariant] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [cart, setCart] = useState([]);
  
  // Dropdown data
  const [buyers, setBuyers] = useState([]);
  const [sellers, setSellers] = useState([]);
  const [products, setProducts] = useState([]);
  const [variants, setVariants] = useState([]);
  
  // Loading states
  const [loadingBuyers, setLoadingBuyers] = useState(false);
  const [loadingSellers, setLoadingSellers] = useState(false);
  const [loadingProducts, setLoadingProducts] = useState(false);
  
  // Result state
  const [orderResult, setOrderResult] = useState(null);

  const steps = ['Select Parties', 'Add Items', 'Review & Submit'];

  // Load orders on component mount
  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    try {
      setLoading(true);
      const data = await ordersAPI.fetchOrders();
      setOrders(data);
    } catch (err) {
      setError('Failed to load orders');
      console.error('Error loading orders:', err);
    } finally {
      setLoading(false);
    }
  };

  // Load dropdown data when dialog opens
  const loadDropdownData = async () => {
    try {
      // Load buyers (customers)
      setLoadingBuyers(true);
      const buyersData = await partnersAPI.fetchPartners('CUSTOMER');
      setBuyers(buyersData.filter(p => p.workflow_stage === 'approved'));
      setLoadingBuyers(false);

      // Load sellers (suppliers)
      setLoadingSellers(true);
      const sellersData = await partnersAPI.fetchPartners('SUPPLIER');
      setSellers(sellersData.filter(p => p.workflow_stage === 'approved'));
      setLoadingSellers(false);

      // Load products
      setLoadingProducts(true);
      const productsData = await productsAPI.fetchProducts({ include_variants: true });
      setProducts(productsData.filter(p => p.workflow_stage === 'approved'));
      setLoadingProducts(false);
    } catch (err) {
      console.error('Error loading dropdown data:', err);
    }
  };

  // Handle product selection to load variants
  const handleProductChange = (productId) => {
    setSelectedProduct(productId);
    setSelectedVariant('');
    
    const product = products.find(p => p.id === productId);
    if (product && product.variants) {
      setVariants(product.variants);
    } else {
      setVariants([]);
    }
  };

  // Add item to cart
  const addToCart = () => {
    if (!selectedProduct || !selectedVariant || quantity <= 0) {
      return;
    }

    const product = products.find(p => p.id === selectedProduct);
    const variant = variants.find(v => v.id === selectedVariant);
    
    if (!product || !variant) return;

    const cartItem = {
      id: `${selectedVariant}-${Date.now()}`,
      product_id: selectedProduct,
      variant_id: selectedVariant,
      product_name: product.name,
      variant_sku: variant.sku,
      variant_attributes: variant.attributes,
      quantity: parseInt(quantity),
      price: parseFloat(variant.final_price),
      line_total: parseInt(quantity) * parseFloat(variant.final_price)
    };

    setCart([...cart, cartItem]);
    
    // Reset form
    setSelectedProduct('');
    setSelectedVariant('');
    setQuantity(1);
    setVariants([]);
  };

  // Remove item from cart
  const removeFromCart = (itemId) => {
    setCart(cart.filter(item => item.id !== itemId));
  };

  // Calculate cart total
  const getCartTotal = () => {
    return cart.reduce((total, item) => total + item.line_total, 0);
  };

  // Handle dialog open
  const handleDialogOpen = () => {
    setDialogOpen(true);
    setActiveStep(0);
    resetForm();
    loadDropdownData();
  };

  // Handle dialog close
  const handleDialogClose = () => {
    setDialogOpen(false);
    resetForm();
    setOrderResult(null);
  };

  // Reset form
  const resetForm = () => {
    setSelectedBuyer('');
    setSelectedSeller('');
    setSelectedProduct('');
    setSelectedVariant('');
    setQuantity(1);
    setCart([]);
    setVariants([]);
  };

  // Handle next step
  const handleNext = () => {
    setActiveStep((prevStep) => prevStep + 1);
  };

  // Handle back step
  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  // Submit order
  const handleSubmit = async () => {
    if (!selectedBuyer || !selectedSeller || cart.length === 0) {
      return;
    }

    try {
      setSubmitting(true);
      
      const orderData = {
        buyer_id: selectedBuyer,
        seller_id: selectedSeller,
        items: cart.map(item => ({
          variant_id: item.variant_id,
          quantity: item.quantity
        }))
      };

      const result = await ordersAPI.createOrder(orderData);
      setOrderResult(result);
      
      // Reload orders list
      await loadOrders();
      
      // Move to final step to show result
      setActiveStep(3);
      
    } catch (err) {
      console.error('Error creating order:', err);
      setError('Failed to create order');
    } finally {
      setSubmitting(false);
    }
  };

  // Get status color and icon
  const getStatusDisplay = (status, workflowStage) => {
    if (workflowStage === 'pending_approval') {
      return {
        color: 'warning',
        icon: <PendingIcon />,
        label: 'Pending Approval'
      };
    }
    
    switch (status) {
      case 'confirmed':
        return {
          color: 'success',
          icon: <CheckCircleIcon />,
          label: 'Confirmed'
        };
      case 'cancelled':
        return {
          color: 'error',
          icon: <CancelIcon />,
          label: 'Cancelled'
        };
      case 'draft':
        return {
          color: 'default',
          icon: <PendingIcon />,
          label: 'Draft'
        };
      default:
        return {
          color: 'default',
          icon: <PendingIcon />,
          label: status
        };
    }
  };

  // Format currency
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR'
    }).format(amount);
  };

  // Handle PDF download
  const handleDownloadPDF = async (orderId, orderNumber) => {
    try {
      const pdfBlob = await ordersAPI.downloadPDF(orderId);
      
      // Create download link
      const url = window.URL.createObjectURL(pdfBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `Order_${orderNumber}.pdf`;
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error downloading PDF:', err);
      setError('Failed to download PDF');
    }
  };

  // Render step content
  const renderStepContent = (step) => {
    switch (step) {
      case 0: // Party Selection
        return (
          <Box sx={{ minHeight: 200 }}>
            <Typography variant="h6" gutterBottom>
              <PersonIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              Select Buyer and Seller
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Select Buyer (Customer)</InputLabel>
                  <Select
                    value={selectedBuyer}
                    onChange={(e) => setSelectedBuyer(e.target.value)}
                    disabled={loadingBuyers}
                  >
                    {buyers.map((buyer) => (
                      <MenuItem key={buyer.id} value={buyer.id}>
                        {buyer.name} - {formatCurrency(buyer.credit_limit)} Credit
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Select Seller (Supplier)</InputLabel>
                  <Select
                    value={selectedSeller}
                    onChange={(e) => setSelectedSeller(e.target.value)}
                    disabled={loadingSellers}
                  >
                    {sellers.map((seller) => (
                      <MenuItem key={seller.id} value={seller.id}>
                        {seller.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Box>
        );

      case 1: // Add Items
        return (
          <Box sx={{ minHeight: 400 }}>
            <Typography variant="h6" gutterBottom>
              <InventoryIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              Add Items to Cart
            </Typography>
            
            {/* Add Item Form */}
            <Paper sx={{ p: 2, mb: 3 }}>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} md={4}>
                  <FormControl fullWidth>
                    <InputLabel>Select Product</InputLabel>
                    <Select
                      value={selectedProduct}
                      onChange={(e) => handleProductChange(e.target.value)}
                      disabled={loadingProducts}
                    >
                      {products.map((product) => (
                        <MenuItem key={product.id} value={product.id}>
                          {product.name} - {formatCurrency(product.base_price)}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12} md={3}>
                  <FormControl fullWidth>
                    <InputLabel>Select Variant</InputLabel>
                    <Select
                      value={selectedVariant}
                      onChange={(e) => setSelectedVariant(e.target.value)}
                      disabled={!selectedProduct || variants.length === 0}
                    >
                      {variants.map((variant) => (
                        <MenuItem key={variant.id} value={variant.id}>
                          {variant.sku} - {formatCurrency(variant.final_price)}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12} md={2}>
                  <TextField
                    fullWidth
                    label="Quantity"
                    type="number"
                    value={quantity}
                    onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                    inputProps={{ min: 1 }}
                  />
                </Grid>
                
                <Grid item xs={12} md={3}>
                  <Button
                    fullWidth
                    variant="contained"
                    onClick={addToCart}
                    disabled={!selectedProduct || !selectedVariant || quantity <= 0}
                    startIcon={<AddIcon />}
                  >
                    Add to Cart
                  </Button>
                </Grid>
              </Grid>
            </Paper>

            {/* Cart Display */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <CartIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Shopping Cart ({cart.length} items)
                </Typography>
                
                {cart.length === 0 ? (
                  <Typography color="text.secondary">
                    No items in cart. Add some products above.
                  </Typography>
                ) : (
                  <>
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Product</TableCell>
                            <TableCell>Variant</TableCell>
                            <TableCell align="right">Qty</TableCell>
                            <TableCell align="right">Price</TableCell>
                            <TableCell align="right">Total</TableCell>
                            <TableCell align="center">Action</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {cart.map((item) => (
                            <TableRow key={item.id}>
                              <TableCell>{item.product_name}</TableCell>
                              <TableCell>
                                <Tooltip title={JSON.stringify(item.variant_attributes, null, 2)}>
                                  <span>{item.variant_sku}</span>
                                </Tooltip>
                              </TableCell>
                              <TableCell align="right">{item.quantity}</TableCell>
                              <TableCell align="right">{formatCurrency(item.price)}</TableCell>
                              <TableCell align="right">{formatCurrency(item.line_total)}</TableCell>
                              <TableCell align="center">
                                <IconButton
                                  size="small"
                                  color="error"
                                  onClick={() => removeFromCart(item.id)}
                                >
                                  <DeleteIcon />
                                </IconButton>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                    
                    <Divider sx={{ my: 2 }} />
                    
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="h6">
                        Running Total:
                      </Typography>
                      <Typography variant="h5" color="primary">
                        {formatCurrency(getCartTotal())}
                      </Typography>
                    </Box>
                  </>
                )}
              </CardContent>
            </Card>
          </Box>
        );

      case 2: // Review & Submit
        const buyer = buyers.find(b => b.id === selectedBuyer);
        const seller = sellers.find(s => s.id === selectedSeller);
        
        return (
          <Box sx={{ minHeight: 300 }}>
            <Typography variant="h6" gutterBottom>
              Review Order Details
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom>
                      <PersonIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                      Buyer Details
                    </Typography>
                    <Typography><strong>Name:</strong> {buyer?.name}</Typography>
                    <Typography><strong>Credit Limit:</strong> {formatCurrency(buyer?.credit_limit || 0)}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom>
                      <StoreIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                      Seller Details
                    </Typography>
                    <Typography><strong>Name:</strong> {seller?.name}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom>
                      Order Summary
                    </Typography>
                    <Typography><strong>Items:</strong> {cart.length}</Typography>
                    <Typography><strong>Total Amount:</strong> {formatCurrency(getCartTotal())}</Typography>
                    
                    {buyer && getCartTotal() > buyer.credit_limit && (
                      <Alert severity="warning" sx={{ mt: 2 }}>
                        <strong>Credit Limit Warning:</strong> Order total ({formatCurrency(getCartTotal())}) 
                        exceeds buyer's credit limit ({formatCurrency(buyer.credit_limit)}). 
                        This order will require approval.
                      </Alert>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        );

      case 3: // Result
        return (
          <Box sx={{ minHeight: 200, textAlign: 'center' }}>
            {orderResult && (
              <>
                {orderResult.status === 'confirmed' ? (
                  <Alert severity="success" sx={{ mb: 2 }}>
                    <Typography variant="h6">Order Created Successfully!</Typography>
                    <Typography>
                      Order #{orderResult.order_number} has been confirmed and is ready for processing.
                    </Typography>
                  </Alert>
                ) : orderResult.workflow_stage === 'pending_approval' ? (
                  <Alert severity="warning" sx={{ mb: 2 }}>
                    <Typography variant="h6">Order Requires Approval</Typography>
                    <Typography>
                      Order #{orderResult.order_number} exceeds credit limit and has been sent for approval.
                    </Typography>
                    {orderResult.rejection_reason && (
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        <strong>Reason:</strong> {orderResult.rejection_reason}
                      </Typography>
                    )}
                  </Alert>
                ) : (
                  <Alert severity="info" sx={{ mb: 2 }}>
                    <Typography variant="h6">Order Created</Typography>
                    <Typography>
                      Order #{orderResult.order_number} has been created with status: {orderResult.status}
                    </Typography>
                  </Alert>
                )}
                
                <Typography variant="body1">
                  <strong>Order Number:</strong> {orderResult.order_number}<br />
                  <strong>Total Amount:</strong> {formatCurrency(orderResult.total_amount)}<br />
                  <strong>Status:</strong> {orderResult.status}<br />
                  <strong>Workflow Stage:</strong> {orderResult.workflow_stage}
                </Typography>
              </>
            )}
          </Box>
        );

      default:
        return null;
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Order Management
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Orders List */}
      <Paper sx={{ mb: 3 }}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Order #</TableCell>
                <TableCell>Buyer</TableCell>
                <TableCell>Seller</TableCell>
                <TableCell align="right">Total Amount</TableCell>
                <TableCell align="center">Status</TableCell>
                <TableCell>Created</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {orders.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography color="text.secondary">
                      No orders found. Create your first order!
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                orders.map((order) => {
                  const statusDisplay = getStatusDisplay(order.status, order.workflow_stage);
                  return (
                    <TableRow key={order.id}>
                      <TableCell>
                        <Typography variant="body2" fontWeight="bold">
                          {order.order_number}
                        </Typography>
                      </TableCell>
                      <TableCell>{order.buyer_name}</TableCell>
                      <TableCell>{order.seller_name}</TableCell>
                      <TableCell align="right">
                        {formatCurrency(order.total_amount)}
                      </TableCell>
                      <TableCell align="center">
                        <Chip
                          icon={statusDisplay.icon}
                          label={statusDisplay.label}
                          color={statusDisplay.color}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {new Date(order.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip title="Download PDF">
                          <IconButton
                            size="small"
                            color="primary"
                            onClick={() => handleDownloadPDF(order.id, order.order_number)}
                          >
                            <PdfIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Floating Action Button */}
      <Fab
        color="primary"
        aria-label="add order"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={handleDialogOpen}
      >
        <AddIcon />
      </Fab>

      {/* Order Creation Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={handleDialogClose}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: { minHeight: 600 }
        }}
      >
        <DialogTitle>
          Create New Order
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
        
        <DialogActions>
          <Button onClick={handleDialogClose}>
            Cancel
          </Button>
          
          {activeStep > 0 && activeStep < 3 && (
            <Button onClick={handleBack}>
              Back
            </Button>
          )}
          
          {activeStep === 0 && (
            <Button
              onClick={handleNext}
              variant="contained"
              disabled={!selectedBuyer || !selectedSeller}
            >
              Next
            </Button>
          )}
          
          {activeStep === 1 && (
            <Button
              onClick={handleNext}
              variant="contained"
              disabled={cart.length === 0}
            >
              Review Order
            </Button>
          )}
          
          {activeStep === 2 && (
            <Button
              onClick={handleSubmit}
              variant="contained"
              disabled={submitting}
              startIcon={submitting ? <CircularProgress size={20} /> : null}
            >
              {submitting ? 'Creating...' : 'Create Order'}
            </Button>
          )}
          
          {activeStep === 3 && (
            <Button
              onClick={handleDialogClose}
              variant="contained"
              color="success"
            >
              Done
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Orders;