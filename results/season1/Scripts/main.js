// ── Custom cursor ──
const cursor = document.getElementById('cursor');
const ring   = document.getElementById('cursorRing');
let mouseX = 0, mouseY = 0;
let ringX  = 0, ringY  = 0;
let cursorReady = false;

// Hide until first mouse movement
cursor.style.opacity = '0';
ring.style.opacity   = '0';

document.addEventListener('mousemove', e => {
  mouseX = e.clientX;
  mouseY = e.clientY;

  // Snap everything to cursor on first move, then reveal
  if (!cursorReady) {
    ringX = mouseX;
    ringY = mouseY;
    cursorReady = true;
    cursor.style.opacity = '1';
    ring.style.opacity   = '1';
  }

  cursor.style.left = mouseX + 'px';
  cursor.style.top  = mouseY + 'px';
});

(function animateRing() {
  ringX += (mouseX - ringX) * 0.12;
  ringY += (mouseY - ringY) * 0.12;
  ring.style.left = ringX + 'px';
  ring.style.top  = ringY + 'px';
  requestAnimationFrame(animateRing);
})();

// ── Grow ring on hover over interactive elements ──
document.querySelectorAll('a, button, .link-item, .featured-card, .live-badge').forEach(el => {
  el.addEventListener('mouseenter', () => {
    ring.style.width       = '60px';
    ring.style.height      = '60px';
    ring.style.borderColor = 'rgba(0,200,255,0.7)';
  });
  el.addEventListener('mouseleave', () => {
    ring.style.width       = '36px';
    ring.style.height      = '36px';
    ring.style.borderColor = 'rgba(0,200,255,0.4)';
  });
});

// ── PROGRESS BAR ──
window.addEventListener('load', () => {
  setTimeout(() => {
    const fill = document.getElementById('lilly-progress');
    if (fill) fill.style.width = '100%';
  }, 300);
});

// ── PROGRESS BAR OS ──
window.addEventListener('load', () => {
  setTimeout(() => {
    const fill = document.getElementById('killeros-progress');
    if (fill) fill.style.width = '90%';
  }, 300);
});

// ── TYPING EFFECT ──
const subtitles = [
  'programmer · creator · cyber',
  'twitch · youtube · socials',
  'lilly ai · cybersec · chaos'
];
let si = 0, ci = 0, deleting = false;
const subEl = document.querySelector('.hero-sub');

function type() {
  const target = subtitles[si];
  if (!deleting) {
    ci++;
    subEl.childNodes[0].textContent = target.slice(0, ci);
    if (ci === target.length) {
      deleting = true;
      setTimeout(type, 2000);
      return;
    }
  } else {
    ci--;
    subEl.childNodes[0].textContent = target.slice(0, ci);
    if (ci === 0) {
      deleting = false;
      si = (si + 1) % subtitles.length;
      setTimeout(type, 400);
      return;
    }
  }
  setTimeout(type, deleting ? 35 : 60);
}

// Set up text node + blinking cursor
subEl.innerHTML = '';
subEl.appendChild(document.createTextNode(''));
const cur = document.createElement('span');
cur.className = 'cursor';
subEl.appendChild(cur);
setTimeout(type, 800);

// ── TWITCH BADGE ──
const statusEl = document.getElementById('status-text');
statusEl.textContent = 'Check Stream →';
statusEl.parentElement.addEventListener('click', () => {
  window.open('https://www.twitch.tv/Kill3rKai', '_blank');
});
