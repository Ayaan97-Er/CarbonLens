/**
 * CARBONLENS — USER PROFILE & DATA EXPORT CONTROLLER
 */

async function initProfilePage() {
  requireAuth();
  await loadProfile();
  bindProfileForm();
  bindPasswordForm();
  bindExportButtons();
}

async function loadProfile() {
  try {
    const user = await apiFetch('/auth/me');
    setStoredUser(user);

    document.getElementById('profile_full_name').value = user.full_name || '';
    document.getElementById('profile_email').value = user.email || '';
    document.getElementById('profile_handle').value = user.public_handle || '';
    document.getElementById('profile_opt_in').checked = user.leaderboard_opt_in;

    const roleBadge = document.getElementById('profile-role-badge');
    if (roleBadge) {
      roleBadge.textContent = user.role === 'admin' ? 'Administrator' : 'Standard Member';
      roleBadge.className = `badge ${user.role === 'admin' ? 'badge-info' : 'badge-neutral'}`;
    }

    const memberSince = document.getElementById('profile-member-since');
    if (memberSince) memberSince.textContent = formatDate(user.created_at);
  } catch (err) {
    console.error('Failed to load profile:', err);
    showToast('Failed to load user profile.', 'error');
  }
}

function bindProfileForm() {
  const form = document.getElementById('profile-info-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('btn-save-profile');
    const fullName = document.getElementById('profile_full_name').value.trim();
    const handle = document.getElementById('profile_handle').value.trim();
    const optIn = document.getElementById('profile_opt_in').checked;

    if (!fullName) {
      showToast('Name cannot be blank.', 'error');
      return;
    }

    setButtonLoading(btn, true, 'Saving...');

    try {
      const updatedUser = await apiFetch('/auth/me', {
        method: 'PUT',
        body: JSON.stringify({
          full_name: fullName,
          public_handle: handle || null,
          leaderboard_opt_in: optIn
        })
      });

      setStoredUser(updatedUser);
      showToast('Profile updated successfully!', 'success');
      initLayout();
    } catch (err) {
      showToast(err.message || 'Failed to update profile.', 'error');
    } finally {
      setButtonLoading(btn, false, 'Save Profile Changes');
    }
  });
}

function bindPasswordForm() {
  const form = document.getElementById('change-password-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('btn-change-password');
    const curPass = document.getElementById('current_password').value;
    const newPass = document.getElementById('new_password').value;
    const confirmPass = document.getElementById('confirm_new_password').value;

    if (newPass.length < 6) {
      showToast('New password must be at least 6 characters.', 'error');
      return;
    }

    if (newPass !== confirmPass) {
      showToast('New passwords do not match.', 'error');
      return;
    }

    setButtonLoading(btn, true, 'Updating Password...');

    try {
      await apiFetch('/auth/change-password', {
        method: 'POST',
        body: JSON.stringify({
          current_password: curPass,
          new_password: newPass
        })
      });

      showToast('Password changed successfully!', 'success');
      form.reset();
    } catch (err) {
      showToast(err.message || 'Failed to update password.', 'error');
    } finally {
      setButtonLoading(btn, false, 'Update Password');
    }
  });
}

function bindExportButtons() {
  const btnJson = document.getElementById('btn-export-json');
  const btnCsv = document.getElementById('btn-export-csv');

  if (btnJson) {
    btnJson.addEventListener('click', async () => {
      try {
        const data = await apiFetch('/activities?page_size=1000');
        const jsonStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data.items, null, 2));
        const dlAnchor = document.createElement('a');
        dlAnchor.setAttribute("href", jsonStr);
        dlAnchor.setAttribute("download", `carbonlens_activities_${new Date().toISOString().split('T')[0]}.json`);
        document.body.appendChild(dlAnchor);
        dlAnchor.click();
        dlAnchor.remove();
        showToast('JSON Export downloaded.', 'success');
      } catch (e) {
        showToast('Export failed.', 'error');
      }
    });
  }

  if (btnCsv) {
    btnCsv.addEventListener('click', async () => {
      try {
        const data = await apiFetch('/activities?page_size=1000');
        let csvContent = "data:text/csv;charset=utf-8,ID,Date,Category,Activity,Quantity,Unit,EmissionFactor,CalculatedCO2_kg,Notes\n";
        data.items.forEach(a => {
          const row = [
            a.id,
            a.activity_date,
            `"${a.category ? a.category.name : ''}"`,
            `"${a.activity_type}"`,
            a.quantity,
            a.unit,
            a.emission_factor,
            a.calculated_co2,
            `"${(a.notes || '').replace(/"/g, '""')}"`
          ].join(',');
          csvContent += row + "\n";
        });
        const encodedUri = encodeURI(csvContent);
        const dlAnchor = document.createElement('a');
        dlAnchor.setAttribute("href", encodedUri);
        dlAnchor.setAttribute("download", `carbonlens_activities_${new Date().toISOString().split('T')[0]}.csv`);
        document.body.appendChild(dlAnchor);
        dlAnchor.click();
        dlAnchor.remove();
        showToast('CSV Export downloaded.', 'success');
      } catch (e) {
        showToast('Export failed.', 'error');
      }
    });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('profile_full_name')) {
    initProfilePage();
  }
});
