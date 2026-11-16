/* ==========================================================================
   MF BUSINESS — socle commun : panier, en-tête, cartes produit, animations
   Script classique (pas de module) pour fonctionner aussi en double-clic.
   ========================================================================== */
(function () {
  'use strict';

  var MF = window.MF;
  var CART_KEY = 'mf-cart-v1';
  var memoryCart = null;
  var storageBroken = false;

  /* ---------------------------------------------------------------- utils */
  function qs(sel, root) { return (root || document).querySelector(sel); }
  function qsa(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

  function escapeHtml(str) {
    return String(str == null ? '' : str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function debounce(fn, delay) {
    var t;
    return function () {
      var args = arguments, ctx = this;
      clearTimeout(t);
      t = setTimeout(function () { fn.apply(ctx, args); }, delay || 200);
    };
  }

  MF.qs = qs;
  MF.qsa = qsa;
  MF.escapeHtml = escapeHtml;
  MF.debounce = debounce;

  /* --------------------------------------------------------------- panier */
  function readCart() {
    if (storageBroken) return memoryCart ? memoryCart.slice() : [];
    try {
      var raw = JSON.parse(localStorage.getItem(CART_KEY) || '[]');
      if (!Array.isArray(raw)) return [];
      return raw.filter(function (item) {
        return item && MF.getProduct(item.id) && Number(item.qty) > 0;
      }).map(function (item) {
        return {
          id: item.id,
          variant: typeof item.variant === 'string' ? item.variant : '',
          qty: Math.min(20, Math.max(1, Math.round(Number(item.qty)) || 1)),
        };
      });
    } catch (err) {
      storageBroken = true;
      return memoryCart ? memoryCart.slice() : [];
    }
  }

  function writeCart(items) {
    try {
      localStorage.setItem(CART_KEY, JSON.stringify(items));
    } catch (err) {
      /* file:// ou navigation privée : le panier reste en mémoire */
      storageBroken = true;
      memoryCart = items.slice();
    }
    updateCartCount();
    document.dispatchEvent(new CustomEvent('mf:cart', { detail: { items: items } }));
  }

  function cartCount() {
    return readCart().reduce(function (sum, item) { return sum + item.qty; }, 0);
  }

  function updateCartCount() {
    var count = cartCount();
    qsa('[data-cart-count]').forEach(function (el) {
      el.textContent = count > 9 ? '9+' : String(count);
      el.hidden = count === 0;
    });
    qsa('[data-cart-label]').forEach(function (el) {
      el.textContent = count === 0 ? 'Panier vide' : count + (count > 1 ? ' articles' : ' article');
    });
  }

  function addToCart(id, qty, variant) {
    var product = MF.getProduct(id);
    if (!product) return;
    qty = Math.max(1, Math.round(Number(qty) || 1));
    variant = variant || defaultVariant(product);
    var items = readCart();
    var found = items.find(function (item) {
      return item.id === id && item.variant === variant;
    });
    if (found) {
      found.qty = Math.min(20, found.qty + qty);
    } else {
      items.push({ id: id, variant: variant, qty: Math.min(20, qty) });
    }
    writeCart(items);
    toast(product.name + ' ajouté au panier.', 'success', { label: 'Voir le panier', href: 'panier.html' });
  }

  function setQty(id, variant, qty) {
    var items = readCart();
    var item = items.find(function (i) { return i.id === id && i.variant === variant; });
    if (!item) return;
    item.qty = Math.max(0, Math.min(20, Math.round(Number(qty) || 0)));
    writeCart(items.filter(function (i) { return i.qty > 0; }));
  }

  function removeFromCart(id, variant) {
    writeCart(readCart().filter(function (item) {
      return !(item.id === id && item.variant === variant);
    }));
  }

  function clearCart() { writeCart([]); }

  function cartDetails() {
    var lines = readCart().map(function (item) {
      var product = MF.getProduct(item.id);
      return {
        id: item.id,
        variant: item.variant,
        qty: item.qty,
        product: product,
        lineTotal: product.price * item.qty,
      };
    });
    var subtotal = lines.reduce(function (sum, line) { return sum + line.lineTotal; }, 0);
    var delivery = subtotal === 0 || subtotal >= MF.SITE.freeDeliveryThreshold ? 0 : MF.SITE.deliveryFee;
    return {
      lines: lines,
      count: lines.reduce(function (sum, l) { return sum + l.qty; }, 0),
      subtotal: subtotal,
      delivery: delivery,
      total: subtotal + delivery,
      freeRemaining: Math.max(0, MF.SITE.freeDeliveryThreshold - subtotal),
    };
  }

  function capacity(product) {
    var first = String(product.subtitle || '').split('·')[0].trim();
    return /^\d+\s?(Go|To)$/i.test(first) ? first : '';
  }

  function defaultVariant(product) {
    var cap = capacity(product);
    var color = product.colors && product.colors.length ? product.colors[0].name : '';
    if (cap && color) return cap + ' · ' + color;
    if (color) return color;
    return product.subtitle || '';
  }

  MF.cart = {
    read: readCart,
    write: writeCart,
    add: addToCart,
    setQty: setQty,
    remove: removeFromCart,
    clear: clearCart,
    count: cartCount,
    details: cartDetails,
    updateCount: updateCartCount,
  };
  MF.capacity = capacity;
  MF.defaultVariant = defaultVariant;

  MF.orderMessage = function (lines, totals, customer) {
    var rows = lines.map(function (line) {
      return '• ' + line.qty + ' × ' + line.product.name + ' — ' + line.variant + ' — ' + MF.formatPrice(line.lineTotal);
    });
    var text = ['Bonjour MF Business 👋', 'Je souhaite passer commande :', ''].concat(rows);
    text.push('');
    text.push('Sous-total : ' + MF.formatPrice(totals.subtotal));
    text.push('Livraison : ' + (totals.delivery === 0 ? 'offerte' : MF.formatPrice(totals.delivery)));
    text.push('Total : ' + MF.formatPrice(totals.total));
    if (customer && (customer.name || customer.phone || customer.city)) {
      text.push('');
      if (customer.name) text.push('Nom : ' + customer.name);
      if (customer.phone) text.push('Téléphone : ' + customer.phone);
      if (customer.city) text.push('Ville : ' + customer.city);
    }
    text.push('');
    text.push('Merci de me confirmer la disponibilité et le délai de livraison.');
    return text.join('\n');
  };

  /* ---------------------------------------------------------- carte produit */
  function stars(rating) {
    return '<span class="rating" aria-label="Note de ' + String(rating).replace('.', ',') + ' sur 5">' +
      '<svg class="rating__star" viewBox="0 0 20 20" aria-hidden="true"><path d="M10 1.6l2.6 5.3 5.8.8-4.2 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8L1.6 7.7l5.8-.8z"/></svg>' +
      '<strong>' + String(rating).replace('.', ',') + '</strong></span>';
  }

  function productCard(product, index) {
    var badge = product.badge
      ? '<span class="badge badge--' + escapeHtml(product.badgeTone || 'new') + '">' + escapeHtml(product.badge) + '</span>'
      : '';
    var old = product.oldPrice
      ? '<s class="price__old">' + MF.formatPrice(product.oldPrice) + '</s>'
      : '';
    return '' +
      '<article class="product-card" data-reveal style="--reveal-delay:' + ((index || 0) % 4) * 70 + 'ms">' +
        '<div class="product-card__media' + (product.category === 'audio' || product.category === 'accessoires' ? ' product-card__media--photo' : '') + '" style="--tint-a:' + product.tint[0] + ';--tint-b:' + product.tint[1] + '">' +
          '<a class="product-card__media-link" href="produit.html?id=' + encodeURIComponent(product.id) + '" aria-label="Voir ' + escapeHtml(product.name) + '">' +
            '<img src="' + escapeHtml(product.image || ('assets/img/products/' + product.id + '.svg')) + '" alt="' + escapeHtml(product.name + ' — ' + product.brand) + '" width="800" height="800" loading="lazy">' +
          '</a>' +
          badge +
          '<button class="product-card__quick" type="button" data-add-to-cart data-id="' + escapeHtml(product.id) + '" aria-label="Ajouter ' + escapeHtml(product.name) + ' au panier">' +
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>' +
          '</button>' +
        '</div>' +
        '<div class="product-card__body">' +
          '<p class="product-card__brand">' + escapeHtml(product.brand) + '</p>' +
          '<h3 class="product-card__name"><a href="produit.html?id=' + encodeURIComponent(product.id) + '">' + escapeHtml(product.name) + '</a></h3>' +
          '<p class="product-card__meta">' + escapeHtml(product.subtitle) + '</p>' +
          '<div class="product-card__rating">' + stars(product.rating) + '<span class="rating__count">(' + product.reviews + ')</span></div>' +
          '<div class="product-card__price"><strong class="price">' + MF.formatPrice(product.price) + '</strong>' + old + '</div>' +
        '</div>' +
      '</article>';
  }

  MF.productCard = productCard;
  MF.stars = stars;

  /* ---------------------------------------------------------------- toasts */
  function toast(message, tone, action) {
    var stack = qs('[data-toasts]');
    if (!stack) return;
    var el = document.createElement('div');
    el.className = 'toast toast--' + (tone || 'default');
    el.setAttribute('role', 'status');
    el.innerHTML = '<span class="toast__dot" aria-hidden="true"></span>' +
      '<p>' + escapeHtml(message) + '</p>' +
      (action ? '<a class="toast__action" href="' + escapeHtml(action.href) + '">' + escapeHtml(action.label) + '</a>' : '');
    stack.appendChild(el);
    requestAnimationFrame(function () { el.classList.add('is-in'); });
    setTimeout(function () {
      el.classList.remove('is-in');
      setTimeout(function () { el.remove(); }, 300);
    }, 3800);
  }
  MF.toast = toast;

  /* ------------------------------------------------------- en-tête & menu */
  function initHeader() {
    var body = document.body;
    var burger = qs('[data-menu-toggle]');
    var nav = qs('#site-nav');
    var overlay = qs('[data-nav-overlay]');
    var searchToggle = qs('[data-search-toggle]');
    var searchPanel = qs('#search-panel');
    var searchInput = qs('#site-search');
    var header = qs('[data-header]');

    /* L'overlay doit vivre dans le contexte d'empilement de l'en-tête pour
       rester sous le tiroir de navigation, lui aussi enfant de l'en-tête. */
    if (overlay && header && overlay.parentNode !== header) header.appendChild(overlay);

    function setMenu(open) {
      if (!nav || !burger) return;
      body.classList.toggle('nav-open', open);
      nav.classList.toggle('is-open', open);
      burger.setAttribute('aria-expanded', String(open));
      burger.setAttribute('aria-label', open ? 'Fermer le menu' : 'Ouvrir le menu');
      if (overlay) overlay.hidden = !open;
      if (open) {
        var first = qs('a, button', nav);
        if (first) setTimeout(function () { first.focus({ preventScroll: true }); }, 80);
      }
    }

    if (burger) {
      burger.addEventListener('click', function () {
        setMenu(!nav.classList.contains('is-open'));
      });
    }
    if (overlay) overlay.addEventListener('click', function () { setMenu(false); });

    if (nav && !qs('.nav__close', nav)) {
      var closeBtn = document.createElement('button');
      closeBtn.type = 'button';
      closeBtn.className = 'nav__close';
      closeBtn.setAttribute('aria-label', 'Fermer le menu');
      closeBtn.innerHTML = '✕';
      closeBtn.addEventListener('click', function () {
        setMenu(false);
        if (burger) burger.focus();
      });
      nav.insertBefore(closeBtn, nav.firstChild);
    }

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        if (nav && nav.classList.contains('is-open')) { setMenu(false); if (burger) burger.focus(); }
        if (searchPanel && !searchPanel.hidden) closeSearch();
      }
    });

    qsa('#site-nav a').forEach(function (link) {
      link.addEventListener('click', function () { if (window.innerWidth < 981) setMenu(false); });
    });

    function openSearch() {
      if (!searchPanel) return;
      searchPanel.hidden = false;
      searchToggle.setAttribute('aria-expanded', 'true');
      body.classList.add('search-open');
      setTimeout(function () { if (searchInput) searchInput.focus(); }, 40);
    }
    function closeSearch() {
      if (!searchPanel) return;
      searchPanel.hidden = true;
      searchToggle.setAttribute('aria-expanded', 'false');
      body.classList.remove('search-open');
    }
    if (searchToggle && searchPanel) {
      searchToggle.addEventListener('click', function () {
        if (searchPanel.hidden) openSearch(); else closeSearch();
      });
      document.addEventListener('click', function (e) {
        if (!searchPanel.hidden && !searchPanel.contains(e.target) && !searchToggle.contains(e.target)) closeSearch();
      });
    }

    function onScroll() {
      if (!header) return;
      header.classList.toggle('is-stuck', window.scrollY > 10);
    }
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });

    updateCartCount();
  }

  /* ------------------------------------------------------------- animations */
  var revealObserver = null;
  function initReveal() {
    var items = qsa('[data-reveal]:not(.is-visible)');
    if (!items.length) return;
    if (!('IntersectionObserver' in window) || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      items.forEach(function (el) { el.classList.add('is-visible'); });
      return;
    }
    if (!revealObserver) {
      revealObserver = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            revealObserver.unobserve(entry.target);
          }
        });
      }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    }
    items.forEach(function (el) { revealObserver.observe(el); });
  }
  MF.initReveal = initReveal;

  /* ------------------------------------------------------------- formulaire */
  function initNewsletter() {
    qsa('[data-newsletter]').forEach(function (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        var input = qs('input[type="email"]', form);
        if (!input || !input.value.trim() || input.value.indexOf('@') < 0) {
          if (input) input.focus();
          toast('Entrez une adresse e-mail valide.', 'error');
          return;
        }
        toast('Merci ! Vous recevrez nos arrivages en avant-première.', 'success');
        form.reset();
      });
    });
  }

  function initYear() {
    qsa('[data-year]').forEach(function (el) { el.textContent = String(new Date().getFullYear()); });
  }

  /* Coordonnées : une seule source de vérité dans MF.SITE (data.js). */
  function syncSiteDetails() {
    qsa('a[href^="tel:"]').forEach(function (a) {
      a.setAttribute('href', 'tel:' + MF.SITE.phoneRaw);
      if (/^[+0-9 ().-]{8,}$/.test(a.textContent.trim())) a.textContent = MF.SITE.phone;
    });
    qsa('a[href*="wa.me/"]').forEach(function (a) {
      var href = a.getAttribute('href').replace(/(wa\.me\/)\d+/, '$1' + MF.SITE.whatsapp);
      if (/text=Bonjour%20MF%20Business/i.test(href)) {
        href = href.split('?')[0] + '?text=' + encodeURIComponent(MF.SITE.defaultMessage);
      }
      a.setAttribute('href', href);
    });
    qsa('a[href^="mailto:"]').forEach(function (a) {
      a.setAttribute('href', 'mailto:' + MF.SITE.email);
      if (a.textContent.indexOf('@') > -1) a.textContent = MF.SITE.email;
    });
  }

  function initNewsletterLink() {
    qsa('[data-whatsapp]').forEach(function (el) {
      el.setAttribute('href', MF.whatsappLink(el.getAttribute('data-whatsapp') || MF.SITE.defaultMessage));
      el.setAttribute('target', '_blank');
      el.setAttribute('rel', 'noopener');
    });
  }

  function syncTotals() {
    var total = (MF.PRODUCTS || []).length;
    qsa('[data-total-products]').forEach(function (el) { el.textContent = String(total); });
    qsa('[data-count]').forEach(function (el) {
      var n = MF.categoryCount(el.getAttribute('data-count'));
      el.textContent = el.hasAttribute('data-pad') ? String(n).padStart(2, '0') : String(n);
    });
  }

  /* ------------------------------------------------------- ajout au panier */
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-add-to-cart]');
    if (!btn) return;
    e.preventDefault();
    var id = btn.getAttribute('data-id');
    var qty = Number(btn.getAttribute('data-qty') || 1);
    var variant = btn.getAttribute('data-variant') || '';
    addToCart(id, qty, variant);
    btn.classList.add('is-added');
    setTimeout(function () { btn.classList.remove('is-added'); }, 700);
  });

  /* --------------------------------------------------------------- démarrage */
  document.addEventListener('DOMContentLoaded', function () {
    syncSiteDetails();
    syncTotals();
    initHeader();
    initNewsletter();
    initYear();
    initNewsletterLink();
    initReveal();
  });
})();
