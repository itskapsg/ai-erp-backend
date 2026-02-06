import React, { useState, useEffect } from 'react';
import {
  Container, Typography, Box, Button, CircularProgress,
  Grid, Card, CardContent, CardActions, Dialog, DialogTitle,
  DialogContent, DialogActions, Stepper, Step, StepLabel,
  TextField, FormControl, InputLabel, Select, MenuItem,
  FormGroup, FormControlLabel, Checkbox, IconButton, Snackbar, Alert
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import { namasteAPI, partnersAPI } from '../services/api';
import moment from 'moment';

const steps = ['Visit Details', 'Itinerary', 'Accommodation & Food', 'Transport'];

const Namaste = () => {
  const [visits, setVisits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openWizard, setOpenWizard] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [partners, setPartners] = useState([]);
  const [newVisit, setNewVisit] = useState({
    partner_id: '',
    purpose: '',
    start_date: '',
    end_date: '',
    notes: '',
    itinerary: [],
    accommodation_type: 'NONE',
    bed_number: null,
    meal_plan: {
      dietary_preference: 'STANDARD',
      breakfast: false,
      lunch: false,
      dinner: false,
    },
    transport_pickup: false,
    pickup_details: '',
    transport_drop: false,
    drop_details: '',
    market_tour: false,
  });
  const [itineraryItem, setItineraryItem] = useState({ date: '', description: '' });
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [bedAvailability, setBedAvailability] = useState([]);

  useEffect(() => {
    fetchVisits();
    fetchPartners();
  }, []);

  const fetchVisits = async () => {
    try {
      setLoading(true);
      const data = await namasteAPI.fetchVisits();
      setVisits(data);
    } catch (error) {
      console.error('Error fetching visits:', error);
      showSnackbar('Failed to fetch visits.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchPartners = async () => {
    try {
      const data = await partnersAPI.fetchPartners();
      setPartners(data);
    } catch (error) {
      console.error('Error fetching partners:', error);
      showSnackbar('Failed to fetch partners for visit creation.', 'error');
    }
  };

  const showSnackbar = (message, severity) => {
    setSnackbar({ open: true, message, severity });
  };

  const handleSnackbarClose = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const handleOpenWizard = () => {
    setOpenWizard(true);
    resetWizard();
  };

  const handleCloseWizard = () => {
    setOpenWizard(false);
    resetWizard();
  };

  const resetWizard = () => {
    setActiveStep(0);
    setNewVisit({
      partner_id: '',
      purpose: '',
      start_date: '',
      end_date: '',
      notes: '',
      itinerary: [],
      accommodation_type: 'NONE',
      bed_number: null,
      meal_plan: {
        dietary_preference: 'STANDARD',
        breakfast: false,
        lunch: false,
        dinner: false,
      },
      transport_pickup: false,
      pickup_details: '',
      transport_drop: false,
      drop_details: '',
      market_tour: false,
    });
    setItineraryItem({ date: '', description: '' });
    setBedAvailability([]);
  };

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const handleVisitChange = (e) => {
    const { name, value } = e.target;
    setNewVisit((prev) => ({ ...prev, [name]: value }));
  };

  const handleMealPlanChange = (e) => {
    const { name, value, type, checked } = e.target;
    setNewVisit((prev) => ({
      ...prev,
      meal_plan: {
        ...prev.meal_plan,
        [name]: type === 'checkbox' ? checked : value,
      },
    }));
  };

  const handleTransportChange = (e) => {
    const { name, checked } = e.target;
    setNewVisit((prev) => ({ ...prev, [name]: checked }));
  };

  const handleItineraryItemChange = (e) => {
    const { name, value } = e.target;
    setItineraryItem((prev) => ({ ...prev, [name]: value }));
  };

  const addItineraryItem = () => {
    if (itineraryItem.date && itineraryItem.description) {
      setNewVisit((prev) => ({
        ...prev,
        itinerary: [...prev.itinerary, itineraryItem],
      }));
      setItineraryItem({ date: '', description: '' });
    } else {
      showSnackbar('Please fill in both date and description for itinerary item.', 'warning');
    }
  };

  const removeItineraryItem = (index) => {
    setNewVisit((prev) => ({
      ...prev,
      itinerary: prev.itinerary.filter((_, i) => i !== index),
    }));
  };

  const handleAccommodationChange = async (e) => {
    const { name, value } = e.target;
    setNewVisit((prev) => ({ ...prev, [name]: value }));

    if (name === 'accommodation_type' && value === 'OFFICE_GUEST_HOUSE' && newVisit.start_date) {
      try {
        const availability = await namasteAPI.checkBedAvailability(newVisit.start_date);
        setBedAvailability(availability);
      } catch (error) {
        console.error('Error checking bed availability:', error);
        showSnackbar('Failed to check bed availability.', 'error');
        setBedAvailability([]);
      }
    } else {
      setBedAvailability([]);
    }
  };

  const handleBedNumberChange = (e) => {
    const { value } = e.target;
    setNewVisit((prev) => ({ ...prev, bed_number: value }));
  };


  const handleSubmit = async () => {
    try {
      const visitData = {
        partner_id: newVisit.partner_id,
        purpose: newVisit.purpose,
        start_date: newVisit.start_date,
        end_date: newVisit.end_date,
        notes: newVisit.notes,
        accommodation_type: newVisit.accommodation_type,
        // Atomic Booking Param:
        preferred_bed: newVisit.bed_number ? parseInt(newVisit.bed_number) : null,
        accommodation_details: null // Add details field if needed later
      };

      const createdVisit = await namasteAPI.createVisit(visitData);

      // Accommodation is now handled atomically in createVisit.
      // Removed separate addAccommodation call to prevent double booking/errors.

      // Add itinerary
      for (const item of newVisit.itinerary) {
        await namasteAPI.addAppointment(createdVisit.id, item);
      }

      // Add meal plan
      await namasteAPI.addMealPlan(createdVisit.id, newVisit.meal_plan);

      // Add transport
      if (newVisit.transport_pickup || newVisit.transport_drop || newVisit.market_tour) {
        await namasteAPI.addTransport(createdVisit.id, {
          pickup: newVisit.transport_pickup,
          pickup_details: newVisit.pickup_details,
          drop: newVisit.transport_drop,
          drop_details: newVisit.drop_details,
          market_tour: newVisit.market_tour,
        });
      }

      showSnackbar('Visit created successfully!', 'success');
      handleCloseWizard();
      fetchVisits();
    } catch (error) {
      console.error('Error creating visit:', error);
      showSnackbar(`Failed to create visit: ${error.response?.data?.detail || error.message}`, 'error');
    }
  };


  const getStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <Box sx={{ p: 3 }}>
            <FormControl fullWidth margin="normal" required>
              <InputLabel id="partner-select-label">Partner</InputLabel>
              <Select
                labelId="partner-select-label"
                id="partner-select"
                name="partner_id"
                value={newVisit.partner_id}
                label="Partner"
                onChange={handleVisitChange}
              >
                {partners.map((partner) => (
                  <MenuItem key={partner.id} value={partner.id}>
                    {partner.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Purpose of Visit"
              name="purpose"
              value={newVisit.purpose}
              onChange={handleVisitChange}
              fullWidth
              margin="normal"
              required
            />
            <TextField
              label="Start Date"
              name="start_date"
              type="date"
              value={newVisit.start_date}
              onChange={handleVisitChange}
              fullWidth
              margin="normal"
              InputLabelProps={{ shrink: true }}
              required
            />
            <TextField
              label="End Date"
              name="end_date"
              type="date"
              value={newVisit.end_date}
              onChange={handleVisitChange}
              fullWidth
              margin="normal"
              InputLabelProps={{ shrink: true }}
              required
            />
            <TextField
              label="Notes"
              name="notes"
              value={newVisit.notes}
              onChange={handleVisitChange}
              fullWidth
              margin="normal"
              multiline
              rows={3}
            />
          </Box>
        );
      case 1:
        return (
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>Itinerary Details</Typography>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={5}>
                <TextField
                  label="Date"
                  name="date"
                  type="date"
                  value={itineraryItem.date}
                  onChange={handleItineraryItemChange}
                  fullWidth
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={5}>
                <TextField
                  label="Description"
                  name="description"
                  value={itineraryItem.description}
                  onChange={handleItineraryItemChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={2}>
                <Button variant="contained" onClick={addItineraryItem}>Add</Button>
              </Grid>
            </Grid>
            <Box sx={{ mt: 2, maxHeight: 200, overflowY: 'auto' }}>
              {newVisit.itinerary.map((item, index) => (
                <Card key={index} sx={{ mb: 1 }}>
                  <CardContent sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 1, '&:last-child': { pb: 1 } }}>
                    <Typography variant="body2">{moment(item.date).format('DD-MM-YYYY')}: {item.description}</Typography>
                    <IconButton size="small" onClick={() => removeItineraryItem(index)}>
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </CardContent>
                </Card>
              ))}
            </Box>
          </Box>
        );
      case 2:
        return (
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>Accommodation & Food</Typography>
            <FormControl fullWidth margin="normal">
              <InputLabel id="accommodation-type-label">Accommodation Type</InputLabel>
              <Select
                labelId="accommodation-type-label"
                id="accommodation-type-select"
                name="accommodation_type"
                value={newVisit.accommodation_type}
                label="Accommodation Type"
                onChange={handleAccommodationChange}
              >
                <MenuItem value="NONE">None</MenuItem>
                <MenuItem value="OFFICE_GUEST_HOUSE">Office Guest House</MenuItem>
                <MenuItem value="HOTEL">Hotel</MenuItem>
              </Select>
            </FormControl>

            {newVisit.accommodation_type === 'OFFICE_GUEST_HOUSE' && (
              <FormControl fullWidth margin="normal">
                <InputLabel id="bed-number-label">Bed Number</InputLabel>
                <Select
                  labelId="bed-number-label"
                  id="bed-number-select"
                  name="bed_number"
                  value={newVisit.bed_number || ''}
                  label="Bed Number"
                  onChange={handleBedNumberChange}
                >
                  {bedAvailability.length > 0 ? (
                    bedAvailability.map((bed) => (
                      <MenuItem key={bed.bed_number} value={bed.bed_number} disabled={!bed.is_available}>
                        Bed {bed.bed_number} {bed.is_available ? '(Available)' : '(Occupied)'}
                      </MenuItem>
                    ))
                  ) : (
                    <MenuItem value="" disabled>
                      {newVisit.start_date ? 'Checking availability...' : 'Enter start date to check bed availability'}
                    </MenuItem>
                  )}
                </Select>
              </FormControl>
            )}

            <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>Meal Plan</Typography>
            <FormControl fullWidth margin="normal">
              <InputLabel id="dietary-preference-label">Dietary Preference</InputLabel>
              <Select
                labelId="dietary-preference-label"
                id="dietary-preference-select"
                name="dietary_preference"
                value={newVisit.meal_plan.dietary_preference}
                label="Dietary Preference"
                onChange={handleMealPlanChange}
              >
                <MenuItem value="STANDARD">Standard</MenuItem>
                <MenuItem value="VEG">Vegetarian</MenuItem>
                <MenuItem value="JAIN">Jain</MenuItem>
              </Select>
            </FormControl>
            <FormGroup>
              <FormControlLabel
                control={<Checkbox checked={newVisit.meal_plan.breakfast} onChange={handleMealPlanChange} name="breakfast" />}
                label="Breakfast"
              />
              <FormControlLabel
                control={<Checkbox checked={newVisit.meal_plan.lunch} onChange={handleMealPlanChange} name="lunch" />}
                label="Lunch"
              />
              <FormControlLabel
                control={<Checkbox checked={newVisit.meal_plan.dinner} onChange={handleMealPlanChange} name="dinner" />}
                label="Dinner"
              />
            </FormGroup>
          </Box>
        );
      case 3:
        return (
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>Transport Details</Typography>
            <FormGroup>
              <FormControlLabel
                control={<Checkbox checked={newVisit.transport_pickup} onChange={handleTransportChange} name="transport_pickup" />}
                label="Pickup Required"
              />
              {newVisit.transport_pickup && (
                <TextField
                  label="Pickup Details"
                  name="pickup_details"
                  value={newVisit.pickup_details}
                  onChange={handleVisitChange}
                  fullWidth
                  margin="normal"
                />
              )}
              <FormControlLabel
                control={<Checkbox checked={newVisit.transport_drop} onChange={handleTransportChange} name="transport_drop" />}
                label="Drop Required"
              />
              {newVisit.transport_drop && (
                <TextField
                  label="Drop Details"
                  name="drop_details"
                  value={newVisit.drop_details}
                  onChange={handleVisitChange}
                  fullWidth
                  margin="normal"
                />
              )}
              <FormControlLabel
                control={<Checkbox checked={newVisit.market_tour} onChange={handleTransportChange} name="market_tour" />}
                label="Market Tour Required"
              />
            </FormGroup>
          </Box>
        );
      default:
        return 'Unknown step';
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" component="h1">
          Namaste - Customer Visits
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleOpenWizard}
        >
          Create New Visit
        </Button>
      </Box>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 5 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={3}>
          {visits.length === 0 ? (
            <Grid item xs={12}>
              <Typography variant="h6" color="text.secondary" align="center">
                No active visits. Click "Create New Visit" to get started!
              </Typography>
            </Grid>
          ) : (
            visits.map((visit) => (
              <Grid item xs={12} sm={6} md={4} key={visit.id}>
                <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Typography variant="h6" component="div">
                      {visit.partner ? visit.partner.name : 'N/A'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Purpose: {visit.purpose}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Dates: {moment(visit.start_date).format('DD MMM')} - {moment(visit.end_date).format('DD MMM YYYY')}
                    </Typography>
                    {visit.meal_plan?.dietary_preference === 'JAIN' && (
                      <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                        <Typography variant="caption" sx={{ color: 'success.main', fontWeight: 'bold' }}>
                          🟢 JAIN
                        </Typography>
                      </Box>
                    )}
                    {visit.accommodation_type === 'OFFICE_GUEST_HOUSE' && (
                      <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                        <Typography variant="caption" sx={{ color: 'info.main', fontWeight: 'bold' }}>
                          {`Guest House ${visit.bed_number ? `(Bed ${visit.bed_number})` : ''}`}
                        </Typography>
                      </Box>
                    )}
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="subtitle2">Itinerary:</Typography>
                      {visit.itinerary && visit.itinerary.length > 0 ? (
                        visit.itinerary.map((item, idx) => (
                          <Typography key={idx} variant="body2" color="text.secondary" sx={{ ml: 1, fontSize: '0.8rem' }}>
                            • {moment(item.date).format('DD/MM')}: {item.description}
                          </Typography>
                        ))
                      ) : (
                        <Typography variant="body2" color="text.secondary" sx={{ ml: 1, fontSize: '0.8rem' }}>
                          No itinerary planned.
                        </Typography>
                      )}
                    </Box>
                  </CardContent>
                  <CardActions>
                    <Button size="small" startIcon={<EditIcon />}>Edit</Button>
                    <Button size="small" color="error" startIcon={<DeleteIcon />}>Delete</Button>
                  </CardActions>
                </Card>
              </Grid>
            ))
          )}
        </Grid>
      )}

      <Dialog open={openWizard} onClose={handleCloseWizard} maxWidth="md" fullWidth>
        <DialogTitle>Create New Visit</DialogTitle>
        <DialogContent dividers>
          <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 3 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
          {getStepContent(activeStep)}
        </DialogContent>
        <DialogActions>
          {activeStep !== 0 && (
            <Button onClick={handleBack}>Back</Button>
          )}
          {activeStep === steps.length - 1 ? (
            <Button variant="contained" onClick={handleSubmit} color="primary">
              Finish
            </Button>
          ) : (
            <Button variant="contained" onClick={handleNext} color="primary">
              Next
            </Button>
          )}
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleSnackbarClose} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default Namaste;
