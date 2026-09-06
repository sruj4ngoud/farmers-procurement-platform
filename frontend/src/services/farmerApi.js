import { api } from './api.js';

export const farmerApi = {
  getDashboard: () => api.get('/farmer/dashboard'),
  getProfile: (passbook) => api.get(`/farmers/${passbook}`),
};
