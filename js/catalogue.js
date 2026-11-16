/* MF Business — catalogue : recherche, filtres, tri, état dans l'URL */
(function () {
  'use strict';

  var grid, empty, resultCount, chipsWrap, form, searchInput, sortSelect, filtersPanel, overlay;
  var BUDGETS = [
    { id: '0-149', label: 'Moins de 150 $', min: 0, max: 149 },
    { id: '150-399', label: '150 – 399 $', min: 150, max: 399 },
    { id: '400-799', label: '400 – 799 $', min: 400, max: 799 },
    { id: '800-1199', label: '800 – 1 199 $', min: 800, max: 1199 },
    { id: '1200-99999', label: '1 200 $ et plus', min: 1200, max: 99999999 },
  ];

  var state = { q: '', categories: [], brands: [], budgets: [], sort: 'featured' };

  function normalise(str) {
    return String(str || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');
  }

  function readUrl() {
    var params = new URLSearchParams(window.location.search);
    state.q = params.get('q') || '';
    state.categories = (params.get('categorie') || '').split(',').filter(function (id) {
      return !!MF.getCategory(id);
    });
    state.brands = (params.get('marque') || '').split(',').filter(function (b) {
      return MF.BRANDS.indexOf(b) > -1;
    });
    state.budgets = (params.get('budget') || '').split(',').filter(function (id) {
      return BUDGETS.some(function (b) { return b.id === id; });
    });
    state.sort = params.get('tri') || 'featured';
    if (['featured', 'price-asc', 'price-desc', 'rating', 'new'].indexOf(state.sort) < 0) state.sort = 'featured';
  }

  function writeUrl() {
    var params = new URLSearchParams();
    if (state.q) params.set('q', state.q);
    if (state.categories.length) params.set('categorie', state.categories.join(','));
    if (state.brands.length) params.set('marque', state.brands.join(','));
    if (state.budgets.length) params.set('budget', state.budgets.join(','));
    if (state.sort !== 'featured') params.set('tri', state.sort);
    var qs = params.toString();
    try {
      history.replaceState(null, '', window.location.pathname + (qs ? '?' + qs : ''));
    } catch (err) {
      /* file:// : l'API History est restreinte, les filtres restent fonctionnels. */
    }
  }

  function renderBrandFilters() {
    var wrap = MF.qs('[data-brand-filters]');
    if (!wrap) return;
    wrap.innerHTML = MF.BRANDS.map(function (brand) {
      var count = MF.PRODUCTS.filter(function (p) { return p.brand === brand; }).length;
      return '<label class="check"><input type="checkbox" name="marque" value="' + MF.escapeHtml(brand) + '">' +
        '<span class="check__box" aria-hidden="true"></span>' + MF.escapeHtml(brand) +
        '<em>' + count + '</em></label>';
    }).join('');
  }

  function syncForm() {
    if (searchInput) searchInput.value = state.q;
    if (sortSelect) sortSelect.value = state.sort;
    MF.qsa('input[name="categorie"]').forEach(function (input) {
      input.checked = state.categories.indexOf(input.value) > -1;
    });
    MF.qsa('input[name="marque"]').forEach(function (input) {
      input.checked = state.brands.indexOf(input.value) > -1;
    });
    MF.qsa('input[name="budget"]').forEach(function (input) {
      input.checked = state.budgets.indexOf(input.value) > -1;
    });
  }

  function matchesBudget(price) {
    if (!state.budgets.length) return true;
    return state.budgets.some(function (id) {
      var b = BUDGETS.find(function (item) { return item.id === id; });
      return b && price >= b.min && price <= b.max;
    });
  }

  function filtered() {
    var terms = normalise(state.q).split(/\s+/).filter(Boolean);
    var list = MF.PRODUCTS.filter(function (p) {
      if (state.categories.length && state.categories.indexOf(p.category) < 0) return false;
      if (state.brands.length && state.brands.indexOf(p.brand) < 0) return false;
      if (!matchesBudget(p.price)) return false;
      if (terms.length) {
        var haystack = normalise([
          p.name, p.brand, p.series, p.subtitle,
          MF.getCategory(p.category).label,
        ].join(' '));
        if (!terms.every(function (term) { return haystack.indexOf(term) > -1; })) return false;
      }
      return true;
    });

    var sort = state.sort;
    if (sort === 'price-asc') list.sort(function (a, b) { return a.price - b.price; });
    else if (sort === 'price-desc') list.sort(function (a, b) { return b.price - a.price; });
    else if (sort === 'rating') list.sort(function (a, b) { return b.rating - a.rating || b.reviews - a.reviews; });
    else if (sort === 'new') list.sort(function (a, b) {
      var an = a.badge === 'Nouveau' ? 1 : 0;
      var bn = b.badge === 'Nouveau' ? 1 : 0;
      return bn - an || b.reviews - a.reviews;
    });
    else list.sort(function (a, b) { return (b.featured ? 1 : 0) - (a.featured ? 1 : 0); });
    return list;
  }

  function renderChips() {
    if (!chipsWrap) return;
    var chips = [];
    if (state.q) chips.push({ type: 'q', value: '', label: '« ' + state.q + ' »' });
    state.categories.forEach(function (id) {
      chips.push({ type: 'categorie', value: id, label: MF.getCategory(id).label });
    });
    state.brands.forEach(function (b) { chips.push({ type: 'marque', value: b, label: b }); });
    state.budgets.forEach(function (id) {
      var b = BUDGETS.find(function (item) { return item.id === id; });
      if (b) chips.push({ type: 'budget', value: id, label: b.label });
    });

    chipsWrap.hidden = chips.length === 0;
    chipsWrap.innerHTML = chips.map(function (chip) {
      return '<span class="chip">' + MF.escapeHtml(chip.label) +
        '<button type="button" data-remove-type="' + chip.type + '" data-remove-value="' + MF.escapeHtml(chip.value) + '" aria-label="Retirer le filtre ' + MF.escapeHtml(chip.label) + '">' +
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>' +
        '</button></span>';
    }).join('');
  }

  function render() {
    var list = filtered();
    if (resultCount) resultCount.textContent = String(list.length);
    if (grid) {
      grid.innerHTML = list.map(MF.productCard).join('');
      grid.hidden = list.length === 0;
    }
    if (empty) empty.hidden = list.length > 0;
    renderChips();
    syncForm();
    MF.initReveal();
  }

  function commit() {
    writeUrl();
    render();
  }

  function removeChip(type, value) {
    if (type === 'q') state.q = '';
    if (type === 'categorie') state.categories = state.categories.filter(function (v) { return v !== value; });
    if (type === 'marque') state.brands = state.brands.filter(function (v) { return v !== value; });
    if (type === 'budget') state.budgets = state.budgets.filter(function (v) { return v !== value; });
    commit();
  }

  function reset() {
    state = { q: '', categories: [], brands: [], budgets: [], sort: 'featured' };
    if (form) form.reset();
    if (sortSelect) sortSelect.value = 'featured';
    commit();
  }

  function setDrawer(open) {
    if (!filtersPanel || !overlay) return;
    filtersPanel.classList.toggle('is-open', open);
    overlay.hidden = !open;
    document.body.classList.toggle('filters-open', open);
    var btn = MF.qs('[data-filters-open]');
    if (btn) btn.setAttribute('aria-expanded', String(open));
  }

  document.addEventListener('DOMContentLoaded', function () {
    grid = MF.qs('[data-products]');
    empty = MF.qs('[data-empty]');
    resultCount = MF.qs('[data-result-count]');
    chipsWrap = MF.qs('[data-active-filters]');
    form = MF.qs('#filters-form');
    searchInput = MF.qs('[data-filter-q]');
    sortSelect = MF.qs('[data-sort]');
    filtersPanel = MF.qs('#filters');
    overlay = MF.qs('[data-filters-overlay]');

    MF.qsa('[data-count]').forEach(function (el) {
      var n = MF.categoryCount(el.getAttribute('data-count'));
      el.textContent = el.hasAttribute('data-pad') ? String(n).padStart(2, '0') : String(n);
    });
    renderBrandFilters();
    readUrl();
    syncForm();
    render();

    if (form) {
      form.addEventListener('change', function (e) {
        var input = e.target;
        if (!input.name) return;
        var value = input.value;
        if (input.name === 'categorie') {
          state.categories = input.checked
            ? state.categories.concat([value])
            : state.categories.filter(function (v) { return v !== value; });
        }
        if (input.name === 'marque') {
          state.brands = input.checked
            ? state.brands.concat([value])
            : state.brands.filter(function (v) { return v !== value; });
        }
        if (input.name === 'budget') {
          state.budgets = input.checked
            ? state.budgets.concat([value])
            : state.budgets.filter(function (v) { return v !== value; });
        }
        commit();
      });
    }

    if (searchInput) {
      searchInput.addEventListener('input', MF.debounce(function () {
        state.q = searchInput.value.trim();
        commit();
      }, 180));
    }

    if (sortSelect) {
      sortSelect.addEventListener('change', function () {
        state.sort = sortSelect.value;
        commit();
      });
    }

    if (chipsWrap) {
      chipsWrap.addEventListener('click', function (e) {
        var btn = e.target.closest('[data-remove-type]');
        if (!btn) return;
        removeChip(btn.getAttribute('data-remove-type'), btn.getAttribute('data-remove-value'));
      });
    }

    MF.qsa('[data-filters-reset], [data-empty-reset]').forEach(function (btn) {
      btn.addEventListener('click', reset);
    });

    var openBtn = MF.qs('[data-filters-open]');
    if (openBtn) openBtn.addEventListener('click', function () { setDrawer(true); });
    var closeBtn = MF.qs('[data-filters-close]');
    if (closeBtn) closeBtn.addEventListener('click', function () { setDrawer(false); });
    var applyBtn = MF.qs('[data-filters-apply]');
    if (applyBtn) applyBtn.addEventListener('click', function () { setDrawer(false); });
    if (overlay) overlay.addEventListener('click', function () { setDrawer(false); });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') setDrawer(false);
    });

    window.addEventListener('resize', function () {
      if (window.innerWidth > 900) setDrawer(false);
    });

    window.addEventListener('popstate', function () {
      readUrl();
      syncForm();
      render();
    });
  });
})();
