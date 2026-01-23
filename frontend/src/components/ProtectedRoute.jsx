/**
 * Protected Route Component
 * Handles authentication and authorization
 */

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { tokenManager } from '../services/api';

const ProtectedRoute = ({ children }) => {
  const location = useLocation();
  
  if (!tokenManager.isTokenValid()) {
    // Redirect to login page with return url
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

export default ProtectedRoute;