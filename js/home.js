/* MF Business — page d'accueil */
(function () {
  'use strict';
  document.addEventListener('DOMContentLoaded', function () {
    var grid = document.querySelector('[data-featured]');
    if (!grid) return;
    var featured = (MF.PRODUCTS || []).filter(function (p) { return p.featured; }).slice(0, 8);
    grid.innerHTML = featured.map(MF.productCard).join('');
    MF.initReveal();
  });
})();
