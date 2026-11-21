/**
 * CARBONLENS — GOALS & CARBON BUDGET CONTROLLER
 */

async function initGoalsPage() {
  requireAuth();
  await loadCurrentGoalProgress();
  await loadGoalsHistory();
  bindGoalForm();
}

async function loadCurrentGoalProgress() {
  const container = document.getElementById('active-goal-container');
  if (!container) return;

  try {
    const data = await apiFetch('/goals/current');

    if (!data.has_active_goal) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">🎯</div>
          <h3 class="empty-state-title">No Monthly Carbon Budget Active</h3>
          <p class="empty-state-desc">Setting a monthly emissions ceiling gives you a clear target to guide your sustainable daily choices.</p>
          <a href="#set-goal-card" class="btn btn-primary">Set Your Target Below</a>
        </div>
      `;
      return;
    }

    const pctUsed = Math.min(100, data.percentage_used || 0);
    const badgeClass = data.status === 'on_track' ? 'badge-success' : data.status === 'caution' ? 'badge-warning' : 'badge-danger';
    const fillBg = data.status === 'exceeded' ? '#e11d48' : data.status === 'caution' ? '#d97706' : '#10b981';

    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
        <div>
          <span class="badge ${badgeClass}" style="margin-bottom: 8px;">
            ${data.status === 'on_track' ? '✓ On Track' : data.status === 'caution' ? '⚠ Caution' : '✕ Target Exceeded'}
          </span>
          <h3 style="font-size: 1.5rem; font-weight: 800; color: var(--text-main);">
            ${formatKg(data.current_month_emissions)} <span style="font-size: 15px; color: var(--text-muted); font-weight: 500;">/ ${formatKg(data.monthly_target)} kg CO₂e</span>
          </h3>
        </div>
        <div style="text-align: right;">
          <div style="font-size: 12px; text-transform: uppercase; color: var(--text-muted); font-weight: 700;">Remaining Budget</div>
          <strong style="font-size: 1.35rem; color: ${data.remaining_budget >= 0 ? '#059669' : '#e11d48'};">
            ${data.remaining_budget >= 0 ? formatKg(data.remaining_budget) + ' kg' : '+' + formatKg(Math.abs(data.remaining_budget)) + ' kg over'}
          </strong>
        </div>
      </div>

      <div style="margin-bottom: 16px;">
        <div class="progress-track" style="height: 12px;">
          <div class="progress-fill" style="width: ${pctUsed}%; background-color: ${fillBg};"></div>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 12px; color: var(--text-muted); margin-top: 6px;">
          <span>0 kg</span>
          <span>${data.percentage_used}% Consumed</span>
          <span>${formatKg(data.monthly_target)} kg Ceiling</span>
        </div>
      </div>

      <div style="background: var(--bg-surface-subtle); border-radius: var(--radius-md); padding: 14px 18px; border-left: 4px solid ${fillBg}; font-size: 13.5px;">
        ${data.status_message}
      </div>
    `;

    // Pre-fill target in form
    const targetInput = document.getElementById('monthly_target');
    if (targetInput && data.monthly_target) {
      targetInput.value = data.monthly_target;
    }
  } catch (err) {
    console.error('Failed to load goal progress:', err);
    showToast('Failed to load active carbon goal.', 'error');
  }
}

let cachedGoals = [];

