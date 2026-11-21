/**
 * CARBONLENS — WHAT-IF SIMULATION LABORATORY
 */

let simulationCategories = [];

async function initSimulatorPage() {
  requireAuth();

  await loadSimulatorCategories();
  await loadPresets();
  bindSimulationControls();

  // Run initial simulation calculation
  runSimulation();
}

async function loadSimulatorCategories() {
  try {
    simulationCategories = await apiFetch('/categories');
    const selectEl = document.getElementById('sim_activity_type');
    if (!selectEl) return;

    let html = '';
    simulationCategories.forEach(cat => {
      if (cat.emission_factors && cat.emission_factors.length > 0) {
        html += `<optgroup label="${cat.name}">`;
        cat.emission_factors.forEach(f => {
          html += `<option value="${f.activity_type}" data-unit="${f.unit}" data-factor="${f.factor}">${f.activity_type} (${f.unit})</option>`;
        });
        html += `</optgroup>`;
      }
    });

    selectEl.innerHTML = html;
  } catch (err) {
    console.error('Failed to load simulator categories:', err);
  }
}

async function loadPresets() {
  const container = document.getElementById('simulator-presets-container');
  if (!container) return;

  try {
    const presets = await apiFetch('/simulator/presets');
    container.innerHTML = presets.map(p => `
      <div class="card preset-card" style="cursor: pointer; padding: 16px; border: 1px solid var(--border-color); border-radius: var(--radius-md); background: var(--bg-card); transition: all var(--transition-fast);" onclick="applyPreset('${p.activity_type}', ${p.default_quantity}, ${p.default_reduction_pct})">
        <div style="font-weight: 700; font-size: 14px; color: var(--text-main); margin-bottom: 4px;">${p.title}</div>
        <p style="font-size: 12.5px; color: var(--text-muted); margin-bottom: 8px;">${p.description}</p>
        <span class="badge badge-info" style="font-size: 11px;">Reduce ${p.default_reduction_pct}% of ${p.default_quantity} ${p.unit}</span>
      </div>
    `).join('');
  } catch (e) {
    console.error('Failed to load presets:', e);
  }
}

function applyPreset(activityType, quantity, reductionPct) {
  const typeSelect = document.getElementById('sim_activity_type');
  const qtySlider = document.getElementById('sim_quantity');
  const redSlider = document.getElementById('sim_reduction_pct');

  if (typeSelect) typeSelect.value = activityType;
  if (qtySlider) qtySlider.value = quantity;
  if (redSlider) redSlider.value = reductionPct;

  updateSliderLabels();
  runSimulation();
  showToast(`Applied preset: ${activityType}`, 'info');
}

function bindSimulationControls() {
  const typeSelect = document.getElementById('sim_activity_type');
  const qtySlider = document.getElementById('sim_quantity');
  const redSlider = document.getElementById('sim_reduction_pct');

  if (typeSelect) {
    typeSelect.addEventListener('change', () => {
      updateSliderLabels();
      runSimulation();
    });
  }

  if (qtySlider) {
    qtySlider.addEventListener('input', () => {
      updateSliderLabels();
      runSimulation();
    });
  }

  if (redSlider) {
    redSlider.addEventListener('input', () => {
      updateSliderLabels();
      runSimulation();
    });
  }
}

function updateSliderLabels() {
  const typeSelect = document.getElementById('sim_activity_type');
  const qtySlider = document.getElementById('sim_quantity');
  const redSlider = document.getElementById('sim_reduction_pct');

  const selectedOpt = typeSelect ? typeSelect.options[typeSelect.selectedIndex] : null;
  const unit = selectedOpt ? selectedOpt.dataset.unit || 'units' : 'units';

  const qtyLabel = document.getElementById('sim-qty-display');
  const redLabel = document.getElementById('sim-red-display');

  if (qtyLabel && qtySlider) qtyLabel.textContent = `${qtySlider.value} ${unit} / month`;
  if (redLabel && redSlider) redLabel.textContent = `${redSlider.value}% reduction`;
}

async function runSimulation() {
  const typeSelect = document.getElementById('sim_activity_type');
  const qtySlider = document.getElementById('sim_quantity');
  const redSlider = document.getElementById('sim_reduction_pct');

  if (!typeSelect || !qtySlider || !redSlider) return;

  const activityType = typeSelect.value;
  const quantity = parseFloat(qtySlider.value);
  const reductionPct = parseFloat(redSlider.value);

  if (!activityType || !quantity || !reductionPct) return;

  try {
    const result = await apiFetch('/simulator/calculate', {
      method: 'POST',
      body: JSON.stringify({
        activity_type: activityType,
        current_quantity: quantity,
        reduction_percentage: reductionPct
      })
    });

    renderSimulationResults(result);
  } catch (err) {
    console.error('Simulation calculation failed:', err);
  }
}

function renderSimulationResults(res) {
  const baseCo2El = document.getElementById('sim-base-co2');
  const projCo2El = document.getElementById('sim-proj-co2');
  const saveMoEl = document.getElementById('sim-saved-monthly');
  const saveYrEl = document.getElementById('sim-saved-annual');
  const treesEl = document.getElementById('sim-trees-val');
  const carKmEl = document.getElementById('sim-carkm-val');
  const tipEl = document.getElementById('sim-action-tip');

  if (baseCo2El) baseCo2El.textContent = `${formatKg(res.current_monthly_emissions_kg)} kg`;
  if (projCo2El) projCo2El.textContent = `${formatKg(res.projected_monthly_emissions_kg)} kg`;
  if (saveMoEl) saveMoEl.textContent = `${formatKg(res.monthly_emissions_saved_kg)} kg/mo`;
  if (saveYrEl) saveYrEl.textContent = `${formatKg(res.annual_emissions_saved_kg)} kg/year`;

  if (treesEl) treesEl.textContent = `${res.trees_equivalent_annual} trees`;
  if (carKmEl) carKmEl.textContent = `${Number(res.car_km_equivalent_annual).toLocaleString()} km`;
  if (tipEl) tipEl.textContent = res.action_tip;
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('sim_activity_type')) {
    initSimulatorPage();
  }
});
