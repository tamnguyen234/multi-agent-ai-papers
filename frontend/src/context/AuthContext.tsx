import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi } from '../api/authApi';
import type { UserResponse, UserLoginPayload, UserRegisterPayload } from '../api/authApi';

interface AuthContextType {
  currentUser: UserResponse | null;
  loading: boolean;
  error: string | null;
  login: (payload: UserLoginPayload) => Promise<void>;
  register: (payload: UserRegisterPayload) => Promise<void>;
  logout: () => void;
  refreshCurrentUser: () => Promise<void>;
  updateCurrentUserLocal: (fields: Partial<UserResponse>) => void;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<UserResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Function to fetch the current user profile from backend
  const refreshCurrentUser = async () => {
    try {
      const user = await authApi.getMe();
      setCurrentUser(user);
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch user profile:', err);
      logout();
    }
  };

  // Perform login
  const login = async (payload: UserLoginPayload) => {
    setLoading(true);
    setError(null);
    try {
      const data = await authApi.login(payload);
      localStorage.setItem('access_token', data.access_token);
      setCurrentUser(data.user);
    } catch (err: any) {
      let errMsg = 'Đăng nhập thất bại. Vui lòng kiểm tra lại tài khoản và mật khẩu.';
      if (!err.response) {
        errMsg = 'Không thể kết nối tới máy chủ. Vui lòng đảm bảo backend đang chạy và kết nối mạng ổn định.';
      } else if (err.response.status >= 500) {
        errMsg = 'Lỗi hệ thống phía máy chủ (Internal Server Error). Vui lòng thử lại sau.';
      } else if (err.response.data?.detail) {
        errMsg = err.response.data.detail;
      }
      setError(errMsg);
      throw new Error(errMsg);
    } finally {
      setLoading(false);
    }
  };

  // Perform register
  const register = async (payload: UserRegisterPayload) => {
    setLoading(true);
    setError(null);
    try {
      await authApi.register(payload);
    } catch (err: any) {
      let errMsg = 'Đăng ký thất bại. Tên đăng nhập hoặc email có thể đã tồn tại.';
      if (!err.response) {
        errMsg = 'Không thể kết nối tới máy chủ. Vui lòng đảm bảo backend đang chạy và kết nối mạng ổn định.';
      } else if (err.response.status >= 500) {
        errMsg = 'Lỗi hệ thống phía máy chủ (Internal Server Error). Vui lòng thử lại sau.';
      } else if (err.response.data?.detail) {
        errMsg = err.response.data.detail;
      }
      setError(errMsg);
      throw new Error(errMsg);
    } finally {
      setLoading(false);
    }
  };

  // Perform logout
  const logout = () => {
    localStorage.removeItem('access_token');
    setCurrentUser(null);
    setError(null);
    setLoading(false);
  };

  const updateCurrentUserLocal = (fields: Partial<UserResponse>) => {
    setCurrentUser((prev) => (prev ? { ...prev, ...fields } : null));
  };

  const clearError = () => setError(null);

  // Initialize and hydrate login state on app mount
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const user = await authApi.getMe();
          setCurrentUser(user);
        } catch (err) {
          console.error('Session validation failed:', err);
          localStorage.removeItem('access_token');
        }
      }
      setLoading(false);
    };

    initAuth();

    // Listen to unauthorized event dispatched by Axios interceptor to keep state in sync
    const handleUnauthorized = () => {
      setCurrentUser(null);
      setLoading(false);
    };

    window.addEventListener('auth_unauthorized', handleUnauthorized);
    return () => {
      window.removeEventListener('auth_unauthorized', handleUnauthorized);
    };
  }, []);

  return (
    <AuthContext.Provider
      value={{
        currentUser,
        loading,
        error,
        login,
        register,
        logout,
        refreshCurrentUser,
        updateCurrentUserLocal,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
