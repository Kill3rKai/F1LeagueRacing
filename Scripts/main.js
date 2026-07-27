/* ============================================================
   VSM F1 League — main.js
   ============================================================ */

/* ——— Nav dropdown (SEASON) ———
   Opens on hover (see main.css :hover rule). Clicking the "Season"
   link itself just navigates straight to the latest season page —
   no JS needed for that anymore. */

/* ——— Page tabs: STANDINGS | CALENDAR ——— */
const standingsControls = document.querySelector('.standings-controls');

document.querySelectorAll('.page-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.page-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    const target = tab.dataset.panel;
    document.querySelectorAll('.standings-panel[data-panel]').forEach(panel => {
      panel.classList.toggle('hidden', panel.dataset.panel !== target);
    });
    if (standingsControls) {
      standingsControls.classList.toggle('hidden', target !== 'standings');
    }
  });
});

/* ——— DRIVERS / CONSTRUCTORS toggle ——— */
document.querySelectorAll('.toggle-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const target = btn.dataset.target;
    document.querySelectorAll('.standings-panel[data-table]').forEach(panel => {
      panel.classList.toggle('hidden', panel.dataset.table !== target);
    });
  });
});

/* ——— Season selector redirect ——— */
const switcher = document.querySelector('.switcher-select');
if (switcher) {
  switcher.addEventListener('change', () => {
    window.location.href = switcher.value;
  });
}