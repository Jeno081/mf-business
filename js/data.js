/* ==========================================================================
   MF BUSINESS — Configuration de la boutique
   Les produits sont dans js/catalog.js (catalogue généré, 188 références).
   ========================================================================== */

window.MF = window.MF || {};

MF.SITE = {
  name: 'MF Business',
  fullName: 'Maison Forlife Business',
  baseline: 'La tech, avec soin.',
  city: 'Kinshasa',
  country: 'RDC',
  address: 'Avenue de la République du Tchad, B.P. 68, 5D, Av. Rep Du Tchad, Kinshasa.',
  phone: '+243 811 860 632',
  phoneRaw: '+243811860632',
  whatsapp: '243811860632',
  email: 'jenovicmulomba@gmail.com',
  hours: 'Lundi – samedi · 8h00 – 19h00',
  deliveryFee: 5,
  freeDeliveryThreshold: 150,
  deliveryNote: 'Livraison à Kinshasa sous 24–48 h. Paiement à la livraison.',
  currency: 'USD',
  currencySymbol: '$',
  defaultMessage: 'Bonjour MF Business, je suis intéressé par…',
  instagram: 'https://www.instagram.com/',
  facebook: 'https://www.facebook.com/',
  tiktok: 'https://www.tiktok.com/',
  mapUrl: 'https://www.google.com/maps/search/?api=1&query=Avenue%20de%20la%20R%C3%A9publique%20du%20Tchad%2C%20Kinshasa%2C%20RDC',
};

MF.CATEGORIES = [
  { id: 'smartphones', label: 'Smartphones', short: 'Téléphones', blurb: 'iPhone, Samsung, Huawei, Google, Xiaomi, Tecno, Itel', icon: 'phone' },
  { id: 'tablettes', label: 'Tablettes', short: 'Tablettes', blurb: 'iPad, Galaxy Tab, MatePad et tablettes Android', icon: 'tablet' },
  { id: 'audio', label: 'Audio', short: 'Audio', blurb: 'Écouteurs, casques et enceintes nomades', icon: 'audio' },
  { id: 'accessoires', label: 'Accessoires', short: 'Accessoires', blurb: 'Pochettes, coques, chargeurs, câbles et montres', icon: 'plug' },
];

MF.BRANDS = [
  'Apple', 'Samsung', 'Huawei', 'Google', 'Xiaomi', 'Tecno', 'Itel', 'Infinix',
  'Oppo', 'Realme', 'OnePlus', 'Honor', 'Belkin', 'JBL', 'Anker', 'MF Atelier',
];

/* --------------------------------------------------------------------------
   Prix en dollars américains (USD). Format français : 1 299 $
   -------------------------------------------------------------------------- */
MF.formatPrice = function (value) {
  var n = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 }).format(value);
  return n.replace(/[\u202f\u00a0]/g, '\u00a0') + '\u00a0$';
};

MF.formatNumber = function (value) {
  return new Intl.NumberFormat('fr-FR').format(value);
};

MF.getProduct = function (id) {
  return (MF.PRODUCTS || []).find(function (p) { return p.id === id; }) || null;
};

MF.getCategory = function (id) {
  return MF.CATEGORIES.find(function (c) { return c.id === id; }) || null;
};

MF.categoryCount = function (id) {
  return (MF.PRODUCTS || []).filter(function (p) { return p.category === id; }).length;
};

MF.relatedProducts = function (product, limit) {
  var all = MF.PRODUCTS || [];
  var same = all.filter(function (p) { return p.id !== product.id && p.category === product.category; });
  var others = all.filter(function (p) { return p.id !== product.id && p.category !== product.category; });
  return same.concat(others).slice(0, limit || 4);
};

MF.whatsappLink = function (message) {
  return 'https://wa.me/' + MF.SITE.whatsapp + '?text=' + encodeURIComponent(message || MF.SITE.defaultMessage);
};
