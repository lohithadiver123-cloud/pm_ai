/**
 * API service layer.
 * Provides an axios instance configured with the backend base URL
 * and JWT token attachment from localStorage.
 */

import axios from 'axios';

// Create axios instance with relative base URL for Vite proxy.
// No default Content-Type: axios infers application/json for plain objects,
// and leaving it unset lets the browser build the multipart boundary for
// FormData bodies (setting it globally broke every FormData request with a 422).
const api = axios.create({
  baseURL: '/api',
});

// Request interceptor — attach JWT token to every request
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('pm_copilot_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor — handle 401 by redirecting to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('pm_copilot_token');
      localStorage.removeItem('pm_copilot_user');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

export default api;
