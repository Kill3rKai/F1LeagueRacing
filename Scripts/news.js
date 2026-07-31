/* ============================================================
   VSM F1 League — news.js
   Category filter pills on news.html. Filters both the
   featured/side stories and the grid cards by data-category.
   ============================================================ */

const filterPills = document.querySelectorAll('.filter-pill');
const filterable = document.querySelectorAll('[data-category]');

filterPills.forEach(pill => {
    pill.addEventListener('click', () => {
        filterPills.forEach(p => p.classList.remove('active'));
        pill.classList.add('active');

        const target = pill.dataset.filter;

        filterable.forEach(item => {
            const show = target === 'all' || item.dataset.category === target;
            item.classList.toggle('is-hidden', !show);
        });
    });
});