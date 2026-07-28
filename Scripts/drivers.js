/* ============================================================
   VSM F1 League — drivers.js
   Renders the roster grid on drivers.html.

   To add/remove a driver or change layout, just edit DRIVERS below.
   - photo   : path from the site root. If it 404s, the card falls
               back to an initials tile automatically — no need to
               have the image ready before adding a driver here.
   - link    : path to that driver's stats page, from site root.
   - size    : "md" (top row) or "lg" (bigger feature card).
   ============================================================ */

const TEAM_COLORS = {
  ferrari:     '#e8001d',
  mclaren:     '#ff8000',
  mercedes:    '#00d2be',
  redbull:     '#3671c6',
  williams:    '#64aaff',
  audi:        '#999999',
  haas:        '#aaaaaa',
  astonmartin: '#358c75',
  cadillac:    '#bbbbbb',
  racingbulls: '#5470c6',
  alpine:      '#ff87bc',
};

const DRIVERS = [
  { name: 'Kai',   team: 'Ferrari',  teamSlug: 'ferrari',  photo: 'Images/KaiDriver.jpeg',   link: 'drivers/kai.html' },
  { name: 'Deshy', team: 'Ferrari',  teamSlug: 'ferrari',  photo: 'Images/deshyPFP.jpg', link: 'drivers/deshy.html' },
  { name: 'Tom',   team: 'McLaren',  teamSlug: 'mclaren',  photo: 'Images/DriverTom.jpg',   link: 'drivers/tom.html' },
  { name: 'Téo',   team: 'Red Bull', teamSlug: 'redbull',  photo: 'Images/teoPFP.png',   link: 'drivers/teo.html' },
  { name: 'Rehan', team: 'Mercedes', teamSlug: 'mercedes', photo: 'Images/rehanPFP.png', link: 'drivers/rehan.html' },
];

function initials(name) {
  return name
    .replace(/[^\p{L}\s]/gu, '')
    .split(/\s+/)
    .filter(Boolean)
    .map(w => w[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
}

function renderDrivers() {
  const grid = document.getElementById('driver-grid');
  if (!grid) return;

  grid.innerHTML = DRIVERS.map(d => {
    const color = TEAM_COLORS[d.teamSlug] || '#e10600';
    return `
      <a class="driver-card" href="${d.link}" style="--team-color:${color}">
        <img
          class="driver-photo"
          src="${d.photo}"
          alt="${d.name}"
          onerror="this.closest('.driver-card').classList.add('no-photo'); this.remove();"
        >
        <div class="driver-photo-fallback">${initials(d.name)}</div>
        <div class="driver-card-overlay"></div>
        <div class="driver-card-info">
          <span class="driver-card-team" style="color:${color}; border-color:${color}66;">${d.team}</span>
          <div class="driver-card-name">
            ${d.name}
            <span class="driver-card-arrow">→</span>
          </div>
        </div>
      </a>
    `;
  }).join('');
}

document.addEventListener('DOMContentLoaded', renderDrivers);