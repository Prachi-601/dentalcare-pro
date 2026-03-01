// ═══════════════════════════════════════════════════
//   DentalCare Pro – Main JavaScript
// ═══════════════════════════════════════════════════

const THEME_KEY = 'dentalcare_theme';

// ─── APPLY THEME ────────────────────────────────────
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  const icon = document.getElementById('theme-icon');
  if (icon) icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
}

// ─── TOGGLE THEME ───────────────────────────────────
function toggleTheme() {
  const curr = document.documentElement.getAttribute('data-theme') || 'light';
  const next = curr === 'dark' ? 'light' : 'dark';
  localStorage.setItem(THEME_KEY, next);
  applyTheme(next);
}

// Apply on load immediately (prevents flash)
// Default is always LIGHT — only switch to dark if user has explicitly chosen it
(function () {
  const saved = localStorage.getItem(THEME_KEY);
  applyTheme(saved === 'dark' ? 'dark' : 'light');
})();


// ─── PASSWORD VISIBILITY TOGGLE ─────────────────────
function togglePw(inputId, iconId) {
  const input = document.getElementById(inputId);
  const icon  = document.getElementById(iconId);
  if (!input) return;
  if (input.type === 'password') {
    input.type = 'text';
    if (icon) icon.className = 'fas fa-eye-slash';
  } else {
    input.type = 'password';
    if (icon) icon.className = 'fas fa-eye';
  }
}


// ─── TOAST NOTIFICATION ─────────────────────────────
function showToast(msg, type = 'info') {
  const div = document.createElement('div');
  div.className = `alert alert-${type}`;
  div.style.cssText = 'position:fixed;top:1rem;right:1rem;z-index:9999;min-width:280px;animation:fadeIn .3s';
  div.innerHTML = `<i class="fas fa-info-circle"></i><span>${msg}</span>`;
  document.body.appendChild(div);
  setTimeout(() => { div.style.opacity = '0'; div.style.transition = 'opacity .4s'; setTimeout(() => div.remove(), 400); }, 3500);
}


// ─── AUTO-DISMISS FLASH MESSAGES ────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.alert').forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity .5s';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 500);
    }, 5000);
  });

  // Default appointment date to today if blank
  const dateInp = document.querySelector('input[type="date"][name="appointment_date"]');
  if (dateInp && !dateInp.value) {
    dateInp.value = new Date().toISOString().split('T')[0];
  }

  // Default payment date to today if blank
  const payDateInp = document.querySelector('input[type="date"][name="payment_date"]');
  if (payDateInp && !payDateInp.value) {
    payDateInp.value = new Date().toISOString().split('T')[0];
  }
});