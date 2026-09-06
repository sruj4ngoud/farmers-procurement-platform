import { api } from './api.js';

export const queueApi = {
  getStatus: (bookingId) => api.get(`/queue/${bookingId}`),
};
