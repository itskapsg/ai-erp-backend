
import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useForm, Controller } from 'react-hook-form';
import {
    Box, Grid, TextField, MenuItem, Typography, Button, Paper, Alert
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { DataService } from '@/services/dataService';
import { Order } from '@/types';
import api from '@/api/axios';

export default function Reconciliation() {
    const { control, watch, register, handleSubmit } = useForm();
    const selectedSupplierId = watch('supplierId');

    // Queries
    const { data: suppliers = [] } = useQuery({
        queryKey: ['partners', 'SUPPLIER'],
        queryFn: () => DataService.getPartners('SUPPLIER')
    });

    // Fetch Unbilled Orders for this Supplier
    // Mocking endpoint that filters by status=CONFIRMED
    // In real app, we'd add status filter to getOrders
    const { data: unbilledOrders = [], isFetching } = useQuery({
        queryKey: ['orders', 'unbilled', selectedSupplierId],
        queryFn: async () => {
            /* 
               Ideally: DataService.getOrders({ seller_id: selectedSupplierId, status: 'confirmed' })
               For now, just fetching all and filtering in client if API doesn't support filter
            */
            // Using direct axios for ad-hoc query if DataService doesn't cover it
            const res = await api.get('/orders', { params: { seller_id: selectedSupplierId } });
            return (res as unknown as Order[]).filter(o => o.status === 'confirmed');
        },
        enabled: !!selectedSupplierId
    });

    const [selection, setSelection] = useState<string[]>([]);

    const reconcileMutation = useMutation({
        mutationFn: async (data: any) => {
            // 1. Create Invoice
            const invRes = await api.post('/accounting/invoices', {
                invoice_number: data.invoiceNumber,
                supplier_id: data.supplierId,
                date: data.date,
                total_amount: parseFloat(data.amount),
                order_id: selection[0] // 1:1 Mapping enforced by backend
            });

            // 2. Reconcile
            await api.post(`/accounting/invoices/${invRes.id}/reconcile`);
            return invRes;
        },
        onSuccess: () => {
            alert("Reconciliation Successful! Ledger Updated.");
            setSelection([]);
        },
        onError: (err: any) => alert(err.detail || "Failed")
    });

    const onSubmit = (data: any) => {
        if (selection.length !== 1) return alert("Select exactly ONE order to reconcile against.");
        reconcileMutation.mutate(data);
    };

    const columns: GridColDef[] = [
        { field: 'order_number', headerName: 'Order #', width: 120 },
        { field: 'total_amount', headerName: 'Amount', width: 120 },
        { field: 'created_at', headerName: 'Date', width: 150 },
        { field: 'status', headerName: 'Status', width: 120 }
    ];

    return (
        <Box>
            <Typography variant="h5" color="primary" gutterBottom>Reconciliation Workbench</Typography>

            <form onSubmit={handleSubmit(onSubmit)}>
                <Paper sx={{ p: 2, mb: 2 }}>
                    <Grid container spacing={2}>
                        <Grid size={{ xs: 12, md: 4 }}>
                            <Controller
                                name="supplierId"
                                control={control}
                                render={({ field }) => (
                                    <TextField {...field} select label="Select Supplier" fullWidth>
                                        {suppliers.map(s => <MenuItem key={s.id} value={s.id}>{s.name}</MenuItem>)}
                                    </TextField>
                                )}
                            />
                        </Grid>
                        <Grid size={{ xs: 6, md: 3 }}>
                            <TextField {...register('invoiceNumber')} label="Invoice No" fullWidth required />
                        </Grid>
                        <Grid size={{ xs: 6, md: 3 }}>
                            <TextField {...register('date')} type="date" label="Date" InputLabelProps={{ shrink: true }} fullWidth required />
                        </Grid>
                        <Grid size={{ xs: 6, md: 2 }}>
                            <TextField {...register('amount')} type="number" label="Amount" fullWidth required />
                        </Grid>
                    </Grid>
                </Paper>

                <Paper sx={{ height: 400, width: '100%', mb: 2 }}>
                    <DataGrid
                        rows={unbilledOrders}
                        columns={columns}
                        loading={isFetching}
                        checkboxSelection
                        onRowSelectionModelChange={(ids) => setSelection(ids as string[])}
                        rowSelectionModel={selection}
                    />
                </Paper>

                <Button variant="contained" size="large" type="submit" disabled={selection.length !== 1}>
                    Reconcile & Post to Ledger
                </Button>
            </form>
        </Box>
    );
}
