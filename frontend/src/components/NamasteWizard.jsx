
import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Stepper,
  Step,
  StepLabel,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  RadioGroup,
  FormControlLabel,
  Radio,
  Checkbox,
  FormGroup,
  Typography,
  Box,
} from '@mui/material';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import dayjs from 'dayjs';

const steps = ['Visit Details', 'Accommodation & Food', 'Logistics'];

const NamasteWizard = ({ open, handleClose }) => {
  const [activeStep, setActiveStep] = useState(0);
  const [formData, setFormData] = useState({
    visitorName: '',
    purpose: '',
    checkIn: null,
    checkOut: null,
    accommodationType: '',
    mealPlan: '',
    pickup: false,
    drop: false,
    marketTour: false,
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({ ...prevData, [name]: value }));
  };

  const handleDateChange = (name, date) => {
    setFormData((prevData) => ({ ...prevData, [name]: date }));
  };

  const handleCheckboxChange = (e) => {
    const { name, checked } = e.target;
    setFormData((prevData) => ({ ...prevData, [name]: checked }));
  };

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const handleSubmit = () => {
    console.log('Form Data Submitted:', formData);
    // Here you would typically send the data to your backend API
    handleClose();
  };

  const getStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Visitor Name"
              name="visitorName"
              value={formData.visitorName}
              onChange={handleInputChange}
              fullWidth
            />
            <TextField
              label="Purpose of Visit"
              name="purpose"
              value={formData.purpose}
              onChange={handleInputChange}
              fullWidth
            />
            <LocalizationProvider dateAdapter={AdapterDayjs}>
              <DatePicker
                label="Check-in Date"
                value={formData.checkIn}
                onChange={(newValue) => handleDateChange('checkIn', newValue)}
                renderInput={(params) => <TextField {...params} fullWidth />}
              />
              <DatePicker
                label="Check-out Date"
                value={formData.checkOut}
                onChange={(newValue) => handleDateChange('checkOut', newValue)}
                renderInput={(params) => <TextField {...params} fullWidth />}
              />
            </LocalizationProvider>
          </Box>
        );
      case 1:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Accommodation Type</InputLabel>
              <Select
                name="accommodationType"
                value={formData.accommodationType}
                label="Accommodation Type"
                onChange={handleInputChange}
              >
                <MenuItem value="OFFICE_GUEST_HOUSE">Office Guest House (5-Bed)</MenuItem>
                <MenuItem value="HOTEL">Hotel (External)</MenuItem>
              </Select>
            </FormControl>

            <FormControl component="fieldset">
              <Typography variant="subtitle1">Meal Plan</Typography>
              <RadioGroup
                name="mealPlan"
                value={formData.mealPlan}
                onChange={handleInputChange}
                row
              >
                <FormControlLabel value="JAIN" control={<Radio />} label="Jain" />
                <FormControlLabel value="VEG" control={<Radio />} label="Veg" />
                <FormControlLabel value="STANDARD" control={<Radio />} label="Standard" />
              </RadioGroup>
            </FormControl>
          </Box>
        );
      case 2:
        return (
          <Box>
            <Typography variant="subtitle1" gutterBottom>Logistics</Typography>
            <FormGroup>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.pickup}
                    onChange={handleCheckboxChange}
                    name="pickup"
                  />
                }
                label="Pickup"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.drop}
                    onChange={handleCheckboxChange}
                    name="drop"
                  />
                }
                label="Drop"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.marketTour}
                    onChange={handleCheckboxChange}
                    name="marketTour"
                  />
                }
                label="Market Tour"
              />
            </FormGroup>
          </Box>
        );
      default:
        return 'Unknown step';
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Create New Visit</DialogTitle>
      <Stepper activeStep={activeStep} sx={{ p: 3 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>
      <DialogContent>
        {getStepContent(activeStep)}
      </DialogContent>
      <DialogActions>
        <Button disabled={activeStep === 0} onClick={handleBack}>
          Back
        </Button>
        <Button
          variant="contained"
          onClick={activeStep === steps.length - 1 ? handleSubmit : handleNext}
        >
          {activeStep === steps.length - 1 ? 'Finish' : 'Next'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default NamasteWizard;