async function loadGoalsHistory() {
  const tableBody = document.getElementById('goals-history-table-body');
  if (!tableBody) return;

  try {
    const goals = await apiFetch('/goals/history');
    cachedGoals = goals;
    if (goals.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 24px; color: var(--text-muted);">No historical targets set yet.</td></tr>`;
      return;
    }

    tableBody.innerHTML = goals.map(g => `
      <tr>
        <td><strong>${formatDate(g.created_at)}</strong></td>
        <td><strong>${formatKg(g.monthly_target)} kg CO₂e</strong></td>
        <td>${formatDate(g.start_date)}</td>
        <td>
          <span class="badge ${g.is_active ? 'badge-success' : 'badge-neutral'}">
            ${g.is_active ? 'Active' : 'Completed'}
          </span>
        </td>
        <td style="text-align: right; white-space: nowrap;">
          <button class="btn btn-secondary btn-sm" onclick="openEditGoalModal(${g.id})" style="padding: 4px 10px; font-size: 12px; margin-right: 6px;">
            ✏️ Edit
          </button>
          <button class="btn btn-sm" onclick="confirmDeleteGoal(${g.id})" style="padding: 4px 10px; font-size: 12px; background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5;">
            🗑️ Delete
          </button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    console.error('Failed to load goals history:', err);
  }
}

function openEditGoalModal(goalId) {
  const goal = cachedGoals.find(g => g.id === goalId);
  if (!goal) return;

  document.getElementById('edit-goal-id').value = goal.id;
  document.getElementById('edit-monthly-target').value = goal.monthly_target;
  document.getElementById('edit-start-date').value = goal.start_date || '';

  const modal = document.getElementById('edit-goal-modal');
  if (modal) {
    modal.style.display = 'flex';
  }
}

function closeEditGoalModal() {
  const modal = document.getElementById('edit-goal-modal');
  if (modal) {
    modal.style.display = 'none';
  }
}

async function confirmDeleteGoal(goalId) {
  if (!confirm('Are you sure you want to delete this target?')) return;

  try {
    await apiFetch(`/goals/${goalId}`, { method: 'DELETE' });
    showToast('Target deleted successfully.', 'success');
    await loadCurrentGoalProgress();
    await loadGoalsHistory();
  } catch (err) {
    showToast(err.message || 'Failed to delete target.', 'error');
  }
}

function bindGoalForm() {
  const form = document.getElementById('set-goal-form');
  if (form) {
    // Preset buttons
    const presetBtns = document.querySelectorAll('.btn-preset-goal');
    presetBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const targetVal = btn.dataset.target;
        document.getElementById('monthly_target').value = targetVal;
      });
    });

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = document.getElementById('btn-save-goal');
      const targetVal = parseFloat(document.getElementById('monthly_target').value);

      if (!targetVal || targetVal <= 0) {
        showToast('Please specify a positive monthly carbon target.', 'error');
        return;
      }

      setButtonLoading(btn, true, 'Saving Target...');

      try {
        await apiFetch('/goals', {
          method: 'POST',
          body: JSON.stringify({
            monthly_target: targetVal,
            start_date: new Date().toISOString().split('T')[0]
          })
        });

        showToast('Monthly carbon target updated successfully!', 'success');
        await loadCurrentGoalProgress();
        await loadGoalsHistory();
      } catch (err) {
        showToast(err.message || 'Failed to update goal.', 'error');
      } finally {
        setButtonLoading(btn, false, 'Update Carbon Target');
      }
    });
  }

  // Edit Goal modal events
  const editForm = document.getElementById('edit-goal-form');
  if (editForm) {
    editForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const goalId = document.getElementById('edit-goal-id').value;
      const targetVal = parseFloat(document.getElementById('edit-monthly-target').value);
      const startDate = document.getElementById('edit-start-date').value;
      const btn = document.getElementById('btn-submit-edit-goal');

      if (!targetVal || targetVal <= 0) {
        showToast('Please provide a valid monthly target limit.', 'error');
        return;
      }

      setButtonLoading(btn, true, 'Saving...');

      try {
        await apiFetch(`/goals/${goalId}`, {
          method: 'PUT',
          body: JSON.stringify({
            monthly_target: targetVal,
            start_date: startDate
          })
        });

        showToast('Target updated successfully!', 'success');
        closeEditGoalModal();
        await loadCurrentGoalProgress();
        await loadGoalsHistory();
      } catch (err) {
        showToast(err.message || 'Failed to update target.', 'error');
      } finally {
        setButtonLoading(btn, false, 'Save Changes');
      }
    });
  }

  const btnClose = document.getElementById('btn-close-edit-goal');
  if (btnClose) btnClose.addEventListener('click', closeEditGoalModal);

  const btnCancel = document.getElementById('btn-cancel-edit-goal');
  if (btnCancel) btnCancel.addEventListener('click', closeEditGoalModal);

  // Close on outside click
  const modal = document.getElementById('edit-goal-modal');
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeEditGoalModal();
    });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('active-goal-container')) {
    initGoalsPage();
  }
});
