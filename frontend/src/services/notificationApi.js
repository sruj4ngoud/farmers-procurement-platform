import { api } from './api.js';

export const notificationApi = {
  list: (passbook) => api.getPublic(`/notifications/${passbook}`),
  markRead: (notificationId) => api.put(`/notifications/${notificationId}/read`),
};
