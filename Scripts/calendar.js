/* ============================================================
   VSM F1 League — calendar.js

   To update the calendar (new season, date changes, or moving
   the "next race" marker) just edit the RACES array below.
   Nothing else on the page needs to change.

   - round : displayed as "R01", "R02", etc.
   - flag  : an emoji flag
   - next  : set true on exactly ONE race to highlight it as
             the next race on the calendar
   ============================================================ */

const RACES = [
  { round: 1,  flag: '🇦🇺', country: 'Australia',            gp: 'Qatar Airways Australian Grand Prix' },
  { round: 2,  flag: '🇨🇳', country: 'China',                 gp: 'Heineken Chinese Grand Prix' },
  { round: 3,  flag: '🇯🇵', country: 'Japan',                 gp: 'Aramco Japanese Grand Prix', next: true },
  { round: 4,  flag: '🇺🇸', country: 'Miami',                 gp: 'Crypto.com Miami Grand Prix' },
  { round: 5,  flag: '🇨🇦', country: 'Canada',                gp: 'Lenovo Grand Prix du Canada' },
  { round: 6,  flag: '🇲🇨', country: 'Monaco',                gp: 'Louis Vuitton Grand Prix de Monaco' },
  { round: 7,  flag: '🇪🇸', country: 'Barcelona-Catalunya',   gp: 'MSC Cruises Gran Premio de Barcelona-Catalunya' },
  { round: 8,  flag: '🇦🇹', country: 'Austria',               gp: 'Lenovo Austrian Grand Prix' },
  { round: 9,  flag: '🇬🇧', country: 'Great Britain',         gp: 'Pirelli British Grand Prix' },
  { round: 10, flag: '🇧🇪', country: 'Belgium',               gp: 'Moët & Chandon Belgian Grand Prix' },
  { round: 11, flag: '🇭🇺', country: 'Hungary',               gp: 'AWS Hungarian Grand Prix' },
  { round: 12, flag: '🇳🇱', country: 'Netherlands',           gp: 'Heineken Dutch Grand Prix' },
  { round: 13, flag: '🇮🇹', country: 'Italy',                 gp: "Pirelli Gran Premio d'Italia" },
  { round: 14, flag: '🇪🇸', country: 'Spain',                 gp: 'TAG Heuer Gran Premio de España' },
  { round: 15, flag: '🇦🇿', country: 'Azerbaijan',            gp: 'Qatar Airways Azerbaijan Grand Prix' },
  { round: 16, flag: '🇸🇬', country: 'Singapore',             gp: 'Singapore Airlines Singapore Grand Prix' },
  { round: 17, flag: '🇺🇸', country: 'United States',         gp: 'MSC Cruises United States Grand Prix' },
  { round: 18, flag: '🇲🇽', country: 'Mexico',                gp: 'Gran Premio de la Ciudad de México' },
  { round: 19, flag: '🇧🇷', country: 'Brazil',                gp: 'MSC Cruises Grande Prêmio de São Paulo' },
  { round: 20, flag: '🇺🇸', country: 'Las Vegas',             gp: 'Heineken Las Vegas Grand Prix' },
  { round: 21, flag: '🇶🇦', country: 'Qatar',                 gp: 'Qatar Airways Qatar Grand Prix' },
  { round: 22, flag: '🇦🇪', country: 'Abu Dhabi',             gp: 'Etihad Airways Abu Dhabi Grand Prix' },
];

function renderCalendar() {
  const list = document.getElementById('cal-list');
  if (!list) return;

  list.innerHTML = RACES.map(race => `
    <div class="cal-row${race.next ? ' next-race' : ''}">
      <span class="cal-round">R${String(race.round).padStart(2, '0')}</span>
      <span class="cal-flag">${race.flag}</span>
      <span class="cal-country">${race.country}</span>
      <span class="cal-gp">${race.gp}</span>
      ${race.next ? '<span class="cal-badge-next">Next Race</span>' : ''}
    </div>
  `).join('');
}

document.addEventListener('DOMContentLoaded', renderCalendar);