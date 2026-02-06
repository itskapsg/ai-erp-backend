
import axios from 'axios';

const api = axios.create({
    baseURL: '/api/v1', // Proxy handles request to localhost:8000
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request Interceptor: Attach Token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response Interceptor: Handle Errors
api.interceptors.response.use(
    (response) => response.data, // Unwrap data directly
    (error) => {
        // Customize error handling here (e.g., redirect on 401)
        if (error.response?.status === 401) {
            // Clear token and redirect?
            // window.location.href = '/login'; 
            console.warn("Unauthorized - Token might be invalid");
        }
        return Promise.reject(error.response?.data || error.message);
    }
);

export default api;
