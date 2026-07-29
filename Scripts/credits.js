/* ============================================================
   VSM F1 League — credits.js
   Renders the sections/rows on credits.html.

   To add, remove, or reorder anything, just edit CREDITS below.
   - section : heading shown above that group of rows
   - items   : each row — name, role/description, and an optional
               link. Links starting with "http" open in a new tab
               automatically; internal links (driver pages etc.)
               navigate normally.
   ============================================================ */

const CREDITS = [
  {
    section: 'The Grid',
    items: [
      { name: 'Kai',   role: 'Ferrari — Driver',   link: 'drivers/kai.html' },
      { name: 'Deshy', role: 'Ferrari — Driver',   link: 'drivers/deshy.html' },
      { name: 'Tom',   role: 'McLaren — Driver',   link: 'drivers/tom.html' },
      { name: 'Téo',   role: 'Red Bull — Driver',  link: 'drivers/teo.html' },
      { name: 'Rehan', role: 'Mercedes — Driver',  link: 'drivers/rehan.html' },
    ],
  },
  {
    section: 'Built By',
    items: [
      { name: 'Kai', role: 'Site Owner & Developer', link: 'https://kill3rkai.ai' },
    ],
  },
  {
    section: 'Powered By',
    items: [
      { name: 'F1 26',        role: 'Codemasters / EA Sports' },
      { name: 'GitHub Pages', role: 'Hosting',                                    link: 'https://pages.github.com' },
      { name: 'Google Fonts', role: 'Barlow Condensed, Inter, JetBrains Mono',    link: 'https://fonts.google.com' },
      { name: 'Discord',      role: 'League community',                          link: 'https://discord.gg/tXmGZc8z87' },
    ],
  },
];

function renderCredits() {
  const root = document.getElementById('credits-root');
  if (!root) return;

  root.innerHTML = CREDITS.map(group => `
    <div class="credits-section">
      <h2 class="credits-heading">${group.section}</h2>
      <div class="credits-list">
        ${group.items.map(item => {
          const isExternal = item.link && item.link.startsWith('http');
          const tag = item.link ? 'a' : 'div';
          const attrs = item.link
            ? `href="${item.link}"${isExternal ? ' target="_blank" rel="noopener"' : ''}`
            : '';
          return `
            <${tag} class="credits-row" ${attrs}>
              <span class="credits-name">${item.name}</span>
              <span class="credits-role">${item.role}</span>
              ${item.link ? '<span class="credits-arrow">→</span>' : ''}
            </${tag}>
          `;
        }).join('')}
      </div>
    </div>
  `).join('');
}

document.addEventListener('DOMContentLoaded', renderCredits);