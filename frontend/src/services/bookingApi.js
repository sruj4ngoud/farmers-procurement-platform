import { api } from './api.js';

export const bookingApi = {
  list: () => api.get('/bookings'),
  getById: (id) => api.get(`/bookings/${id}`),
  create: (data) => api.post('/bookings', data),
  generateToken: (bookingId) => api.post(`/bookings/${bookingId}/token`),
};
