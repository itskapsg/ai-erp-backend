
import React, { useState, useMemo } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useForm, Controller } from 'react-hook-form';
import {
    Box, Grid, TextField, MenuItem, Typography, Button, Paper,
    Dialog, DialogTitle, DialogContent, DialogActions,
    Table, TableBody, TableCell, TableHead, TableRow,
    Alert, AlertTitle, Chip, Stack
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { DataService } from '@/services/dataService';
import { Partner, Product, ProductVariant } from '@/types';

// Types
type CartItem = {
    variantId: string;
    productId: string;
    designNumber: string;
    sku: string; // Variant SKU or Attrs
    price: number;
    quantity: number;
};

export default function OrderEntry() {
    // --- Form State ---
    const { control, watch, handleSubmit, formState: { errors } } = useForm({
        defaultValues: {
            sellerId: '',
            buyerId: ''
        }
    });

    const selectedSellerId = watch('sellerId');
    const selectedBuyerId = watch('buyerId');

    // --- Queries ---
    const { data: customers = [] } = useQuery({
        queryKey: ['partners', 'CUSTOMER'],
        queryFn: () => DataService.getPartners('CUSTOMER')
    });

    const { data: suppliers = [] } = useQuery({
        queryKey: ['partners', 'SUPPLIER'],
        queryFn: () => DataService.getPartners('SUPPLIER')
    });

    const { data: products = [], isFetching: isProductsLoading } = useQuery({
        queryKey: ['products', selectedSellerId],
        queryFn: () => DataService.getProducts(selectedSellerId),
        enabled: !!selectedSellerId
    });

    // --- Local State ---
    const [cart, setCart] = useState<CartItem[]>([]);
    const [variantDialogOpen, setVariantDialogOpen] = useState(false);
    const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
    const [qtyInputs, setQtyInputs] = useState<Record<string, number>>({}); // variantId -> qty

    // --- Actions ---
    const handleOpenVariants = (product: Product) => {
        setSelectedProduct(product);
        setQtyInputs({});
        setVariantDialogOpen(true);
    };

    const handleAddToCart = () => {
        if (!selectedProduct) return;

        const newItems: CartItem[] = [];
        Object.entries(qtyInputs).forEach(([variantId, qty]) => {
            if (qty > 0) {
                const variant = selectedProduct.variants.find(v => v.id === variantId);
                if (variant) {
                    const price = selectedProduct.base_price + (variant.price_adjustment || 0);
                    // Format Attrs
                    const attrs = Object.entries(variant.attributes).map(([k, v]) => `${k}:${v}`).join(', ');

                    newItems.push({
                        variantId: variant.id,
                        productId: selectedProduct.id,
                        designNumber: selectedProduct.design_number,
                        sku: attrs || 'Default',
                        price,
                        quantity: qty
                    });
                }
            }
        });

        setCart(prev => [...prev, ...newItems]);
        setVariantDialogOpen(false);
    };

    const createOrderMutation = useMutation({
        mutationFn: DataService.createOrder,
        onSuccess: (data) => {
            alert(`Order Created! Number: ${data.order_number}`);
            setCart([]);
            // Reset form?
        },
        onError: (err: any) => {
            alert(`Error: ${err.detail || 'Failed'}`);
        }
    });

    const onSubmit = () => {
        if (cart.length === 0) return alert("Cart is empty");

        const payload = {
            buyer_id: selectedBuyerId,
            seller_id: selectedSellerId,
            items: cart.map(item => ({
                variant_id: item.variantId,
                quantity: item.quantity
            }))
        };

        createOrderMutation.mutate(payload);
    };

    // --- Calculations ---
    const selectedBuyer = customers.find(c => c.id === selectedBuyerId);
    const cartTotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const isOverLimit = selectedBuyer ? (selectedBuyer.outstanding_balance + cartTotal) > selectedBuyer.credit_limit : false;


    // --- Grid Config ---
    const productColumns: GridColDef[] = [
        {
            field: 'design_number', headerName: 'Design Number', width: 150,
            renderCell: (params) => <strong>{params.value}</strong>
        },
        { field: 'name', headerName: 'Product Name', width: 200 },
        { field: 'category', headerName: 'Category', width: 120 },
        { field: 'base_price', headerName: 'Base Price', width: 120, type: 'number' },
        {
            field: 'actions', headerName: 'Actions', width: 150,
            renderCell: (params) => (
                <Button size="small" variant="outlined" onClick={() => handleOpenVariants(params.row)}>
                    Select Variants
                </Button>
            )
        }
    ];

    return (
        <Box>
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                Salesman Order Entry
            </Typography>

            {/* Header Form */}
            <Paper sx={{ p: 2, mb: 2 }}>
                <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                        <Controller
                            name="sellerId"
                            control={control}
                            render={({ field }) => (
                                <TextField {...field} select label="Select Supplier" fullWidth>
                                    {suppliers.map((s) => (
                                        <MenuItem key={s.id} value={s.id}>{s.name}</MenuItem>
                                    ))}
                                </TextField>
                            )}
                        />
                    </Grid>
                    <Grid item xs={12} md={6}>
                        <Controller
                            name="buyerId"
                            control={control}
                            render={({ field }) => (
                                <TextField {...field} select label="Select Customer" fullWidth>
                                    {customers.map((c) => (
                                        <MenuItem key={c.id} value={c.id}>
                                            {c.name} (Limit: {c.credit_limit} | Bal: {c.outstanding_balance})
                                        </MenuItem>
                                    ))}
                                </TextField>
                            )}
                        />
                    </Grid>
                </Grid>
            </Paper>

            {/* Main Content Area */}
            <Grid container spacing={2}>
                {/* Left: Product Catalog */}
                <Grid item xs={12} md={8}>
                    <Paper sx={{ height: 600, width: '100%' }}>
                        <DataGrid
                            rows={products}
                            columns={productColumns}
                            loading={isProductsLoading}
                            rowHeight={40}
                            disableRowSelectionOnClick
                        />
                    </Paper>
                </Grid>

                {/* Right: Cart & Summary */}
                <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
                        <Typography variant="h6" gutterBottom>Cart ({cart.length} Items)</Typography>

                        <Box sx={{ flexGrow: 1, overflow: 'auto', mb: 2 }}>
                            {cart.map((item, idx) => (
                                <Box key={idx} sx={{ display: 'flex', justifyContent: 'space-between', mb: 1, borderBottom: '1px dashed #eee', pb: 1 }}>
                                    <Box>
                                        <Typography variant="body2" fontWeight="bold">{item.designNumber}</Typography>
                                        <Typography variant="caption" color="text.secondary">{item.sku}</Typography>
                                    </Box>
                                    <Box textAlign="right">
                                        <Typography variant="body2">{item.quantity} x {item.price}</Typography>
                                        <Typography variant="body2" fontWeight="bold">{(item.quantity * item.price).toFixed(2)}</Typography>
                                    </Box>
                                </Box>
                            ))}
                        </Box>

                        <Box sx={{ borderTop: '1px solid #ddd', pt: 2 }}>
                            <Stack direction="row" justifyContent="space-between">
                                <Typography>Total:</Typography>
                                <Typography fontWeight="bold">{cartTotal.toFixed(2)}</Typography>
                            </Stack>
                            {selectedBuyer && (
                                <Stack direction="row" justifyContent="space-between" sx={{ mt: 1 }}>
                                    <Typography variant="caption">Credit Limit:</Typography>
                                    <Typography variant="caption">{selectedBuyer.credit_limit}</Typography>
                                </Stack>
                            )}

                            {isOverLimit && (
                                <Alert severity="warning" sx={{ mt: 2 }}>
                                    <AlertTitle>Credit Limit Exceeded</AlertTitle>
                                    Order will need Approval.
                                </Alert>
                            )}

                            <Button
                                variant="contained"
                                fullWidth
                                size="large"
                                sx={{ mt: 2 }}
                                disabled={cart.length === 0 || !selectedBuyerId}
                                onClick={onSubmit}
                            >
                                {isOverLimit ? 'Submit for Approval' : 'Submit Order'}
                            </Button>
                        </Box>
                    </Paper>
                </Grid>
            </Grid>

            {/* Variantes Dialog */}
            <Dialog open={variantDialogOpen} onClose={() => setVariantDialogOpen(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Select Variants: {selectedProduct?.design_number}</DialogTitle>
                <DialogContent>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>SKU / Attributes</TableCell>
                                <TableCell>Price</TableCell>
                                <TableCell>Quantity</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {selectedProduct?.variants.map((v) => (
                                <TableRow key={v.id}>
                                    <TableCell>
                                        {Object.entries(v.attributes).map(([k, val]) => (
                                            <Chip key={k} label={`${k}: ${val}`} size="small" sx={{ mr: 0.5 }} />
                                        ))}
                                    </TableCell>
                                    <TableCell>{selectedProduct.base_price + (v.price_adjustment || 0)}</TableCell>
                                    <TableCell>
                                        <TextField
                                            type="number"
                                            size="small"
                                            sx={{ width: 80 }}
                                            value={qtyInputs[v.id] || ''}
                                            onChange={(e) => setQtyInputs(prev => ({ ...prev, [v.id]: parseInt(e.target.value) || 0 }))}
                                        />
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setVariantDialogOpen(false)}>Cancel</Button>
                    <Button onClick={handleAddToCart} variant="contained">Add to Cart</Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
}
