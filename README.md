# MF Business — Maison Forlife Business

Boutique en ligne statique pour **MF Business**, maison de téléphones et
d’accessoires à **Kinshasa (RDC)**. Le site est en français, les prix sont en
**dollars américains (USD)**, et la commande se finalise sur **WhatsApp** avec
paiement à la livraison.

> « Forlife », pour la technologie qui vous accompagne toute la vie.
> « Business », pour les outils qui font avancer vos projets.

---

## 1. Lancer le site

**Le plus simple :** double-cliquez sur `index.html`. Le panier, les filtres,
les fiches produit et les liens WhatsApp fonctionnent directement depuis le
disque.

**Version recommandée** (plus confortable, et nécessaire si vous ajoutez un
jour des modules JavaScript) :

```bash
python -m http.server 4173
```

Puis ouvrez <http://localhost:4173>.

---

## 2. Ce que contient le site

- **188 références** réparties entre Apple, Samsung, Huawei, Google, Xiaomi,
  Tecno, Itel, Infinix, Oppo, Realme, OnePlus, Honor, JBL, Anker et MF Atelier.
- **144 smartphones**, **23 tablettes**, **8 produits audio** et **13 accessoires**.
- **Recherche par marque ou modèle** : « Samsung », « Fold », « iPhone 15 »,
  « S25 Ultra », « Camon 50 »…
- **Filtres** : catégorie, marque (16 marques), budget en USD, tri par prix,
  note ou nouveauté.
- **Fiches produit** : photo réelle, prix USD, coloris, quantité, écran, puce,
  mémoire, batterie, photo, système, produits liés.
- **Panier persistant** : quantités, suppression, livraison offerte dès 150 $,
  total en USD, message WhatsApp prérempli.
- **Contact** : formulaire validé → WhatsApp, téléphone, e-mail, showroom,
  FAQ.
- **Mobile** : menu latéral, filtres en tiroir, recherche, panier.
- **Accessibilité** : lien d’évitement, labels, `aria-*`, focus visible,
  respect de `prefers-reduced-motion`.

### Contacts intégrés

| Canal | Valeur |
| --- | --- |
| WhatsApp | `+243 811 860 632` — `https://wa.me/243811860632` |
| E-mail | `jenovicmulomba@gmail.com` |
| Adresse | Avenue de la République du Tchad, B.P. 68, 5D, Av. Rep Du Tchad, Kinshasa |
| Livraison | 5 $, offerte dès 150 $ |

---

## 3. Stack technique

**HTML5 + CSS3 + JavaScript vanilla, sans framework ni étape de build.**

| Critère | Ce choix |
| --- | --- |
| Vitesse | Aucun bundle, aucune hydratation : affichage immédiat. |
| Hébergement | N’importe quel hébergement statique gratuit. |
| Maintenance | Des fichiers lisibles, modifiables sans React ni CLI. |
| SEO | HTML sémantique, métadonnées, données structurées produit. |
| Évolution | Un backend de paiement peut être ajouté plus tard sans refaire le design. |

Un framework serait justifié pour un compte client, un stock temps réel ou un
paiement intégré. Ce n’est pas nécessaire pour 188 fiches et une commande
WhatsApp.

---

## 4. Arborescence

```
mf-business-site/
├── index.html              Accueil
├── catalogue.html          Catalogue filtrable
├── produit.html            Fiche produit (?id=iphone-18-pro-max)
├── panier.html             Panier + commande WhatsApp
├── contact.html            Formulaire, showroom, FAQ
├── a-propos.html           Histoire et signification du nom
├── css/style.css           Design system complet (mobile-first)
├── js/
│   ├── data.js             ★ Configuration : contacts, livraison, catégories
│   ├── catalog.js          Catalogue généré (188 produits) — ne pas éditer à la main
│   ├── app.js              Panier, en-tête, cartes, toasts
│   ├── home.js             Sélection de l’accueil
│   ├── catalogue.js        Recherche, filtres, tri, URL
│   ├── produit.js          Fiche produit, coloris, onglets
│   ├── panier.js           Panier et message WhatsApp
│   └── contact.js          Validation du formulaire
├── data/
│   └── catalog.json        ★ Source du catalogue (188 produits)
├── assets/img/
│   ├── logo-monogram.png
│   ├── logo-full-white.png
│   └── products/photos/*.webp   188 photos produit
├── tools/
│   ├── rebuild_catalog_js.py   Régénère js/catalog.js depuis catalog.json
│   ├── catalog_build.py        Scraper de secours (GSMArena)
│   └── check_site.py           Contrôle liens, assets, ids, balises
├── CREDITS.md              Sources des visuels
└── README.md
```

---

## 5. Identité visuelle

| Élément | Choix |
| --- | --- |
| Noir profond | `#0F0F0F` — la maison, la confiance |
| Ivoire | `#F3EFE6` / `#FCFAF5` — la chaleur |
| Graphite | `#2B2B2B` — boutons et survols |
| Titres | **Bodoni Moda**, serif Didone aligné sur le logo |
| Texte | **DM Sans**, lisible et contemporain |
| Logo | Monogramme MF cerclé, wordmark Maison Forlife, logo complet noir/blanc |

