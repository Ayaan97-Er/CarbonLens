/**
 * CARBONLENS — DASHBOARD & NATURE ANALYTICS CONTROLLER
 */

let trendChartInstance = null;
let categoryChartInstance = null;
let dailyChartInstance = null;

async function loadDashboard() {
  requireAuth();

  const user = getStoredUser();
  if (user) {
    const greetingEl = document.getElementById('user-greeting');
    if (greetingEl) {
      greetingEl.textContent = user.full_name.split(' ')[0];
    }
  }

  // Set current date display
  const dateEl = document.getElementById('hero-date-display');
  if (dateEl) {
    const now = new Date();
    dateEl.textContent = now.toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
  }

  try {
    const data = await apiFetch('/dashboard/summary');
    renderMetrics(data);
    renderCharts(data);
    renderScoreWidget(data.sustainability_score);
    renderRecentActivities(data.recent_activities);
    loadRecommendationsSnippet();
  } catch (err) {
    console.error('Failed to load dashboard:', err);
    showToast('Failed to load dashboard data.', 'error');
  }
}

function renderMetrics(data) {
  // 1. Monthly Total
  const monthlyEl = document.getElementById('metric-monthly-co2');
  if (monthlyEl) monthlyEl.textContent = formatKg(data.total_monthly_emissions);

  // MoM Delta Badge
  const deltaBadge = document.getElementById('metric-mom-delta');
  if (deltaBadge) {
    const pct = data.percentage_change;
    if (pct < 0) {
      deltaBadge.className = 'delta-badge delta-down';
      deltaBadge.innerHTML = `↓ ${Math.abs(pct)}% vs last month`;
    } else if (pct > 0) {
      deltaBadge.className = 'delta-badge delta-up';
      deltaBadge.innerHTML = `↑ ${pct}% vs last month`;
    } else {
      deltaBadge.className = 'delta-badge';
      deltaBadge.textContent = `0% change`;
    }
  }

  // 2. Daily Average
  const dailyAvgEl = document.getElementById('metric-daily-avg');
  if (dailyAvgEl) dailyAvgEl.textContent = formatKg(data.daily_average);

  // 3. Goal Remaining
  const goal = data.goal;
  const goalValEl = document.getElementById('metric-goal-val');
  const goalSubEl = document.getElementById('metric-goal-sub');
  const goalFill = document.getElementById('metric-goal-fill');

  if (goalValEl && goal) {
    if (goal.has_active_goal) {
      goalValEl.textContent = `${formatKg(goal.remaining_budget)} kg`;
      if (goalSubEl) {
        goalSubEl.textContent = `of ${formatKg(goal.monthly_target)} kg target (${goal.percentage_used}% used)`;
      }
      if (goalFill) {
        const fillWidth = Math.min(100, goal.percentage_used || 0);
        goalFill.style.width = `${fillWidth}%`;
        goalFill.style.backgroundColor = fillWidth > 100 ? '#e76f51' : fillWidth > 80 ? '#f4a261' : '#52b788';
      }
    } else {
      goalValEl.textContent = 'No Target';
      if (goalSubEl) goalSubEl.textContent = 'Click to set a monthly target';
    }
  }
}

function renderCharts(data) {
  // 1. Monthly Trend Chart
  const trendCtx = document.getElementById('trendChart');
  if (trendCtx && data.monthly_trend) {
    if (trendChartInstance) trendChartInstance.destroy();

    const labels = data.monthly_trend.map(d => d.month_str);
    const values = data.monthly_trend.map(d => d.total_co2);
    const targets = data.monthly_trend.map(d => d.target_co2 || null);

    trendChartInstance = new Chart(trendCtx, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: 'Monthly Emissions (kg CO₂e)',
            data: values,
            backgroundColor: 'rgba(82, 183, 136, 0.85)',
            borderColor: '#2d6a4f',
            borderWidth: 1.5,
            borderRadius: 10,
            hoverBackgroundColor: '#2d6a4f',
          },
          ...(targets.some(t => t !== null) ? [{
            label: 'Target Budget Ceiling',
            data: targets,
            type: 'line',
            borderColor: '#f4a261',
            borderDash: [6, 6],
            borderWidth: 2.5,
            pointRadius: 4,
            pointBackgroundColor: '#f4a261',
            fill: false,
          }] : [])
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 12, font: { family: 'Plus Jakarta Sans', size: 12, weight: '600' } } },
          tooltip: {
            backgroundColor: '#172d21',
            padding: 12,
            cornerRadius: 10,
            callbacks: {
              label: (ctx) => ` ${ctx.dataset.label}: ${ctx.raw} kg CO₂e`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: 'kg CO₂e', font: { family: 'Plus Jakarta Sans', size: 11 } },
            grid: { color: '#edf2e9' }
          },
          x: {
            grid: { display: false }
          }
        }
      }
    });
  }

  // 2. Category Breakdown Chart (Doughnut)
  const catCtx = document.getElementById('categoryChart');
  if (catCtx && data.categories_breakdown) {
    if (categoryChartInstance) categoryChartInstance.destroy();

    const categories = data.categories_breakdown;
    const catLabels = categories.map(c => c.category_name);
    const catValues = categories.map(c => c.total_co2);
    const colorPalette = ['#2d6a4f', '#52b788', '#3d7ab8', '#f4a261', '#e76f51', '#74c69d'];

    categoryChartInstance = new Chart(catCtx, {
      type: 'doughnut',
      data: {
        labels: catLabels.length > 0 ? catLabels : ['No Activity'],
        datasets: [{
          data: catValues.length > 0 ? catValues : [1],
          backgroundColor: catValues.length > 0 ? colorPalette.slice(0, catLabels.length) : ['#e4ece0'],
          borderWidth: 3,
          borderColor: '#ffffff',
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 10, font: { family: 'Plus Jakarta Sans', size: 11, weight: '500' } } },
          tooltip: {
            backgroundColor: '#172d21',
            padding: 12,
            cornerRadius: 10,
            callbacks: {
              label: (ctx) => ` ${ctx.label}: ${formatKg(ctx.raw)} kg CO₂e`
            }
          }
        },
        cutout: '70%'
      }
    });
  }

  // 3. Daily Emissions Timeline
  const dailyCtx = document.getElementById('dailyChart');
  if (dailyCtx && data.recent_daily_emissions) {
    if (dailyChartInstance) dailyChartInstance.destroy();

    const dailyLabels = data.recent_daily_emissions.map(d => d.date_str.slice(5)); // MM-DD
    const dailyValues = data.recent_daily_emissions.map(d => d.total_co2);

    dailyChartInstance = new Chart(dailyCtx, {
      type: 'line',
      data: {
        labels: dailyLabels,
        datasets: [{
          label: 'Daily Footprint',
          data: dailyValues,
          borderColor: '#40916c',
          backgroundColor: 'rgba(64, 145, 108, 0.12)',
          fill: true,
          tension: 0.4,
          borderWidth: 2.5,
          pointBackgroundColor: '#2d6a4f',
          pointRadius: 3.5,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#172d21',
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              label: (ctx) => ` Emissions: ${ctx.raw} kg CO₂e`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: '#edf2e9' }
          },
          x: {
            grid: { display: false }
          }
        }
      }
    });
  }
}

