/* MF Business — panier */
(function () {
  'use strict';

  var view, empty, itemsWrap, summaryLines, totalEl, progressBar, progressText, checkout;

  function lineMarkup(line) {
    var p = line.product;
    var variant = line.variant || p.subtitle;
    return '' +
      '<article class="cart-item">' +
        '<a class="cart-item__media' + (p.category === 'audio' || p.category === 'accessoires' ? ' cart-item__media--photo' : '') + '" href="produit.html?id=' + encodeURIComponent(p.id) + '" style="--tint-a:' + p.tint[0] + ';--tint-b:' + p.tint[1] + '" aria-label="Voir ' + MF.escapeHtml(p.name) + '">' +
          '<img src="' + p.image + '" alt="" width="800" height="800" loading="lazy">' +
        '</a>' +
        '<div class="cart-item__body">' +
          '<p class="cart-item__brand">' + MF.escapeHtml(p.brand) + '</p>' +
          '<h2 class="cart-item__name"><a href="produit.html?id=' + encodeURIComponent(p.id) + '">' + MF.escapeHtml(p.name) + '</a></h2>' +
          '<p class="cart-item__variant">' + MF.escapeHtml(variant) + '</p>' +
        '</div>' +
        '<div class="cart-item__foot">' +
          '<div class="qty qty--sm">' +
            '<button type="button" data-cart-step="-1" data-id="' + p.id + '" data-variant="' + MF.escapeHtml(variant) + '" aria-label="Diminuer la quantité de ' + MF.escapeHtml(p.name) + '">−</button>' +
            '<input type="number" value="' + line.qty + '" min="1" max="20" inputmode="numeric" data-qty-input data-id="' + p.id + '" data-variant="' + MF.escapeHtml(variant) + '" aria-label="Quantité de ' + MF.escapeHtml(p.name) + '">' +
            '<button type="button" data-cart-step="1" data-id="' + p.id + '" data-variant="' + MF.escapeHtml(variant) + '" aria-label="Augmenter la quantité de ' + MF.escapeHtml(p.name) + '">+</button>' +
          '</div>' +
          '<strong class="cart-item__price">' + MF.formatPrice(line.lineTotal) + '</strong>' +
          '<button class="cart-item__remove" type="button" data-remove data-id="' + p.id + '" data-variant="' + MF.escapeHtml(variant) + '">' +
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M9 7V5h6v2M7 7l1 13h8l1-13"/></svg>' +
            'Retirer' +
          '</button>' +
        '</div>' +
      '</article>';
  }

  function render() {
    var details = MF.cart.details();

    if (!details.lines.length) {
      if (view) view.hidden = true;
      if (empty) empty.hidden = false;
      return;
    }

    if (view) view.hidden = false;
    if (empty) empty.hidden = true;
    if (itemsWrap) itemsWrap.innerHTML = details.lines.map(lineMarkup).join('');

    var savings = details.lines.reduce(function (sum, line) {
      return sum + (line.product.oldPrice ? (line.product.oldPrice - line.product.price) * line.qty : 0);
    }, 0);

    if (summaryLines) {
      var lines = '';
      lines += '<div><span class="muted">Sous-total (' + details.count + (details.count > 1 ? ' articles' : ' article') + ')</span><span>' + MF.formatPrice(details.subtotal) + '</span></div>';
      lines += '<div><span class="muted">Livraison</span><span>' + (details.delivery === 0 ? 'Offerte' : MF.formatPrice(details.delivery)) + '</span></div>';
      if (savings > 0) {
        lines += '<div><span class="muted">Vous économisez</span><span style="color:var(--success);font-weight:600">−' + MF.formatPrice(savings) + '</span></div>';
      }
      summaryLines.innerHTML = lines;
    }

    if (totalEl) totalEl.textContent = MF.formatPrice(details.total);

    if (progressBar && progressText) {
      var ratio = Math.min(1, details.subtotal / MF.SITE.freeDeliveryThreshold);
      progressBar.style.width = (ratio * 100).toFixed(1) + '%';
      progressText.textContent = details.freeRemaining > 0
        ? 'Plus que ' + MF.formatPrice(details.freeRemaining) + ' pour la livraison offerte.'
        : 'Livraison offerte sur cette commande.';
    }

    if (checkout) {
      checkout.href = MF.whatsappLink(MF.orderMessage(details.lines, details));
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    view = MF.qs('[data-cart-view]');
    empty = MF.qs('[data-cart-empty]');
    itemsWrap = MF.qs('[data-cart-items]');
    summaryLines = MF.qs('[data-summary-lines]');
    totalEl = MF.qs('[data-total]');
    progressBar = MF.qs('[data-progress]');
    progressText = MF.qs('[data-progress-text]');
    checkout = MF.qs('[data-checkout]');

    render();

    if (itemsWrap) {
      itemsWrap.addEventListener('click', function (e) {
        var step = e.target.closest('[data-cart-step]');
        if (step) {
          var id = step.getAttribute('data-id');
          var variant = step.getAttribute('data-variant');
          var line = MF.cart.read().find(function (item) { return item.id === id && item.variant === variant; });
          if (!line) return;
          MF.cart.setQty(id, variant, line.qty + Number(step.getAttribute('data-cart-step')));
          return;
        }
        var remove = e.target.closest('[data-remove]');
        if (remove) {
          var product = MF.getProduct(remove.getAttribute('data-id'));
          MF.cart.remove(remove.getAttribute('data-id'), remove.getAttribute('data-variant'));
          MF.toast((product ? product.name : 'Article') + ' retiré du panier.', 'default');
        }
      });

      itemsWrap.addEventListener('change', function (e) {
        var input = e.target.closest('[data-qty-input]');
        if (!input) return;
        var value = Math.max(1, Math.min(20, Math.round(Number(input.value) || 1)));
        MF.cart.setQty(input.getAttribute('data-id'), input.getAttribute('data-variant'), value);
      });
    }

    var clear = MF.qs('[data-clear-cart]');
    if (clear) {
      clear.addEventListener('click', function () {
        if (!window.confirm('Vider entièrement le panier ?')) return;
        MF.cart.clear();
        MF.toast('Le panier a été vidé.', 'default');
      });
    }

    document.addEventListener('mf:cart', render);
  });
})();
