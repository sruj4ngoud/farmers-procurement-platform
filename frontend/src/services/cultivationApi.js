import { api } from './api.js';

export const cultivationApi = {
  list: () => api.get('/farmer/cultivations'),
  create: (data) => api.post('/farmer/cultivations', data),
  updateQuantityToSell: (cultivationId, quantity) =>
    api.put(`/farmer/cultivations/${cultivationId}/quantity-to-sell`, { quantity_to_sell_quintals: quantity }),
};
