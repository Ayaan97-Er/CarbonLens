/**
 * CARBONLENS — CENTRAL API CLIENT & UTILITIES
 */

const API_BASE_URL = `${window.location.origin}/api/v1`;

// Token Management
function getAuthToken() {
  return localStorage.getItem('carbonlens_token');
}

function setAuthToken(token) {
  localStorage.setItem('carbonlens_token', token);
}

function getStoredUser() {
  const user = localStorage.getItem('carbonlens_user');
  return user ? JSON.parse(user) : null;
}

function setStoredUser(user) {
  localStorage.setItem('carbonlens_user', JSON.stringify(user));
}

function clearAuthSession() {
  localStorage.removeItem('carbonlens_token');
  localStorage.removeItem('carbonlens_user');
}

/**
 * Universal Fetch wrapper with auth token injection, error handling, and 401 redirect
 */
async function apiFetch(endpoint, options = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
  const token = getAuthToken();

  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers
    });

    // Unauthorized - Session expired
    if (response.status === 401) {
      if (!window.location.pathname.includes('login.html') && !window.location.pathname.includes('register.html') && !window.location.pathname.endsWith('index.html') && window.location.pathname !== '/') {
        clearAuthSession();
        window.location.href = 'login.html?expired=1';
        return;
      }
    }

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      const errorMsg = data.detail || data.message || `Request failed with status ${response.status}`;
      const err = new Error(errorMsg);
      err.status = response.status;
      err.data = data;
      throw err;
    }

    return data;
  } catch (error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      showToast('Unable to connect to CarbonLens server. Please ensure backend is running.', 'error');
    }
    throw error;
  }
}

/**
 * Global Toast Notifications
 */
function showToast(message, type = 'success', duration = 3500) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
  toast.innerHTML = `
    <span style="font-weight: bold;">${icon}</span>
    <span>${message}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

/**
 * Format Helpers
 */
function formatKg(val) {
  if (val === undefined || val === null) return '0.0';
  return Number(val).toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

/**
 * Initialize Sidebar and Mobile Drawer Navigation
 */
function initLayout() {
  const toggleBtn = document.querySelector('.mobile-nav-toggle');
  const sidebar = document.querySelector('.sidebar');
  
  if (toggleBtn && sidebar) {
    let backdrop = document.querySelector('.sidebar-backdrop');
    if (!backdrop) {
      backdrop = document.createElement('div');
      backdrop.className = 'sidebar-backdrop';
      document.body.appendChild(backdrop);
    }

    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('open');
      backdrop.classList.toggle('active');
    });

    backdrop.addEventListener('click', () => {
      sidebar.classList.remove('open');
      backdrop.classList.remove('active');
    });
  }

  // Populate user badge in sidebar if present
  const user = getStoredUser();
  if (user) {
    const avatarEl = document.querySelector('.user-avatar');
    const nameEl = document.querySelector('.user-meta-name');
    const roleEl = document.querySelector('.user-meta-role');
    
    if (avatarEl) {
      avatarEl.textContent = (user.full_name || 'U').charAt(0).toUpperCase();
    }
    if (nameEl) {
      nameEl.textContent = user.full_name || 'User';
    }
    if (roleEl) {
      roleEl.textContent = user.role === 'admin' ? 'Administrator' : 'Sustainability Member';
    }
  }

  // Logout button bind
  const logoutBtn = document.querySelector('.btn-logout');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', (e) => {
      e.preventDefault();
      clearAuthSession();
      showToast('Logged out successfully.', 'info');
      setTimeout(() => {
        window.location.href = 'login.html';
      }, 500);
    });
  }
}

document.addEventListener('DOMContentLoaded', initLayout);