---

## 6. Personnaliser

### 6.1 Coordonnées, livraison, devise

Ouvrez `js/data.js`, objet `MF.SITE` :

```js
MF.SITE = {
  city: 'Kinshasa',
  address: 'Avenue de la République du Tchad, B.P. 68, 5D, Av. Rep Du Tchad, Kinshasa.',
  phone: '+243 811 860 632',
  phoneRaw: '+243811860632',
  whatsapp: '243811860632',   // sans + ni espaces
  email: 'jenovicmulomba@gmail.com',
  deliveryFee: 5,
  freeDeliveryThreshold: 150,
  currency: 'USD',
  currencySymbol: '$',
};
```

`app.js` propage le téléphone, l’e-mail, le numéro WhatsApp et le message
d’accueil à tous les liens. Les prix sont formatés par `MF.formatPrice`.

### 6.2 Catalogue

La source est **`data/catalog.json`**. Chaque produit contient :

- `id`, `name`, `brand`, `category` (`smartphones`, `tablettes`, `audio`, `accessoires`)
- `series`, `price`, `badge`, `badgeTone`, `featured`
- `subtitle` (stockage · coloris), `colors`, `tint`
- `description`, `features`, `specs`, `keywords`
- `image`, `rating`, `reviews`, `stock`

Après une modification :

```bash
python tools/rebuild_catalog_js.py
```

Le script réécrit `js/catalog.js` et met à jour les compteurs des pages.

### 6.3 Photos

Les photos sont dans `assets/img/products/photos/`. Pour remplacer un visuel,
déposez une image carrée (1000 × 1000 px, fond clair) et mettez à jour le champ
`image` du produit dans `catalog.json`.

Les images actuelles proviennent de fiches GSMArena (téléphones, tablettes) et de
Wikimedia Commons (audio, montres, accessoires) : elles conviennent pour la
démonstration, mais **pour une publication commerciale, utilisez vos propres
photos ou des visuels sous licence**. Voir `CREDITS.md`.

### 6.4 Couleurs et logo

Variables `:root` dans `css/style.css`. Logo : `assets/img/logo-monogram.png`,
`logo-full-black.png`, `logo-full-white.png`, `favicon.png`.

---

## 7. Recherche et filtres

- Index basé sur le **nom, la marque, la série, le stockage et le coloris**.
- Recherche multi-mots : « iPhone 15 » ne sort que la série 15 ; « Fold » sort
  les Galaxy Z Fold, Pixel Fold et Xiaomi Fold ; « Samsung » sort les 40
  références Samsung.
- Filtres marque/catégorie/budget, tri, filtres actifs, état dans l’URL.
- Sur mobile, les filtres s’ouvrent dans un tiroir.

---

## 8. Tests effectués

- **39 vérifications automatisées** : catalogue 188, 8 produits en vedette,
  recherche « Fold »/« Samsung »/« iPhone 15 », filtres, tri, panier, total
  USD, lien WhatsApp, téléphone/e-mail, validation du formulaire.
- Aucune erreur JavaScript.
- Aucun débordement horizontal à 390 px ni 1440 px.
- Toutes les images et tous les liens locaux existent.
- Ouverture directe en `file://` vérifiée.

Relancer les contrôles :

```bash
python tools/check_site.py
```

---

## 9. Limites assumées

- **Pas de paiement en ligne** : commande confirmée sur WhatsApp, réglée à la
  livraison ou en boutique.
- **Prix indicatifs** : à valider selon vos fournisseurs et le marché de
  Kinshasa.
- **Photos de démonstration** : voir la note sur les droits dans `CREDITS.md`.
- **Newsletter simulée** : pas de backend, le formulaire affiche un message.
- **Avis clients** : exemples à remplacer par de vrais témoignages.
- **Stock** : indicatif, WhatsApp reste la source de vérité.

---

## 10. Hébergement

| Option | Avantages | Inconvénients |
| --- | --- | --- |
| **Netlify** (gratuit) | Glisser-déposer, HTTPS, domaine personnalisé | Limites du plan gratuit |
| **Cloudflare Pages** | CDN rapide, bande passante illimitée | Interface plus technique |
| **Vercel** | Déploiements automatiques, aperçus | Plan Hobby non commercial ; Pro ≈ 20 $/mois |
| **GitHub Pages** | Gratuit, versionné | Dépôt public, plus technique |
| **Hébergeur classique** | E-mail, support, tout au même endroit | Configuration manuelle |

**Recommandation :** Netlify ou Cloudflare Pages + un domaine `mfbusiness.cm`
ou `.com`. Aucun serveur n’est nécessaire.

---

## 11. Prochaines étapes

1. Valider les prix et les modèles avec vos fournisseurs.
2. Remplacer les photos de démonstration par vos propres visuels.
3. Ajouter votre adresse exacte et vos horaires définitifs.
4. Brancher un paiement Mobile Money (Airtel Money, M-Pesa) via
   un agrégateur et un petit backend.
5. Ajouter une politique de confidentialité si vous activez des statistiques.

---

*Site conçu et développé pour MF Business — Maison Forlife Business.*
