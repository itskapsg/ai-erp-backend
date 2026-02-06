import React, { useState, useEffect } from 'react';
import {
    Box,
    Grid,
    Paper,
    Typography,
    Button,
    TextField,
    CircularProgress,
    Snackbar,
    Alert
} from '@mui/material';
import api from '../services/api';

const ReviewInbox = () => {
    const [entries, setEntries] = useState([]);
    const [selectedEntry, setSelectedEntry] = useState(null);
    const [loading, setLoading] = useState(true);
    const [processing, setProcessing] = useState(false);
    const [formState, setFormState] = useState({});
    const [toast, setToast] = useState({ open: false, message: '', severity: 'info' });

    // Fetch Pending Entries
    const fetchEntries = async () => {
        setLoading(true);
        try {
            const response = await api.get('/staging/pending');
            setEntries(response.data);
            if (response.data.length > 0) {
                selectEntry(response.data[0]);
            } else {
                setSelectedEntry(null);
            }
        } catch (error) {
            console.error("Failed to fetch entries", error);
            showToast("Failed to fetch pending documents", "error");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchEntries();
    }, []);

    const selectEntry = (entry) => {
        setSelectedEntry(entry);
        setFormState(entry.ai_extracted_json || {});
    };

    const handleFieldChange = (key, value) => {
        setFormState(prev => ({ ...prev, [key]: value }));
    };

    const showToast = (message, severity) => {
        setToast({ open: true, message, severity });
    };

    const handleAction = async (status) => {
        if (!selectedEntry) return;

        setProcessing(true);
        try {
            await api.put(`/staging/${selectedEntry.id}`, {
                status: status,
                ai_extracted_json: formState
            });
            showToast(`Document ${status} Successfully!`, "success");

            // Artificial delay for better UX (so user sees the success state briefly if we added one, 
            // but here it just prevents instant flash)
            await new Promise(r => setTimeout(r, 500));

            await fetchEntries(); // Refresh list to get next item
        } catch (error) {
            console.error(`Failed to ${status}`, error);
            showToast(`Failed to ${status} document`, "error");
        } finally {
            setProcessing(false);
        }
    };

    if (loading && entries.length === 0) {
        return <Box display="flex" justifyContent="center" p={5}><CircularProgress /></Box>;
    }

    return (
        <Box sx={{ height: 'calc(100vh - 100px)', p: 2 }}>
            <Typography variant="h5" gutterBottom>Review Inbox ({entries.length})</Typography>

            {entries.length === 0 ? (
                <Paper sx={{ p: 4, textAlign: 'center' }}>
                    <Typography variant="h6">No pending documents to review! 🎉</Typography>
                </Paper>
            ) : (
                <Grid container spacing={2} sx={{ height: '100%' }}>
                    {/* LEFT: Image Viewer */}
                    <Grid item xs={12} md={6} sx={{ height: '100%' }}>
                        <Paper sx={{ height: '100%', p: 1, display: 'flex', flexDirection: 'column', bgcolor: '#f5f5f5' }}>
                            <Typography variant="subtitle2" gutterBottom>Source: {selectedEntry?.source_phone}</Typography>
                            {selectedEntry?.media_url ? (
                                <Box
                                    component="img"
                                    src={`/uploads/${selectedEntry.media_url.split('/').pop()}`}
                                    alt="Document"
                                    sx={{
                                        width: '100%',
                                        height: 'auto',
                                        maxHeight: 'calc(100vh - 200px)',
                                        objectFit: 'contain',
                                        flexGrow: 1
                                    }}
                                />
                            ) : (
                                <Box display="flex" alignItems="center" justifyContent="center" flexGrow={1}>
                                    <Typography>No Image Available</Typography>
                                </Box>
                            )}
                        </Paper>
                    </Grid>

                    {/* RIGHT: Edit Form */}
                    <Grid item xs={12} md={6} sx={{ height: '100%', overflowY: 'auto' }}>
                        <Paper sx={{ p: 3 }}>
                            <Typography variant="h6" gutterBottom color="primary">Extracted Data</Typography>

                            {Object.keys(formState).length === 0 ? (
                                <Alert severity="warning" sx={{ mb: 2 }}>
                                    No data extracted yet. Please review the image manually.
                                </Alert>
                            ) : (
                                <Grid container spacing={3}>
                                    {Object.entries(formState).map(([key, value]) => {
                                        if (key === 'items' && Array.isArray(value)) {
                                            return (
                                                <Grid item xs={12} key={key}>
                                                    <Typography variant="subtitle2" sx={{ mt: 1, mb: 1 }}>Items List</Typography>
                                                    <Paper variant="outlined" sx={{ p: 1, bgcolor: '#fafafa' }}>
                                                        {value.map((item, idx) => (
                                                            <Box key={idx} sx={{ mb: 1, borderBottom: '1px solid #eee', pb: 1 }}>
                                                                <Grid container spacing={1}>
                                                                    <Grid item xs={8}><Typography variant="body2"><strong>{item.description}</strong></Typography></Grid>
                                                                    <Grid item xs={2}><Typography variant="body2">x{item.quantity}</Typography></Grid>
                                                                    <Grid item xs={2}><Typography variant="body2">${item.price}</Typography></Grid>
                                                                </Grid>
                                                            </Box>
                                                        ))}
                                                    </Paper>
                                                </Grid>
                                            )
                                        }
                                        if (typeof value === 'object' && value !== null) {
                                            return null; // Skip complex objects for now unless specific
                                        }
                                        return (
                                            <Grid item xs={12} sm={6} key={key}>
                                                <TextField
                                                    fullWidth
                                                    label={key.replace(/_/g, ' ').toUpperCase()}
                                                    value={value}
                                                    onChange={(e) => handleFieldChange(key, e.target.value)}
                                                    variant="outlined"
                                                    size="small"
                                                    InputLabelProps={{ shrink: true }}
                                                />
                                            </Grid>
                                        )
                                    })}
                                </Grid>
                            )}

                            <Box sx={{ mt: 4, display: 'flex', gap: 2, justifyContent: 'flex-start' }}>
                                <Button
                                    variant="contained"
                                    color="success"
                                    onClick={() => handleAction('APPROVED')}
                                    size="large"
                                    disabled={processing}
                                    startIcon={processing ? <CircularProgress size={20} color="inherit" /> : null}
                                >
                                    {processing ? 'Processing...' : 'Approve'}
                                </Button>
                                <Button
                                    variant="contained"
                                    color="error"
                                    onClick={() => handleAction('REJECTED')}
                                    size="large"
                                    disabled={processing}
                                >
                                    Reject
                                </Button>
                            </Box>

                        </Paper>
                    </Grid>
                </Grid>
            )}

            <Snackbar open={toast.open} autoHideDuration={6000} onClose={() => setToast({ ...toast, open: false })}>
                <Alert severity={toast.severity}>{toast.message}</Alert>
            </Snackbar>
        </Box>
    );
};

export default ReviewInbox;
