import { createContext, useContext, useState, useCallback } from 'react';
import { adminApi } from '../services/adminApi.js';

const AdminContext = createContext(null);

export function AdminProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('fp_admin_token'));
  const [admin, setAdmin] = useState(() => {
    try {
      const d = localStorage.getItem('fp_admin');
      return d ? JSON.parse(d) : null;
    } catch { return null; }
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const isAuthenticated = !!token;

  const login = useCallback(async (username, password) => {
    setLoading(true);
    setError(null);
    try {
      const res = await adminApi.login(username, password);
      const newToken = res.access_token;
      const adminData = {
        admin_id: res.admin_id,
        username: res.username,
        district: res.district,
        admin_name: res.admin_name,
      };
      localStorage.setItem('fp_admin_token', newToken);
      localStorage.setItem('fp_admin', JSON.stringify(adminData));
      setToken(newToken);
      setAdmin(adminData);
      return res;
    } catch (e) {
      setError(e.message);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('fp_admin_token');
    localStorage.removeItem('fp_admin');
    setToken(null);
    setAdmin(null);
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return (
    <AdminContext.Provider value={{ token, admin, isAuthenticated, loading, error, login, logout, clearError, setError }}>
      {children}
    </AdminContext.Provider>
  );
}

export function useAdmin() {
  const ctx = useContext(AdminContext);
  if (!ctx) throw new Error('useAdmin must be used within AdminProvider');
  return ctx;
}
