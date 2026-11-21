/**
 * CARBONLENS — COMMUNITY LEADERBOARD CONTROLLER
 */

async function initLeaderboardPage() {
  requireAuth();
  await loadLeaderboard();
}

async function loadLeaderboard() {
  const tableBody = document.getElementById('leaderboard-table-body');
  if (!tableBody) return;

  const currentUser = getStoredUser();

  try {
    const data = await apiFetch('/leaderboard');

    if (!data || data.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 32px; color: var(--text-muted);">No leaderboard participants yet.</td></tr>`;
      return;
    }

    tableBody.innerHTML = data.map(entry => {
      const isSelf = currentUser && (entry.display_name === currentUser.public_handle || entry.display_name.startsWith(currentUser.full_name.split(' ')[0]));
      const rankBadge = entry.rank === 1 ? '🥇 1' : entry.rank === 2 ? '🥈 2' : entry.rank === 3 ? '🥉 3' : `#${entry.rank}`;
      
      const tierColor = entry.tier === 'Eco Master' ? 'badge-success' : entry.tier === 'Green Champion' ? 'badge-info' : 'badge-warning';

      return `
        <tr style="${isSelf ? 'background-color: #f0fdf4; font-weight: 600;' : ''}">
          <td><strong style="font-size: 15px;">${rankBadge}</strong></td>
          <td>
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="font-weight: 600; color: var(--text-main);">${entry.display_name}</span>
              ${isSelf ? '<span class="badge badge-success" style="font-size: 10px;">You</span>' : ''}
            </div>
          </td>
          <td>
            <div style="display: flex; align-items: center; gap: 6px;">
              <strong style="font-size: 15px; color: #059669;">${entry.sustainability_score}</strong>
              <span style="font-size: 11px; color: var(--text-muted);">/100</span>
            </div>
          </td>
          <td><span class="badge ${tierColor}">${entry.tier}</span></td>
          <td>${formatKg(entry.monthly_emissions_kg)} kg CO₂e</td>
          <td>
            <span style="color: ${entry.reduction_percentage > 0 ? '#059669' : 'var(--text-muted)'}; font-weight: 600;">
              ${entry.reduction_percentage > 0 ? `↓ ${entry.reduction_percentage}%` : `${entry.reduction_percentage}%`}
            </span>
          </td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    console.error('Failed to load leaderboard:', err);
    showToast('Failed to load community leaderboard.', 'error');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('leaderboard-table-body')) {
    initLeaderboardPage();
  }
});
