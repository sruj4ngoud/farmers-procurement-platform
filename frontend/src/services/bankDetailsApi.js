import { api } from './api.js';

export const bankDetailsApi = {
  get: () => api.get('/farmer/bank-details'),
  save: (data) => api.post('/farmer/bank-details', data),
  requestOtp: () => api.post('/farmer/bank-details/request-otp'),
  verifyOtp: (otp) => api.post('/farmer/bank-details/verify-otp', { otp }),
};
