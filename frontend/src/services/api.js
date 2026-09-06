const BASE = '/api';

function getToken() {
  try { return localStorage.getItem('fp_token'); } catch { return null; }
}

async function request(method, path, body, requireAuth = true) {
  const headers = { 'Content-Type': 'application/json' };
  const token = getToken();
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

export const api = {
  get:    (path) => request('GET', path),
  post:   (path, body) => request('POST', path, body),
  put:    (path, body) => request('PUT', path, body),
  del:    (path) => request('DELETE', path),
  getPublic: (path) => request('GET', path, undefined, false),
};
