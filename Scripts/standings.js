/* ============================================================
   VSM F1 League — standings.js

   Fetches Scripts/standings.json (written by tools/update.py) and
   draws it into the drivers and constructors tables on the page.

   Because this uses fetch(), the site needs to be served over
   http/https to work — either properly hosted, or run locally with
   e.g. `py -m http.server` from the site root and viewed at
   http://localhost:8000. Opening index.html by double-clicking it
   (file://) will NOT work — browsers block fetch() of local files.

   Each season page sets two things before this script runs:
     <script>
       window.CURRENT_SEASON = 1;
       window.STANDINGS_JSON_PATH = '../Scripts/standings.json';
     </script>
     <script src="../Scripts/standings.js"></script>
   ============================================================ */

function renderDriverTable(drivers) {
  const tbody = document.querySelector('[data-table="drivers"] tbody');
  if (!tbody) return;

  tbody.innerHTML = drivers.map(d => `
    <tr data-team="${d.teamSlug}">
      <td class="td-pos">${String(d.pos).padStart(2, '0')}</td>
      <td class="td-name${d.isPlayer ? ' player' : ''}">${d.name}${d.isPlayer ? ' ★' : ''}</td>
      <td class="td-team tc-${d.teamSlug}">${d.team}</td>
      <td class="td-pts${d.pos === 1 ? ' leader' : ''}">${d.pts}</td>
      <td class="td-gap">${d.gap}</td>
    </tr>
  `).join('');
}

function renderConstructorTable(constructors) {
  const tbody = document.querySelector('[data-table="constructors"] tbody');
  if (!tbody) return;

  tbody.innerHTML = constructors.map(c => `
    <tr data-team="${c.teamSlug}">
      <td class="td-pos">${String(c.pos).padStart(2, '0')}</td>
      <td class="td-name tc-${c.teamSlug}">${c.team}</td>
      <td class="td-pts${c.pos === 1 ? ' leader' : ''}">${c.pts}</td>
      <td class="td-gap">${c.gap}</td>
    </tr>
  `).join('');
}

function updatePreSeasonNote(drivers, message) {
  const note = document.querySelector('.pre-season-note');
  if (!note) return;
  if (message) {
    note.textContent = message;
    note.style.display = '';
    return;
  }
  const started = drivers.some(d => d.pts > 0);
  note.style.display = started ? 'none' : '';
}

async function renderStandings() {
  const seasonNum = window.CURRENT_SEASON || 1;
  const jsonPath = window.STANDINGS_JSON_PATH || '../Scripts/standings.json';

  let allSeasons;
  try {
    const res = await fetch(jsonPath, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    allSeasons = await res.json();
  } catch (err) {
    console.error(
      `Could not load ${jsonPath} — if you're viewing this by double-clicking index.html, ` +
      `that won't work: browsers block fetch() over file://. Serve the site over http(s) ` +
      `(a real host, or "py -m http.server" run locally) and reload.`, err
    );
    updatePreSeasonNote(null, 'Standings failed to load — see console for details.');
    return;
  }

  const data = allSeasons[String(seasonNum)];
  if (!data) {
    console.warn(`No data for season ${seasonNum} in ${jsonPath}.`);
    return;
  }

  renderDriverTable(data.drivers);
  renderConstructorTable(data.constructors);
  updatePreSeasonNote(data.drivers);
}

document.addEventListener('DOMContentLoaded', renderStandings);