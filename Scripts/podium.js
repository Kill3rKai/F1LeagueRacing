/* ============================================================
   VSM F1 League — podium.js

   Manually enter the top-3 finishers for each COMPLETED race here.
   Nothing else needs to change — not calendar.js, not update.py.

   Key each block by the race's round number (must match the
   `round` field for that race in Scripts/calendar.js's RACES array).
   Leave a round out of PODIUMS and it simply won't show a podium
   strip — no need to "clear" anything for future rounds.

   Fields per finisher:
     pos      - 1, 2, or 3
     code     - 3-letter driver code shown in the coloured circle
     name     - display name
     teamSlug - must match a team colour defined in Style/main.css
                (ferrari, mclaren, mercedes, redbull, williams,
                 audi, haas, astonmartin, cadillac, racingbulls, alpine)
   ============================================================ */

const PODIUMS = {
  1: [
    { pos: 1, code: 'DES', name: 'Deshy',   teamSlug: 'ferrari' },
    { pos: 2, code: 'ALB', name: 'Albon', teamSlug: 'williams' },
    { pos: 3, code: 'ANT', name: 'Antonelli',   teamSlug: 'mercedes' },
  ],
  2: [
    { pos: 1, code: 'NOR', name: 'Norris',   teamSlug: 'mclaren' },
    { pos: 2, code: 'VER', name: 'Verstappen', teamSlug: 'redbull' },
    { pos: 3, code: 'ASH', name: 'Teo',   teamSlug: 'redbull' },
  ],
  3: [
    { pos: 1, code: 'REH', name: 'Rehan',   teamSlug: 'mercedes' },
    { pos: 2, code: 'ASH', name: 'Teo', teamSlug: 'redbull' },
    { pos: 3, code: 'KAI', name: 'Kai',   teamSlug: 'ferrari' },
  ],
  /*4: [
    { pos: 1, code: 'KAI', name: 'Kai',   teamSlug: 'ferrari' },
    { pos: 2, code: 'REH', name: 'Rehan', teamSlug: 'mercedes' },
    { pos: 3, code: 'ASH', name: 'Teo',   teamSlug: 'redbull' },
  ],*/
};

function renderPodiums() {
  Object.entries(PODIUMS).forEach(([round, entries]) => {
    const row = document.querySelector(`.cal-row[data-round="${round}"]`);
    if (!row) return;

    // Avoid stacking duplicates if this ever runs twice
    const already = row.nextElementSibling;
    if (already && already.classList.contains('cal-podium') && already.dataset.round === round) {
      already.remove();
    }

    const strip = document.createElement('div');
    strip.className = 'cal-podium';
    strip.dataset.round = round;
    strip.innerHTML = entries.map(e => `
      <div class="podium-card">
        <span class="podium-pos">P${e.pos}</span>
        <span class="podium-avatar" style="background:var(--${e.teamSlug})">${e.code}</span>
        <div class="podium-info">
          <span class="podium-name">${e.name}</span>
        </div>
      </div>
    `).join('');

    row.insertAdjacentElement('afterend', strip);

    // Make the row clickable: toggles the strip open/closed
    row.classList.add('has-podium');
    if (!row.querySelector('.cal-caret')) {
      const caret = document.createElement('span');
      caret.className = 'cal-caret';
      caret.textContent = '▾';
      row.appendChild(caret);
    }
    row.addEventListener('click', () => {
      const isOpen = row.classList.toggle('podium-open');
      strip.classList.toggle('open', isOpen);
    });
  });
}

/* calendar.js builds the rows on DOMContentLoaded too — as long as this
   script tag comes AFTER Scripts/calendar.js in the HTML, this listener
   registers second and will run after the rows already exist. */
document.addEventListener('DOMContentLoaded', renderPodiums);