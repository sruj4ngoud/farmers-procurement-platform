import { api } from './api.js';

export const mspApi = {
  getAll: () => api.getPublic('/msp'),
  getCropMsp: (cropName) => api.getPublic(`/msp/${encodeURIComponent(cropName)}`),
};
