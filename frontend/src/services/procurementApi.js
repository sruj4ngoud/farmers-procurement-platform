import { api } from './api.js';

export const procurementApi = {
  getByBooking: (bookingId) => api.get(`/procurement/${bookingId}`),
};
