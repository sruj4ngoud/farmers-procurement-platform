const BASE = '/api/admin';

function getAdminToken() {
  try { return localStorage.getItem('fp_admin_token'); } catch { return null; }
}

async function adminRequest(method, path, body, requireAuth = true) {
  const headers = { 'Content-Type': 'application/json' };
  const token = getAdminToken();
  if (token && requireAuth) headers['Authorization'] = `Bearer ${token}`;

  const opts = { method, headers };
  if (body !== undefined) opts.body = JSON.stringify(body);

  const res = await fetch(`${BASE}${path}`, opts);
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    const msg = data?.detail || `Request failed (${res.status})`;
    const err = new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

export const adminApi = {
  login: (username, password) =>
    adminRequest('POST', '/auth/login', { username, password }, false),

  // Dashboard & mandals
  getDashboard: () => adminRequest('GET', '/dashboard'),
  getMandals: () => adminRequest('GET', '/mandals'),
  getMandalDetail: (mandalId) => adminRequest('GET', `/mandals/${mandalId}`),

  // Farmers & centres & bookings (existing)
  getFarmers: () => adminRequest('GET', '/farmers'),
  getCentres: () => adminRequest('GET', '/centres'),
  getBookings: () => adminRequest('GET', '/bookings'),
  getDistrictInfo: () => adminRequest('GET', '/district-info'),

  // Crop CRUD
  getCrops: () => adminRequest('GET', '/crops'),
  getCrop: (cropId) => adminRequest('GET', `/crops/${cropId}`),
  createCrop: (data) => adminRequest('POST', '/crops', data),
  updateCrop: (cropId, data) => adminRequest('PUT', `/crops/${cropId}`, data),

  // Centre CRUD (district-scoped)
  getCentre: (centreId) => adminRequest('GET', `/centres/${centreId}`),
  createCentre: (data) => adminRequest('POST', '/centres', data),
  updateCentre: (centreId, data) => adminRequest('PUT', `/centres/${centreId}`, data),

  // Slot CRUD (district-scoped)
  getSlots: () => adminRequest('GET', '/slots'),
  getSlot: (slotId) => adminRequest('GET', `/slots/${slotId}`),
  createSlot: (data) => adminRequest('POST', '/slots', data),
  updateSlot: (slotId, data) => adminRequest('PUT', `/slots/${slotId}`, data),

  // Booking reviews
  getPendingReviews: () => adminRequest('GET', '/reviews/pending'),
  getAllReviews: () => adminRequest('GET', '/reviews/all'),
  reviewBooking: (bookingId, decision, comment) =>
    adminRequest('PUT', `/reviews/${bookingId}/review`, { decision, comment }),
  processAutoAccept: () => adminRequest('POST', '/reviews/auto-accept'),

  // Queue management
  getQueueOverview: () => adminRequest('GET', '/queue/overview'),
  getSlotTokens: (slotId) => adminRequest('GET', `/queue/slot/${slotId}/tokens`),
  transitionToken: (tokenId, newStatus) =>
    adminRequest('PUT', `/queue/tokens/${tokenId}/transition`, { new_status: newStatus }),
  callNextToken: (slotId) => adminRequest('POST', `/queue/slot/${slotId}/call-next`),

  // Procurement management
  getPendingProcurements: () => adminRequest('GET', '/procurement/pending'),
  getAllProcurements: () => adminRequest('GET', '/procurement/all'),
  getProcurementDetail: (bookingId) => adminRequest('GET', `/procurement/${bookingId}`),
  updateProcurement: (bookingId, data) =>
    adminRequest('PUT', `/procurement/${bookingId}`, data),
  completeProcurement: (bookingId) =>
    adminRequest('POST', `/procurement/${bookingId}/complete`),

  // Bank verification
  getBankVerifications: (status) => adminRequest('GET', `/bank-verification?status=${status || 'PENDING_VERIFICATION'}`),
  verifyBank: (bankDetailId, decision, reason) =>
    adminRequest('PUT', `/bank-verification/${bankDetailId}`, { decision, reason }),

  // Payment management
  getPaymentDashboard: () => adminRequest('GET', '/payments/dashboard'),
  getPayments: (status) => adminRequest('GET', `/payments${status ? `?status=${status}` : ''}`),
  updatePayment: (paymentId, data) => adminRequest('PUT', `/payments/${paymentId}`, data),
  processPayment: (paymentId) => adminRequest('POST', `/payments/${paymentId}/process`),
  creditPayment: (paymentId, ref) => adminRequest('POST', `/payments/${paymentId}/credit?transaction_ref=${ref || ''}`),
  failPayment: (paymentId, reason) => adminRequest('POST', `/payments/${paymentId}/fail?reason=${encodeURIComponent(reason || 'Failed')}`),

  // Reports
  reportFarmers: (mandal) => adminRequest('GET', `/reports/farmers${mandal ? `?mandal=${mandal}` : ''}`),
  reportCrops: () => adminRequest('GET', '/reports/crops'),
  reportCentres: () => adminRequest('GET', '/reports/centres'),
  reportBookings: () => adminRequest('GET', '/reports/bookings'),
  reportPayments: () => adminRequest('GET', '/reports/payments'),

  // Issues
  getIssues: (status) => adminRequest('GET', `/issues${status ? `?status=${status}` : ''}`),
  createIssue: (data) => adminRequest('POST', '/issues', data),
  updateIssue: (issueId, data) => adminRequest('PUT', `/issues/${issueId}`, data),

  // Audit logs
  getAuditLogs: () => adminRequest('GET', '/audit-logs'),

  // ML insights
  getMLInsights: () => adminRequest('GET', '/ml-insights'),

  // Final dashboard
  getDashboardFinal: () => adminRequest('GET', '/dashboard-final'),
};
