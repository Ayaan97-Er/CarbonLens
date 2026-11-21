/**
 * CARBONLENS — ACTIVITIES MANAGEMENT CONTROLLER
 */

let categoriesData = [];
let currentPage = 1;
const pageSize = 12;
let activeDeleteId = null;
let activeEditId = null;

async function initActivitiesPage() {
  requireAuth();

  // Set default activity date to today
  const today = new Date().toISOString().split('T')[0];
  const dateInput = document.getElementById('activity_date');
  if (dateInput) dateInput.value = today;

  await loadCategories();
  await loadActivitiesTable();

  // Bind Form Events
  bindActivityFormEvents();
  bindFilterEvents();
}

async function loadCategories() {
  try {
    categoriesData = await apiFetch('/categories');
    
    // Populate form category select
    const formCatSelect = document.getElementById('category_id');
    const filterCatSelect = document.getElementById('filter_category');

    if (formCatSelect) {
      formCatSelect.innerHTML = '<option value="">Select Category...</option>' + 
        categoriesData.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
    }

    if (filterCatSelect) {
      filterCatSelect.innerHTML = '<option value="">All Categories</option>' + 
        categoriesData.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
    }
  } catch (err) {
    console.error('Failed to load categories:', err);
    showToast('Failed to load activity categories.', 'error');
  }
}

function bindActivityFormEvents() {
  const form = document.getElementById('add-activity-form');
  const catSelect = document.getElementById('category_id');
  const typeSelect = document.getElementById('activity_type');
  const qtyInput = document.getElementById('quantity');
  const unitLabel = document.getElementById('unit-label');
  const previewBox = document.getElementById('co2-live-preview');

  if (catSelect && typeSelect) {
    catSelect.addEventListener('change', () => {
      const catId = parseInt(catSelect.value);
      const cat = categoriesData.find(c => c.id === catId);

      if (cat && cat.emission_factors) {
        typeSelect.innerHTML = '<option value="">Select Activity Type...</option>' +
          cat.emission_factors.map(f => `<option value="${f.activity_type}" data-unit="${f.unit}" data-factor="${f.factor}">${f.activity_type} (${f.unit})</option>`).join('');
        typeSelect.disabled = false;
      } else {
        typeSelect.innerHTML = '<option value="">Select Category first...</option>';
        typeSelect.disabled = true;
      }
      updatePreview();
    });

    typeSelect.addEventListener('change', () => {
      const selectedOption = typeSelect.options[typeSelect.selectedIndex];
      if (selectedOption && selectedOption.dataset.unit) {
        if (unitLabel) unitLabel.textContent = selectedOption.dataset.unit;
      }
      updatePreview();
    });

    if (qtyInput) {
      qtyInput.addEventListener('input', updatePreview);
    }
  }

  async function updatePreview() {
    if (!previewBox) return;
    const activityType = typeSelect ? typeSelect.value : '';
    const quantity = qtyInput ? parseFloat(qtyInput.value) : 0;
    const catId = catSelect ? parseInt(catSelect.value) : null;

    if (activityType && quantity > 0) {
      try {
        const preview = await apiFetch(`/activities/preview?activity_type=${encodeURIComponent(activityType)}&quantity=${quantity}&category_id=${catId || ''}`);
        previewBox.innerHTML = `
          <div style="background: #f0fdf4; border: 1px solid #bbf7d0; padding: 12px 16px; border-radius: var(--radius-md); display: flex; align-items: center; justify-content: space-between;">
            <div>
              <span style="font-size: 13px; color: #166534; font-weight: 600;">Estimated Impact:</span>
              <strong style="font-size: 16px; color: #15803d; margin-left: 6px;">${preview.calculated_co2_kg} kg CO₂e</strong>
            </div>
            <span style="font-size: 11.5px; color: #166534; background: #dcfce7; padding: 2px 8px; border-radius: var(--radius-full);">
              Factor: ${preview.emission_factor} kg/${preview.unit}
            </span>
          </div>
        `;
      } catch (e) {
        // Fallback preview
        const opt = typeSelect.options[typeSelect.selectedIndex];
        const factor = opt && opt.dataset.factor ? parseFloat(opt.dataset.factor) : 0.15;
        const est = (quantity * factor).toFixed(2);
        previewBox.innerHTML = `
          <div style="background: #f0fdf4; border: 1px solid #bbf7d0; padding: 12px 16px; border-radius: var(--radius-md);">
            <span style="font-size: 13px; color: #166534; font-weight: 600;">Estimated Impact: </span>
            <strong style="font-size: 16px; color: #15803d;">${est} kg CO₂e</strong>
          </div>
        `;
      }
    } else {
      previewBox.innerHTML = '';
    }
  }

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = document.getElementById('btn-submit-activity');
      const catId = parseInt(document.getElementById('category_id').value);
      const activityType = document.getElementById('activity_type').value;
      const quantity = parseFloat(document.getElementById('quantity').value);
      const selectedOption = typeSelect.options[typeSelect.selectedIndex];
      const unit = selectedOption ? selectedOption.dataset.unit || 'unit' : 'unit';
      const activityDate = document.getElementById('activity_date').value;
      const notes = document.getElementById('notes').value;

      if (!catId || !activityType || !quantity || !activityDate) {
        showToast('Please fill all required fields.', 'error');
        return;
      }

      setButtonLoading(btn, true, 'Logging...');

      try {
        await apiFetch('/activities', {
          method: 'POST',
          body: JSON.stringify({
            category_id: catId,
            activity_type: activityType,
            quantity,
            unit,
            activity_date: activityDate,
            notes: notes || null
          })
        });

        showToast('Activity successfully logged!', 'success');
        form.reset();
        document.getElementById('activity_date').value = new Date().toISOString().split('T')[0];
        if (unitLabel) unitLabel.textContent = 'Units';
        if (previewBox) previewBox.innerHTML = '';
        typeSelect.disabled = true;

        await loadActivitiesTable();
      } catch (err) {
        showToast(err.message || 'Failed to log activity.', 'error');
      } finally {
        setButtonLoading(btn, false, 'Record Activity');
      }
    });
  }
}

