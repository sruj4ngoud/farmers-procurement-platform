import { api } from './api.js';

export const authApi = {
  requestOtp: (passbook_number, mobile_number) =>
    api.post('/auth/request-otp', { passbook_number, mobile_number }),

  verifyOtp: (passbook_number, mobile_number, otp) =>
    api.post('/auth/verify-otp', { passbook_number, mobile_number, otp }),

  logout: () => api.post('/auth/logout'),
};
