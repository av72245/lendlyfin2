/**
 * Lendlyfin API Client
 * -----------------------------------------------------------
 * Single file imported by every HTML page that talks to the backend.
 *
 * Environment detection (in priority order):
 *  1. window.LENDLYFIN_API  — set manually before this script loads
 *  2. localhost / 127.0.0.1 — local dev  → http://localhost:8000
 *  3. file://               — opened from disk → localhost
 *  4. Everything else       — production → Render backend URL
 *
 * ⚠ After deploying to Render, replace RENDER_BACKEND_URL below
 *   with your actual Render service URL, e.g.:
 *   https://lendlyfin-api.onrender.com
 */
const RENDER_BACKEND_URL = 'https://lendlyfin-api.onrender.com';

const API_BASE = window.LENDLYFIN_API || (() => {
  const h = window.location.hostname;
  if (!h || h === 'localhost' || h === '127.0.0.1') return 'http://localhost:8000';
  return RENDER_BACKEND_URL;
})();


// ── TOKEN STORAGE ─────────────────────────────────────────────
const Auth = {
  getToken:    ()        => localStorage.getItem('lf_token'),
  setToken:    (t)       => localStorage.setItem('lf_token', t),
  removeToken: ()        => localStorage.removeItem('lf_token'),
  getUser:     ()        => { try { return JSON.parse(localStorage.getItem('lf_user') || 'null'); } catch { return null; } },
  setUser:     (u)       => localStorage.setItem('lf_user', JSON.stringify(u)),
  removeUser:  ()        => localStorage.removeItem('lf_user'),
  isLoggedIn:  ()        => !!localStorage.getItem('lf_token'),
  logout:      ()        => { Auth.removeToken(); Auth.removeUser(); window.location.href = '/admin/login.html'; },
};

// ── CORE FETCH WRAPPER ────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  const token = Auth.getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401) { Auth.logout(); return null; }

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `Error ${res.status}`);
  return data;
}

// ── PUBLIC ENDPOINTS ──────────────────────────────────────────
const LendlyAPI = {

  // Rates — used by homepage carousel + compare-loans page
  getRates: () => apiFetch('/api/rates'),

  // Borrowing power — server-side calculation
  calcBorrowingPower: (inputs) => apiFetch('/api/calc/borrowing-power', {
    method: 'POST', body: JSON.stringify(inputs),
  }),

  // Contact form submission
  submitLead: (formData) => apiFetch('/api/leads', {
    method: 'POST', body: JSON.stringify(formData),
  }),

  // ── AUTHENTICATED (broker/admin) ──────────────────────────

  // Auth
  login: async (email, password) => {
    const form = new URLSearchParams({ username: email, password });
    const res  = await fetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Login failed');
    Auth.setToken(data.access_token);
    Auth.setUser(data.user);
    return data;
  },

  getMe: () => apiFetch('/api/auth/me'),

  // Leads
  getLeads:    (params = {}) => apiFetch('/api/leads?' + new URLSearchParams(params)),
  getLead:     (id)          => apiFetch(`/api/leads/${id}`),
  updateLead:  (id, data)    => apiFetch(`/api/leads/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteLead:  (id)          => apiFetch(`/api/leads/${id}`, { method: 'DELETE' }),
  addNote:     (id, content) => apiFetch(`/api/leads/${id}/notes`, { method: 'POST', body: JSON.stringify({ content }) }),
  getStats:    ()            => apiFetch('/api/leads/stats'),

  // Rates admin
  updateRates: (rates) => apiFetch('/api/rates/bulk', { method: 'PUT', body: JSON.stringify({ rates }) }),

  // Users
  getUsers:    ()       => apiFetch('/api/auth/users'),
  createUser:  (data)   => apiFetch('/api/auth/users', { method: 'POST', body: JSON.stringify(data) }),
};

window.LendlyAPI = LendlyAPI;
window.Auth      = Auth;
