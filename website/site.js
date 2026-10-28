/* Presentation only. Analysis and official catalogue behavior remain separate. */
(() => {
  function init(document, window) {
    document.body.classList.add('js-ready');
    const toggle = document.querySelector('.menu-toggle');
    const nav = document.querySelector('#primary-nav');
    if (toggle && nav) {
      const close = () => { toggle.setAttribute('aria-expanded', 'false'); nav.classList.remove('is-open'); };
      toggle.addEventListener('click', () => {
        const open = toggle.getAttribute('aria-expanded') !== 'true';
        toggle.setAttribute('aria-expanded', String(open));
        nav.classList.toggle('is-open', open);
      });
      nav.addEventListener('click', event => { if (event.target.closest('a')) close(); });
      document.addEventListener('keydown', event => {
        if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') { close(); toggle.focus(); }
      });
      const desktop = window.matchMedia('(min-width: 761px)');
      desktop.addEventListener?.('change', event => { if (event.matches) close(); });
    }
    const filters = [...document.querySelectorAll('[data-filter]')];
    const cards = [...document.querySelectorAll('[data-category]')];
    const status = document.querySelector('#filter-status');
    const rail = document.querySelector('.workflow-rail');
    for (const button of filters) {
      button.addEventListener('click', () => {
        const category = button.dataset.filter;
        for (const filter of filters) filter.setAttribute('aria-pressed', String(filter === button));
        let count = 0;
        for (const card of cards) {
          const visible = category === 'all' || card.dataset.category.split(' ').includes(category);
          card.hidden = !visible;
          if (visible) count++;
        }
        if (status) status.textContent = `Showing ${count} ${category === 'all' ? '' : button.textContent.trim() + ' '}workflow${count === 1 ? '' : 's'}.`;
        if (rail) rail.scrollLeft = 0;
      });
    }
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (!reduced.matches && window.IntersectionObserver) {
      const observer = new window.IntersectionObserver(entries => {
        for (const entry of entries) if (entry.isIntersecting) { entry.target.classList.add('is-visible'); observer.unobserve(entry.target); }
      }, { threshold: 0.12 });
      for (const element of document.querySelectorAll('[data-reveal]')) { element.classList.add('will-reveal'); observer.observe(element); }
      reduced.addEventListener?.('change', event => {
        if (event.matches) { observer.disconnect(); for (const el of document.querySelectorAll('[data-reveal]')) el.classList.add('is-visible'); }
      });
    }
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = { init };
  if (typeof document !== 'undefined') init(document, window);
})();
