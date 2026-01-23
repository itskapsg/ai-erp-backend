/**
 * API Service Layer
 * Handles all communication with the Dynamic Approval System backend
 */

import axios from 'axios';
import { jwtDecode } from 'jwt-decode';

// API Configuration
const API_BASE_URL = 'http://95.111.253.134:54279/api/v1';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token management
const TOKEN_KEY = 'erp_token';
const USER_KEY = 'erp_user';

export const tokenManager = {
  getToken: () => localStorage.getItem(TOKEN_KEY),
  setToken: (token) => localStorage.setItem(TOKEN_KEY, token),
  removeToken: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
  getUser: () => {
    const user = localStorage.getItem(USER_KEY);
    return user ? JSON.parse(user) : null;
  },
  setUser: (user) => localStorage.setItem(USER_KEY, JSON.stringify(user)),
  isTokenValid: () => {
    const token = tokenManager.getToken();
    if (!token) return false;
    
    try {
      const decoded = jwtDecode(token);
      return decoded.exp * 1000 > Date.now();
    } catch {
      return false;
    }
  }
};

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = tokenManager.getToken();
    if (token && tokenManager.isTokenValid()) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      tokenManager.removeToken();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Authentication API
export const authAPI = {
  login: async (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await api.post('/auth/token', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    
    const { access_token, user_id, username: user, role } = response.data;
    
    // Store token and user info
    tokenManager.setToken(access_token);
    tokenManager.setUser({ id: user_id, username: user, role });
    
    return response.data;
  },
  
  logout: () => {
    tokenManager.removeToken();
  },
  
  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  }
};

// Partners API
export const partnersAPI = {
  getPartners: async (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.status) params.append('status', filters.status);
    if (filters.type) params.append('type', filters.type);
    
    const response = await api.get(`/partners/?${params}`);
    return response.data;
  },
  
  getPartner: async (id) => {
    const response = await api.get(`/partners/${id}`);
    return response.data;
  },
  
  createPartner: async (partnerData) => {
    const response = await api.post('/partners/', partnerData);
    return response.data;
  },
  
  approvePartner: async (id, action, reason = null) => {
    const response = await api.put(`/partners/${id}/approve`, {
      action,
      reason
    });
    return response.data;
  },
  
  getPendingCount: async () => {
    const response = await api.get('/partners/pending/count');
    return response.data;
  }
};

// Health check
export const healthAPI = {
  check: async () => {
    const response = await axios.get(`${API_BASE_URL.replace('/api/v1', '')}/health`);
    return response.data;
  }
};

export default api;