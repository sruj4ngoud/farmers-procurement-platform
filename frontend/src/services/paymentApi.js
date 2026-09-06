import { api } from './api.js';

export const paymentApi = {
  getByBooking: (bookingId) => api.get(`/payments/${bookingId}`),
};
