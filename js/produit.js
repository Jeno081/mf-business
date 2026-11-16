/* MF Business — fiche produit */
(function () {
  'use strict';

  var product = null;
  var selectedColor = '';
  var selectedVariant = '';

  function mixWithWhite(hex, ratio) {
    var h = String(hex).replace('#', '');
    if (h.length === 3) h = h.split('').map(function (c) { return c + c; }).join('');
    var r = parseInt(h.slice(0, 2), 16);
    var g = parseInt(h.slice(2, 4), 16);
    var b = parseInt(h.slice(4, 6), 16);
    r = Math.round(r + (255 - r) * ratio);
    g = Math.round(g + (255 - g) * ratio);
    b = Math.round(b + (255 - b) * ratio);
    return '#' + [r, g, b].map(function (n) { return n.toString(16).padStart(2, '0'); }).join('');
  }

  function setText(sel, value) {
    var el = MF.qs(sel);
    if (el) el.textContent = value;
  }

  function updateVariant() {
    var cap = MF.capacity(product);
    selectedVariant = cap && selectedColor ? cap + ' · ' + selectedColor : (selectedColor || product.subtitle);
    setText('[data-color-name]', selectedColor);
    var addBtn = MF.qs('.product__buy [data-add-to-cart]');
    if (addBtn) addBtn.setAttribute('data-variant', selectedVariant);
    var wa = MF.qs('[data-whatsapp-product]');
    if (wa) {
      wa.href = MF.whatsappLink(
        'Bonjour MF Business 👋\nJe suis intéressé(e) par : ' + product.name +
        ' (' + selectedVariant + ') — ' + MF.formatPrice(product.price) + '.\nEst-il disponible ?'
      );
    }
  }

  function renderColors() {
    var wrap = MF.qs('[data-colors]');
    var option = MF.qs('[data-color-option]');
    if (!wrap || !option) return;
    if (!product.colors || !product.colors.length) {
      option.hidden = true;
      return;
    }
    option.hidden = false;
    wrap.innerHTML = product.colors.map(function (color, index) {
      return '<button class="swatch' + (index === 0 ? ' is-active' : '') + '" type="button" role="radio" aria-checked="' + (index === 0) + '"' +
        ' style="--swatch:' + color.hex + '" data-color-index="' + index + '" aria-label="' + MF.escapeHtml(color.name) + '" title="' + MF.escapeHtml(color.name) + '"></button>';
    }).join('');
    selectedColor = product.colors[0].name;
    updateVariant();

    wrap.addEventListener('click', function (e) {
      var btn = e.target.closest('[data-color-index]');
      if (!btn) return;
      var index = Number(btn.getAttribute('data-color-index'));
      var color = product.colors[index];
      if (!color) return;
      selectedColor = color.name;
      MF.qsa('[data-color-index]', wrap).forEach(function (b) {
        var active = b === btn;
        b.classList.toggle('is-active', active);
        b.setAttribute('aria-checked', String(active));
      });
      var stage = MF.qs('[data-stage]');
      if (stage) {
        stage.style.setProperty('--tint-a', mixWithWhite(color.hex, 0.82));
        stage.style.setProperty('--tint-b', mixWithWhite(color.hex, 0.64));
      }
      updateVariant();
    });

    wrap.addEventListener('keydown', function (e) {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
      var buttons = MF.qsa('[data-color-index]', wrap);
      var current = buttons.indexOf(document.activeElement);
      if (current < 0) return;
      e.preventDefault();
      var next = (current + (e.key === 'ArrowRight' ? 1 : -1) + buttons.length) % buttons.length;
      buttons[next].focus();
      buttons[next].click();
    });
  }

  function renderTabs() {
    var tabs = MF.qsa('.tab');
    var panels = MF.qsa('[data-panel]');
    if (!tabs.length) return;
    function select(index) {
      tabs.forEach(function (tab, i) {
        var active = i === index;
        tab.setAttribute('aria-selected', String(active));
        tab.tabIndex = active ? 0 : -1;
      });
      panels.forEach(function (panel, i) { panel.hidden = i !== index; });
    }
    tabs.forEach(function (tab, index) {
      tab.addEventListener('click', function () { select(index); });
      tab.addEventListener('keydown', function (e) {
        if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
        e.preventDefault();
        var next = (index + (e.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
        tabs[next].focus();
        select(next);
      });
    });
    select(0);
  }

  function renderRelated() {
    var section = MF.qs('[data-related]');
    var grid = MF.qs('[data-related-grid]');
    if (!section || !grid) return;
    var related = MF.relatedProducts(product, 4);
    if (!related.length) return;
    grid.innerHTML = related.map(MF.productCard).join('');
    section.hidden = false;
  }

  function renderStructuredData() {
    var data = {
      '@context': 'https://schema.org',
      '@type': 'Product',
      name: product.name,
      description: product.description,
      brand: { '@type': 'Brand', name: product.brand },
      image: [product.image],
      offers: {
        '@type': 'Offer',
        priceCurrency: 'USD',
        price: product.price,
        availability: product.stock > 0 ? 'https://schema.org/InStock' : 'https://schema.org/PreOrder',
      },
    };
    var script = document.createElement('script');
    script.type = 'application/ld+json';
    script.textContent = JSON.stringify(data);
    document.head.appendChild(script);
  }

  document.addEventListener('DOMContentLoaded', function () {
    var id = new URLSearchParams(window.location.search).get('id');
    product = id ? MF.getProduct(id) : null;
    var view = MF.qs('[data-product-view]');
    var missing = MF.qs('[data-product-missing]');

    if (!product) {
      if (view) view.hidden = true;
      if (missing) missing.hidden = false;
      document.title = 'Produit introuvable — MF Business';
      return;
    }

    document.title = product.name + ' — ' + product.brand + ' | MF Business';
    var meta = document.querySelector('meta[name="description"]');
    if (meta) meta.setAttribute('content', product.description);

    setText('[data-breadcrumb-name]', product.name);
    var stage = MF.qs('[data-stage]');
    if (stage) {
      stage.style.setProperty('--tint-a', product.tint[0]);
      stage.style.setProperty('--tint-b', product.tint[1]);
      stage.classList.toggle('product__stage--photo', product.category === 'audio' || product.category === 'accessoires');
    }

    var img = MF.qs('[data-product-image]');
    if (img) {
      img.src = product.image;
      img.alt = product.name + ' — ' + product.brand;
    }

    var badge = MF.qs('[data-product-badge]');
    if (badge && product.badge) {
      badge.textContent = product.badge;
      badge.classList.add('badge--' + (product.badgeTone || 'new'));
      badge.hidden = false;
    }

    setText('[data-product-brand]', product.brand);
    setText('[data-product-name]', product.name);
    setText('[data-product-desc]', product.description);
    var starsWrap = MF.qs('[data-product-stars]');
    if (starsWrap) starsWrap.innerHTML = MF.stars(product.rating).replace('rating', 'rating rating--lg');
    setText('[data-product-reviews]', '(' + product.reviews + ' avis)');
    setText('[data-product-stock]', product.stock >= 6 ? 'En stock' : 'Plus que ' + product.stock + ' en stock');

    setText('[data-product-price]', MF.formatPrice(product.price));
    var old = MF.qs('[data-product-old]');
    if (old && product.oldPrice) {
      old.textContent = MF.formatPrice(product.oldPrice);
      old.hidden = false;
    }
    var save = MF.qs('[data-product-save]');
    if (save && product.oldPrice) {
      save.textContent = 'Économisez ' + MF.formatPrice(product.oldPrice - product.price);
      save.hidden = false;
    }
    var installment = MF.qs('[data-product-installment]');
    if (installment) {
      if (product.price >= 500) {
        var per = Math.ceil(product.price / 3);
        installment.textContent = 'ou 3 × ' + MF.formatPrice(per) + ' sans frais';
      } else {
        installment.textContent = 'Prix affiché TTC, disponible en boutique.';
      }
    }

    renderColors();

    var addBtn = MF.qs('.product__buy [data-add-to-cart]');
    if (addBtn) addBtn.setAttribute('data-id', product.id);

    var qtyInput = MF.qs('#quantity');
    var minus = MF.qs('[data-qty-minus]');
    var plus = MF.qs('[data-qty-plus]');
    function syncQty() {
      if (!qtyInput) return;
      var value = Math.max(1, Math.min(20, Math.round(Number(qtyInput.value) || 1)));
      qtyInput.value = String(value);
      if (addBtn) addBtn.setAttribute('data-qty', String(value));
    }
    if (minus) minus.addEventListener('click', function () {
      qtyInput.value = String(Math.max(1, Number(qtyInput.value) - 1));
      syncQty();
    });
    if (plus) plus.addEventListener('click', function () {
      qtyInput.value = String(Math.min(20, Number(qtyInput.value) + 1));
      syncQty();
    });
    if (qtyInput) {
      qtyInput.addEventListener('change', syncQty);
      qtyInput.addEventListener('input', syncQty);
    }
    syncQty();

    var features = MF.qs('[data-product-features]');
    if (features) {
      features.innerHTML = product.features.map(function (f) { return '<li>' + MF.escapeHtml(f) + '</li>'; }).join('');
    }
    var specs = MF.qs('[data-product-specs]');
    if (specs) {
      specs.innerHTML = product.specs.map(function (row) {
        return '<tr><th scope="row">' + MF.escapeHtml(row[0]) + '</th><td>' + MF.escapeHtml(row[1]) + '</td></tr>';
      }).join('');
    }

    renderTabs();
    renderRelated();
    renderStructuredData();
    MF.initReveal();
  });
})();
