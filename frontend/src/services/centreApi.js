import { api } from './api.js';

export const centreApi = {
  list: () => api.get('/centres'),
  nearby: (passbook) => api.getPublic(`/centres/nearby?passbook_number=${passbook}`),
  getById: (id) => api.get(`/centres/${id}`),
  getSlots: (centreId) => api.get(`/centres/${centreId}/slots`),
};
