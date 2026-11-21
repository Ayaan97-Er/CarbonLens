/**
 * CARBONLENS — AUTHENTICATION HANDLERS
 */

function requireAuth() {
  const token = getAuthToken();
  if (!token) {
    window.location.href = 'login.html';
  }
}

function redirectIfAuth() {
  const token = getAuthToken();
  if (token) {
    window.location.href = 'dashboard.html';
  }
}

// Login Form Handling
function initLoginForm() {
  const form = document.getElementById('login-form');
  const alertEl = document.getElementById('auth-alert');
  const btnSubmit = document.getElementById('btn-login-submit');

  if (!form) return;

  // Check URL params for expired notice or registration success
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('expired')) {
    showAlert('Your session has expired. Please sign in again.', 'error');
  } else if (urlParams.get('registered')) {
    showAlert('Account created successfully! Please sign in.', 'success');
  }

  // Demo user button helper
  const btnDemo = document.getElementById('btn-demo-fill');
  if (btnDemo) {
    btnDemo.addEventListener('click', () => {
      document.getElementById('email').value = 'demo@carbonlens.dev';
      document.getElementById('password').value = 'CarbonLens2026!';
      showAlert('Demo credentials filled. Click "Sign In" to proceed.', 'success');
    });
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideAlert();

    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    if (!email || !password) {
      showAlert('Please enter both email and password.', 'error');
      return;
    }

    setButtonLoading(btnSubmit, true, 'Signing in...');

    try {
      const data = await apiFetch('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
      });

      setAuthToken(data.access_token);
      setStoredUser(data.user);
      showToast(`Welcome back, ${data.user.full_name}!`, 'success');

      setTimeout(() => {
        window.location.href = 'dashboard.html';
      }, 500);
    } catch (err) {
      setButtonLoading(btnSubmit, false, 'Sign In');
      showAlert(err.message || 'Invalid email or password.', 'error');
    }
  });

  function showAlert(msg, type = 'error') {
    if (!alertEl) return;
    alertEl.textContent = msg;
    alertEl.className = `auth-alert show auth-alert-${type}`;
  }

  function hideAlert() {
    if (!alertEl) return;
    alertEl.className = 'auth-alert';
  }
}

// Registration Form Handling
function initRegisterForm() {
  const form = document.getElementById('register-form');
  const alertEl = document.getElementById('auth-alert');
  const btnSubmit = document.getElementById('btn-register-submit');

  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideAlert();

    const fullName = document.getElementById('full_name').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm_password').value;
    const handle = document.getElementById('public_handle') ? document.getElementById('public_handle').value.trim() : null;

    if (!fullName || !email || !password) {
      showAlert('Please fill in all required fields.', 'error');
      return;
    }

    if (password.length < 6) {
      showAlert('Password must be at least 6 characters long.', 'error');
      return;
    }

    if (password !== confirmPassword) {
      showAlert('Passwords do not match. Please re-enter.', 'error');
      return;
    }

    setButtonLoading(btnSubmit, true, 'Creating Account...');

    try {
      const data = await apiFetch('/auth/register', {
        method: 'POST',
        body: JSON.stringify({
          full_name: fullName,
          email,
          password,
          public_handle: handle || null
        })
      });

      setAuthToken(data.access_token);
      setStoredUser(data.user);
      showToast('Account created successfully! Welcome to CarbonLens.', 'success');

      setTimeout(() => {
        window.location.href = 'dashboard.html';
      }, 600);
    } catch (err) {
      setButtonLoading(btnSubmit, false, 'Create Account');
      showAlert(err.message || 'Registration failed. Please try again.', 'error');
    }
  });

  function showAlert(msg, type = 'error') {
    if (!alertEl) return;
    alertEl.textContent = msg;
    alertEl.className = `auth-alert show auth-alert-${type}`;
  }

  function hideAlert() {
    if (!alertEl) return;
    alertEl.className = 'auth-alert';
  }
}

function setButtonLoading(btn, isLoading, text) {
  if (!btn) return;
  btn.disabled = isLoading;
  btn.innerHTML = isLoading 
    ? `<span class="spinner" style="display:inline-block;width:14px;height:14px;border:2px solid #ffffff;border-top-color:transparent;border-radius:50%;animation:spin 0.6s linear infinite;margin-right:6px;"></span> ${text}`
    : text;
}
