/**
 * Protected Route Component
 * Handles authentication and authorization
 */

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { tokenManager } from '../services/api';

const ProtectedRoute = ({ children, allowedRoles = [] }) => {
  const location = useLocation();
  const user = tokenManager.getUser();

  if (!tokenManager.isTokenValid()) {
    // Redirect to login page with return url
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Role-Based Access Control (RBAC)
  // Role-Based Access Control (RBAC)
  if (allowedRoles.length > 0) {
    if (!user || !allowedRoles.includes(user.role)) {
      // User does not have permission or user info is missing
      console.warn(`Access denied for role: ${user?.role} to ${location.pathname}`);
      return <Navigate to="/dashboard" replace />;
    }
  }

  return children;
};

export default ProtectedRoute;