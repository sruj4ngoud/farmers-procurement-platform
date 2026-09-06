import { api } from './api.js';

export const cropApi = {
  /** Get all active crops with MSP — replaces hardcoded CROPS array. */
  getActiveCrops: () => api.getPublic('/crops'),

  /** Get MSP for a specific crop. */
  getMsp: (cropName) => api.getPublic(`/crops/${encodeURIComponent(cropName)}/msp`),

  /** Get distinct crop categories. */
  getCategories: () => api.getPublic('/crop-categories'),
};
