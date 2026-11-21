/**
 * CARBONLENS — ACHIEVEMENTS & MILESTONES CONTROLLER
 */

async function initAchievementsPage() {
  requireAuth();
  
  // Show active account identification
  const user = getStoredUser();
  if (user) {
    const badgeEl = document.getElementById('account-name-badge');
    const emailEl = document.getElementById('user-account-email');
    if (badgeEl) badgeEl.textContent = `${user.full_name}'s Milestones`;
    if (emailEl) emailEl.textContent = `(${user.email})`;
  }

  await loadAchievements();
}

async function loadAchievements() {
  const container = document.getElementById('achievements-grid');
  const countEl = document.getElementById('unlocked-count');
  const totalEl = document.getElementById('total-count');
  const progressFill = document.getElementById('achievements-progress-fill');
  const pctText = document.getElementById('achievements-pct-text');

  if (!container) return;

  try {
    const data = await apiFetch('/achievements');

    if (countEl) countEl.textContent = data.unlocked_count;
    if (totalEl) totalEl.textContent = data.total_achievements;
    if (progressFill) progressFill.style.width = `${data.completion_percentage}%`;
    if (pctText) pctText.textContent = `${data.completion_percentage}% Completed`;

    container.innerHTML = data.items.map(ach => {
      const isUnlocked = ach.is_unlocked;
      const tierColor = ach.badge_tier === 'emerald' ? '#059669' : ach.badge_tier === 'gold' ? '#d97706' : ach.badge_tier === 'silver' ? '#64748b' : '#b45309';
      const iconSymbol = ach.icon === 'footprints' ? '👣' : ach.icon === 'calendar-check' ? '📅' : ach.icon === 'database' ? '📊' : ach.icon === 'shield-check' ? '🛡️' : ach.icon === 'trending-down' ? '📉' : ach.icon === 'bike' ? '🚲' : ach.icon === 'sprout' ? '🌱' : '🏆';

      return `
        <div class="card" style="position: relative; opacity: ${isUnlocked ? '1' : '0.75'}; border: 1px solid ${isUnlocked ? 'rgba(16, 185, 129, 0.4)' : 'var(--border-color)'}; background: ${isUnlocked ? '#ffffff' : '#f8fafc'};">
          <div style="display: flex; gap: 16px; align-items: flex-start;">
            <div style="width: 52px; height: 52px; border-radius: var(--radius-md); background: ${isUnlocked ? 'var(--primary-light)' : '#e2e8f0'}; display: flex; align-items: center; justify-content: center; font-size: 26px; flex-shrink: 0; box-shadow: ${isUnlocked ? '0 4px 12px rgba(16, 185, 129, 0.25)' : 'none'};">
              ${iconSymbol}
            </div>
            <div style="flex: 1;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <h4 style="font-size: 15px; font-weight: 700; color: var(--text-main);">${ach.name}</h4>
                <span class="badge" style="background: ${isUnlocked ? '#d1fae5' : '#f1f5f9'}; color: ${isUnlocked ? '#065f46' : '#64748b'}; text-transform: capitalize;">
                  ${ach.badge_tier}
                </span>
              </div>
              <p style="font-size: 13px; color: var(--text-muted); line-height: 1.4; margin-bottom: 12px;">${ach.description}</p>
              
              ${isUnlocked ? `
                <div style="display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600; color: #059669;">
                  <span>✓ Unlocked</span>
                  <span style="color: var(--text-light);">• ${formatDate(ach.unlocked_at)}</span>
                </div>
              ` : `
                <div>
                  <div style="display: flex; justify-content: space-between; font-size: 11.5px; color: var(--text-muted); margin-bottom: 4px;">
                    <span>Progress: ${ach.current_progress} / ${ach.requirement_value}</span>
                    <span>${ach.progress_percentage}%</span>
                  </div>
                  <div class="progress-track" style="height: 6px;">
                    <div class="progress-fill" style="width: ${ach.progress_percentage}%; background-color: #94a3b8;"></div>
                  </div>
                </div>
              `}
            </div>
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    console.error('Failed to load achievements:', err);
    showToast('Failed to load achievements list.', 'error');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('achievements-grid')) {
    initAchievementsPage();
  }
});