function renderScoreWidget(scoreObj) {
  if (!scoreObj) return;

  const numEl = document.getElementById('score-number');
  const ratingEl = document.getElementById('score-rating-badge');
  const descEl = document.getElementById('score-explanation');

  if (numEl) numEl.textContent = scoreObj.score;
  if (ratingEl) {
    ratingEl.textContent = scoreObj.rating;
    ratingEl.className = `badge badge-${scoreObj.score >= 70 ? 'success' : scoreObj.score >= 50 ? 'warning' : 'danger'}`;
  }
  if (descEl) descEl.textContent = scoreObj.explanation;

  // Subcomponents
  const targetBar = document.getElementById('score-bar-target');
  const trendBar = document.getElementById('score-bar-trend');
  const consistencyBar = document.getElementById('score-bar-consistency');
  const mitigationBar = document.getElementById('score-bar-mitigation');

  if (targetBar) targetBar.style.width = `${(scoreObj.target_component / 35) * 100}%`;
  if (trendBar) trendBar.style.width = `${(scoreObj.trend_component / 30) * 100}%`;
  if (consistencyBar) consistencyBar.style.width = `${(scoreObj.consistency_component / 20) * 100}%`;
  if (mitigationBar) mitigationBar.style.width = `${(scoreObj.mitigation_component / 15) * 100}%`;
}

function renderRecentActivities(activities) {
  const container = document.getElementById('recent-activities-table-body');
  if (!container) return;

  if (!activities || activities.length === 0) {
    container.innerHTML = `
      <tr>
        <td colspan="5" style="text-align:center; padding: 36px; color: var(--text-muted);">
          No activities recorded yet. <a href="activities.html" style="font-weight:700; color: var(--primary);">Log your first activity</a> to begin!
        </td>
      </tr>
    `;
    return;
  }

  container.innerHTML = activities.map(act => `
    <tr>
      <td><strong>${formatDate(act.activity_date)}</strong></td>
      <td><span class="badge badge-neutral">${act.category ? act.category.name : 'General'}</span></td>
      <td>${act.activity_type}</td>
      <td>${act.quantity} ${act.unit}</td>
      <td><strong style="color: #2d6a4f; font-family: var(--font-display);">${formatKg(act.calculated_co2)} kg</strong></td>
    </tr>
  `).join('');
}

async function loadRecommendationsSnippet() {
  const container = document.getElementById('recommendations-snippet-container');
  if (!container) return;

  try {
    const data = await apiFetch('/recommendations');
    const recs = data.recommendations.slice(0, 3);

    if (recs.length === 0) {
      container.innerHTML = '<p style="color:var(--text-muted);">Log more activities to generate smart personalized recommendations.</p>';
      return;
    }

    container.innerHTML = recs.map(r => `
      <div class="rec-item-card">
        <div class="rec-icon">🌱</div>
        <div class="rec-body">
          <div class="rec-title-row">
            <span class="rec-title">${r.title}</span>
            <span class="rec-savings-badge">Save ~${r.potential_monthly_savings_kg} kg/mo</span>
          </div>
          <p class="rec-description">${r.description}</p>
          <div class="rec-action-tip">👉 ${r.actionable_step}</div>
        </div>
      </div>
    `).join('');
  } catch (e) {
    console.error('Failed to load recommendations snippet:', e);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('trendChart')) {
    loadDashboard();
  }
});
