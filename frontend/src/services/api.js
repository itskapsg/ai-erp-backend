/**
 * API Service Layer
 * Handles all communication with the Dynamic Approval System backend
 */

import axios from 'axios';
import { jwtDecode } from 'jwt-decode';

// API Configuration
// Use the same host as the frontend but on port 54279 (backend port)
const API_BASE_URL = '/api/v1';

// Debug: Log the API URL
console.log('🔗 API Base URL:', API_BASE_URL);

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

  // Fetch partners by type for order creation
  fetchPartners: async (type = null) => {
    const params = new URLSearchParams();
    if (type) params.append('type', type);

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
  },

  updatePartnerStatus: async (id, status) => {
    const response = await api.put(`/partners/${id}/status`, null, { params: { status } });
    return response.data;
  }
};

// Approvals API - Dedicated approval management endpoints
export const approvalsAPI = {
  // Fetch all pending approvals across different resources
  fetchPendingApprovals: async () => {
    const response = await api.get('/partners/?workflow_stage=pending_approval');
    return response.data;
  },

  // Approve a partner
  approvePartner: async (id) => {
    const response = await api.put(`/partners/${id}/approve`, {
      action: 'approve'
    });
    return response.data;
  },

  // Reject a partner with reason
  rejectPartner: async (id, reason) => {
    const response = await api.put(`/partners/${id}/approve`, {
      action: 'reject',
      reason: reason
    });
    return response.data;
  },

  // Get approval statistics
  getApprovalStats: async () => {
    const response = await api.get('/approvals/stats');
    return response.data;
  },

  // Get approval history
  getApprovalHistory: async (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.workflow_stage) params.append('workflow_stage', filters.workflow_stage);
    if (filters.limit) params.append('limit', filters.limit);

    // For now, get all partners that are approved or rejected
    const response = await api.get(`/partners/?${params}`);
    const data = response.data;

    // Filter to only show approved/rejected items
    return data.filter(item => ['approved', 'rejected'].includes(item.workflow_stage));
  }
};

// Products API
export const productsAPI = {
  // Fetch all products with optional filters
  fetchProducts: async (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.category) params.append('category', filters.category);
    if (filters.workflow_stage) params.append('workflow_stage', filters.workflow_stage);
    if (filters.include_variants !== undefined) params.append('include_variants', filters.include_variants);

    const response = await api.get(`/products/?${params}`);
    return response.data;
  },

  // Get a specific product with variants
  getProduct: async (id, includeVariants = true) => {
    const response = await api.get(`/products/${id}?include_variants=${includeVariants}`);
    return response.data;
  },

  // Create a new product
  createProduct: async (productData) => {
    const response = await api.post('/products/', productData);
    return response.data;
  },

  // Update a product
  updateProduct: async (id, productData) => {
    const response = await api.put(`/products/${id}`, productData);
    return response.data;
  },

  // Delete a product
  deleteProduct: async (id) => {
    const response = await api.delete(`/products/${id}`);
    return response.data;
  },

  // Add a variant to a product
  addVariant: async (productId, variantData) => {
    const response = await api.post(`/products/${productId}/variants/`, variantData);
    return response.data;
  },

  // Update a variant
  updateVariant: async (productId, variantId, variantData) => {
    const response = await api.put(`/products/${productId}/variants/${variantId}`, variantData);
    return response.data;
  },

  // Delete a variant
  deleteVariant: async (productId, variantId) => {
    const response = await api.delete(`/products/${productId}/variants/${variantId}`);
    return response.data;
  },

  // Get product categories (for dropdown)
  getCategories: async () => {
    // This would ideally be a separate endpoint, but for now we'll derive from products
    const products = await api.get('/products/');
    const categories = [...new Set(products.data.map(p => p.category))];
    return categories.sort();
  },

  // Get pending products count
  getPendingCount: async () => {
    const response = await api.get('/products/?workflow_stage=pending_approval');
    return response.data.length;
  }
};

// Orders API
export const ordersAPI = {
  // Fetch all orders with optional filters
  fetchOrders: async (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.buyer_id) params.append('buyer_id', filters.buyer_id);
    if (filters.seller_id) params.append('seller_id', filters.seller_id);
    if (filters.status) params.append('status', filters.status);

    const response = await api.get(`/orders/?${params}`);
    return response.data;
  },

  // Get a specific order
  getOrder: async (id) => {
    const response = await api.get(`/orders/${id}`);
    return response.data;
  },

  // Create a new order
  createOrder: async (orderData) => {
    const response = await api.post('/orders/', orderData);
    return response.data;
  },

  // Approve or reject an order
  approveOrder: async (id, action, reason = null) => {
    const response = await api.post(`/orders/${id}/approval`, {
      action,
      reason
    });
    return response.data;
  },

  // Get pending orders count
  getPendingCount: async () => {
    const response = await api.get('/orders/pending/count');
    return response.data;
  },

  // Download order PDF
  downloadPDF: async (orderId) => {
    const response = await api.get(`/orders/${orderId}/pdf`, {
      responseType: 'blob'
    });
    return response.data;
  }
};

// Namaste API - Customer Visits Management
export const namasteAPI = {
  // Fetch visits with optional filter
  fetchVisits: async (filter = null) => {
    const params = new URLSearchParams();
    if (filter) params.append('status', filter);

    const response = await api.get(`/namaste/?${params}`);
    return response.data;
  },

  // Create a new visit
  createVisit: async (visitData) => {
    const response = await api.post('/namaste/', visitData);
    return response.data;
  },

  // Get a specific visit
  getVisit: async (id) => {
    const response = await api.get(`/namaste/${id}`);
    return response.data;
  },

  // Add accommodation (including bed assignment)
  addAccommodation: async (visitId, accommodationData) => {
    const response = await api.post(`/namaste/${visitId}/accommodation/`, accommodationData);
    return response.data;
  },

  // Add appointment to visit
  addAppointment: async (visitId, appointmentData) => {
    const response = await api.post(`/namaste/${visitId}/itinerary/`, appointmentData);
    return response.data;
  },

  // Add transport to visit
  addTransport: async (visitId, transportData) => {
    const response = await api.post(`/namaste/${visitId}/transport/`, transportData);
    return response.data;
  },

  // Add meal plan to visit
  addMealPlan: async (visitId, mealPlanData) => {
    const response = await api.post(`/namaste/${visitId}/meal-plan/`, mealPlanData);
    return response.data;
  },

  // Check bed availability
  checkBedAvailability: async (date) => {
    const response = await api.get(`/namaste/beds/availability?check_date=${date}`);
    return response.data;
  },

  // Get occupancy report
  getOccupancyReport: async (startDate, endDate) => {
    const response = await api.get(`/namaste/reports/occupancy?start_date=${startDate}&end_date=${endDate}`);
    return response.data;
  }
};

// Health check
// Users API
export const usersAPI = {
  getUsers: async (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.limit) params.append('limit', filters.limit);
    const response = await api.get(`/users/?${params}`);
    return response.data;
  },

  createUser: async (userData) => {
    const response = await api.post('/users/', userData);
    return response.data;
  }
};

export const healthAPI = {
  check: async () => {
    const response = await axios.get(`${API_BASE_URL.replace('/api/v1', '')}/health`);
    return response.data;
  }
};

export default api;
