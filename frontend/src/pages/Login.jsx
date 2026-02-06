/**
 * Login Page - Mobile-Friendly Authentication
 * Responsive design with centered card layout
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  Container,
  Avatar,
  InputAdornment,
  IconButton,
  useTheme,
  useMediaQuery
} from '@mui/material';
import {
  Login as LoginIcon,
  Visibility,
  VisibilityOff,
  Person,
  Lock
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { authAPI, tokenManager } from '../services/api';

const Login = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Redirect if already logged in
  React.useEffect(() => {
    if (tokenManager.isTokenValid()) {
      navigate('/dashboard');
    }
  }, [navigate]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError(''); // Clear error when user types
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await authAPI.login(formData.username, formData.password);
      navigate('/dashboard');
    } catch (err) {
      setError(
        err.response?.data?.detail || 
        'Login failed. Please check your credentials.'
      );
    } finally {
      setLoading(false);
    }
  };

  const demoUsers = [
    { username: 'admin', role: 'Admin', color: '#f44336' },
    { username: 'manager', role: 'Manager', color: '#ff9800' },
    { username: 'accountant', role: 'Accountant', color: '#2196f3' },
    { username: 'salesman', role: 'Salesman', color: '#4caf50' }
  ];

  const handleDemoLogin = (username) => {
    setFormData((prev) => ({
      ...prev,
      username,
      password: `${username}123`
    }));
  };

  return (
    <Container component="main" maxWidth="sm">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          py: 3
        }}
      >
        {/* Logo/Header */}
        <Box sx={{ mb: 4, textAlign: 'center' }}>
          <Avatar
            sx={{
              m: 'auto',
              mb: 2,
              bgcolor: 'primary.main',
              width: 64,
              height: 64,
              fontSize: '2rem'
            }}
          >
            🚀
          </Avatar>
          <Typography component="h1" variant="h4" fontWeight="bold" gutterBottom>
            AI ERP System
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Dynamic Approval System
          </Typography>
        </Box>

        {/* Login Card */}
        <Card
          sx={{
            width: '100%',
            maxWidth: 400,
            boxShadow: theme.shadows[8],
            borderRadius: 2
          }}
        >
          <CardContent sx={{ p: 4 }}>
            <Box component="form" onSubmit={handleSubmit}>
              <Typography variant="h5" component="h2" gutterBottom textAlign="center">
                Sign In
              </Typography>

              {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {error}
                </Alert>
              )}

              <TextField
                margin="normal"
                required
                fullWidth
                id="username"
                label="Username"
                name="username"
                autoComplete="username"
                autoFocus
                value={formData.username}
                onChange={handleChange}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Person color="action" />
                    </InputAdornment>
                  ),
                }}
              />

              <TextField
                margin="normal"
                required
                fullWidth
                name="password"
                label="Password"
                type={showPassword ? 'text' : 'password'}
                id="password"
                autoComplete="current-password"
                value={formData.password}
                onChange={handleChange}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Lock color="action" />
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="toggle password visibility"
                        onClick={() => setShowPassword(!showPassword)}
                        edge="end"
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />

              <Button
                type="submit"
                fullWidth
                variant="contained"
                sx={{ mt: 3, mb: 2, py: 1.5 }}
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : <LoginIcon />}
              >
                {loading ? 'Signing In...' : 'Sign In'}
              </Button>
            </Box>
          </CardContent>
        </Card>

        {/* Demo Users */}
        <Card sx={{ width: '100%', maxWidth: 400, mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom textAlign="center">
              Demo Users
            </Typography>
            <Typography variant="body2" color="text.secondary" textAlign="center" sx={{ mb: 2 }}>
              Click to auto-fill credentials
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, justifyContent: 'center' }}>
              {demoUsers.map((user) => (
                <Button
                  key={user.username}
                  type="button"
                  variant="outlined"
                  size="small"
                  onClick={() => handleDemoLogin(user.username)}
                  sx={{
                    borderColor: user.color,
                    color: user.color,
                    '&:hover': {
                      backgroundColor: user.color + '10',
                      borderColor: user.color,
                    },
                    minWidth: isMobile ? '45%' : 'auto'
                  }}
                >
                  {user.role}
                </Button>
              ))}
            </Box>
          </CardContent>
        </Card>

        {/* Footer */}
        <Typography variant="body2" color="text.secondary" textAlign="center" sx={{ mt: 4 }}>
          © 2026 AI ERP System. Dynamic Approval Workflow v2.0
        </Typography>
      </Box>
    </Container>
  );
};

export default Login;