function bindFilterEvents() {
  const searchInput = document.getElementById('filter_search');
  const catFilter = document.getElementById('filter_category');
  const startDate = document.getElementById('filter_start_date');
  const endDate = document.getElementById('filter_end_date');
  const btnReset = document.getElementById('btn-reset-filters');

  const triggerFilter = () => {
    currentPage = 1;
    loadActivitiesTable();
  };

  if (searchInput) searchInput.addEventListener('input', debounce(triggerFilter, 300));
  if (catFilter) catFilter.addEventListener('change', triggerFilter);
  if (startDate) startDate.addEventListener('change', triggerFilter);
  if (endDate) endDate.addEventListener('change', triggerFilter);

  if (btnReset) {
    btnReset.addEventListener('click', () => {
      if (searchInput) searchInput.value = '';
      if (catFilter) catFilter.value = '';
      if (startDate) startDate.value = '';
      if (endDate) endDate.value = '';
      triggerFilter();
    });
  }
}

async function loadActivitiesTable() {
  const tableBody = document.getElementById('activities-table-body');
  const paginationEl = document.getElementById('activities-pagination');
  const statsSummaryEl = document.getElementById('activities-summary-stats');
  if (!tableBody) return;

  const catFilter = document.getElementById('filter_category')?.value || '';
  const search = document.getElementById('filter_search')?.value || '';
  const startDate = document.getElementById('filter_start_date')?.value || '';
  const endDate = document.getElementById('filter_end_date')?.value || '';

  let query = `/activities?page=${currentPage}&page_size=${pageSize}`;
  if (catFilter) query += `&category_id=${catFilter}`;
  if (search) query += `&search=${encodeURIComponent(search)}`;
  if (startDate) query += `&start_date=${startDate}`;
  if (endDate) query += `&end_date=${endDate}`;

  try {
    const data = await apiFetch(query);

    if (statsSummaryEl) {
      statsSummaryEl.textContent = `Showing ${data.items.length} of ${data.total} logged activities (${formatKg(data.total_emissions_kg)} kg CO₂e tracked)`;
    }

    if (data.items.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="6">
            <div class="empty-state">
              <div class="empty-state-icon">🌱</div>
              <h3 class="empty-state-title">No activities found</h3>
              <p class="empty-state-desc">No activities match your current filter or date range. Log a new activity above!</p>
            </div>
          </td>
        </tr>
      `;
      if (paginationEl) paginationEl.innerHTML = '';
      return;
    }

    tableBody.innerHTML = data.items.map(act => `
      <tr>
        <td><strong>${formatDate(act.activity_date)}</strong></td>
        <td><span class="badge badge-neutral">${act.category ? act.category.name : 'Other'}</span></td>
        <td>
          <div style="font-weight: 600; color: var(--text-main);">${act.activity_type}</div>
          ${act.notes ? `<div style="font-size: 12px; color: var(--text-muted);">${act.notes}</div>` : ''}
        </td>
        <td>${act.quantity} ${act.unit}</td>
        <td><strong style="color: #059669;">${formatKg(act.calculated_co2)} kg</strong></td>
        <td>
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-secondary btn-sm" onclick="openEditModal(${act.id})">Edit</button>
            <button class="btn btn-secondary btn-sm" style="color: #e11d48;" onclick="openDeleteModal(${act.id})">Delete</button>
          </div>
        </td>
      </tr>
    `).join('');

    renderPagination(data.total_pages, data.page);
  } catch (err) {
    console.error('Failed to load activities:', err);
    showToast('Failed to load activities.', 'error');
  }
}

function renderPagination(totalPages, page) {
  const container = document.getElementById('activities-pagination');
  if (!container || totalPages <= 1) {
    if (container) container.innerHTML = '';
    return;
  }

  container.innerHTML = `
    <div style="display: flex; align-items: center; justify-content: center; gap: 8px; margin-top: 20px;">
      <button class="btn btn-secondary btn-sm" ${page <= 1 ? 'disabled' : ''} onclick="changePage(${page - 1})">Previous</button>
      <span style="font-size: 13px; color: var(--text-muted); font-weight: 600;">Page ${page} of ${totalPages}</span>
      <button class="btn btn-secondary btn-sm" ${page >= totalPages ? 'disabled' : ''} onclick="changePage(${page + 1})">Next</button>
    </div>
  `;
}

function changePage(newPage) {
  currentPage = newPage;
  loadActivitiesTable();
}

// Delete Activity
function openDeleteModal(id) {
  activeDeleteId = id;
  const modal = document.getElementById('delete-modal');
  if (modal) modal.classList.add('active');
}

function closeDeleteModal() {
  activeDeleteId = null;
  const modal = document.getElementById('delete-modal');
  if (modal) modal.classList.remove('active');
}

async function confirmDeleteActivity() {
  if (!activeDeleteId) return;
  try {
    await apiFetch(`/activities/${activeDeleteId}`, { method: 'DELETE' });
    showToast('Activity removed.', 'success');
    closeDeleteModal();
    loadActivitiesTable();
  } catch (err) {
    showToast(err.message || 'Failed to delete activity.', 'error');
  }
}

// Edit Activity
async function openEditModal(id) {
  activeEditId = id;
  try {
    const act = await apiFetch(`/activities/${id}`);
    document.getElementById('edit_quantity').value = act.quantity;
    document.getElementById('edit_notes').value = act.notes || '';
    document.getElementById('edit_activity_date').value = act.activity_date;
    document.getElementById('edit-activity-title').textContent = `Edit ${act.activity_type}`;
    document.getElementById('edit-unit-label').textContent = act.unit;

    const modal = document.getElementById('edit-modal');
    if (modal) modal.classList.add('active');
  } catch (err) {
    showToast('Failed to load activity details for editing.', 'error');
  }
}

function closeEditModal() {
  activeEditId = null;
  const modal = document.getElementById('edit-modal');
  if (modal) modal.classList.remove('active');
}

async function saveEditActivity() {
  if (!activeEditId) return;
  const qty = parseFloat(document.getElementById('edit_quantity').value);
  const notes = document.getElementById('edit_notes').value;
  const actDate = document.getElementById('edit_activity_date').value;

  if (!qty || !actDate) {
    showToast('Please provide quantity and date.', 'error');
    return;
  }

  try {
    await apiFetch(`/activities/${activeEditId}`, {
      method: 'PUT',
      body: JSON.stringify({
        quantity: qty,
        activity_date: actDate,
        notes: notes || null
      })
    });

    showToast('Activity updated successfully!', 'success');
    closeEditModal();
    loadActivitiesTable();
  } catch (err) {
    showToast(err.message || 'Failed to update activity.', 'error');
  }
}

function debounce(fn, delay) {
  let timer = null;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('activities-table-body')) {
    initActivitiesPage();
  }
});
