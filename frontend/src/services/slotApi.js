import { api } from './api.js';

export const slotApi = {
  list: () => api.get('/slots'),
  getById: (id) => api.get(`/slots/${id}`),
};
