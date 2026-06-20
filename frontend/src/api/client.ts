import axios from 'axios';

// Get base URL from environment variables, default to backend running on port 8000
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
const baseURL = `${apiBaseUrl.replace(/\/$/, '')}/api/v1`;

const client = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Interceptor to inject the access token into the Authorization header
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor to handle 401 unauthorized errors safely
client.interceptors.response.use(
  (response) => response,
  (error) => {
    const originalRequest = error.config;
    
    if (error.response && error.response.status === 401) {
      const isLogin = originalRequest.url && originalRequest.url.includes('/auth/login');
      const isRegister = originalRequest.url && originalRequest.url.includes('/auth/register');
      
      // If we encounter a 401 on protected requests (excluding login/register attempts)
      if (!isLogin && !isRegister) {
        localStorage.removeItem('access_token');
        
        // Prevent redirect loop if already on login/register pages
        if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
          // Dispatch a custom event to notify AuthContext to clear local state without circular dependency
          window.dispatchEvent(new Event('auth_unauthorized'));
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default client;
