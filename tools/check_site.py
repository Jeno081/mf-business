#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contrôles statiques : liens, assets, ids, balises, catalogue."""
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parent.parent
PAGES = sorted(ROOT.glob("*.html"))
errors = []
warnings = []


class Checker(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.ids = []
        self.links = []
        self.assets = []
        self.has_main = False
        self.imgs_without_alt = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "main":
            self.has_main = True
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag in ("img", "script") and attrs.get("src"):
            self.assets.append(attrs["src"])
        if tag == "link" and attrs.get("href"):
            self.assets.append(attrs["href"])
        if tag == "img" and "alt" not in attrs:
            self.imgs_without_alt += 1


def local_target(base, url):
    if not url or url.startswith(("http://", "https://", "mailto:", "tel:", "data:", "#", "javascript:")):
        return None
    parsed = urlparse(url)
    if parsed.scheme or parsed.netloc:
        return None
    path = unquote(parsed.path)
    if not path:
        return None
    return (base / path).resolve()


for page in PAGES:
    parser = Checker(page)
    parser.feed(page.read_text(encoding="utf-8"))
    dupes = {i for i in parser.ids if parser.ids.count(i) > 1}
    if dupes:
        errors.append(f"{page.name}: ids dupliqués {sorted(dupes)}")
    if not parser.has_main:
        errors.append(f"{page.name}: pas de <main>")
    if parser.imgs_without_alt:
        errors.append(f"{page.name}: {parser.imgs_without_alt} image(s) sans alt")
    for href in parser.links:
        target = local_target(page.parent, href)
        if target and not target.exists():
            errors.append(f"{page.name}: lien mort {href}")
    for src in parser.assets:
        target = local_target(page.parent, src)
        if target and not target.exists():
            errors.append(f"{page.name}: asset manquant {src}")
    text = page.read_text(encoding="utf-8")
    if "fonts.googleapis.com" not in text:
        warnings.append(f"{page.name}: polices Google absentes")
    if 'lang="fr"' not in text:
        errors.append(f"{page.name}: langue absente")

catalog = json.loads((ROOT / "data" / "catalog.json").read_text(encoding="utf-8"))
if len(catalog) < 150:
    warnings.append(f"{len(catalog)} produits détectés (150+ attendus)")
for item in catalog:
    image = ROOT / item["image"]
    if not image.exists():
        errors.append(f"image produit manquante : {item['image']}")
    if not item.get("specs"):
        errors.append(f"{item['id']}: specs vides")

if not (ROOT / "js" / "catalog.js").exists():
    errors.append("js/catalog.js absent")

for page in PAGES:
    text = page.read_text(encoding="utf-8")
    if "FCFA" in text:
        errors.append(f"{page.name}: FCFA restant")
    if "+237" in text:
        errors.append(f"{page.name}: ancien numéro +237")
    if "Douala" in text or "Yaoundé" in text:
        errors.append(f"{page.name}: ancienne ville")

css = (ROOT / "css" / "style.css").read_text(encoding="utf-8")
if css.count("{") != css.count("}"):
    errors.append(f"style.css : accolades déséquilibrées ({css.count('{')} / {css.count('}')})")

print(f"Pages analysées : {len(PAGES)}")
print(f"Produits : {len(catalog)}")
print(f"Images : {len([i for i in catalog if i.get('image')])}")
print(f"Erreurs : {len(errors)}")
for e in errors:
    print("  ERREUR:", e)
print(f"Avertissements : {len(warnings)}")
for w in warnings:
    print("  NOTE:", w)
raise SystemExit(1 if errors else 0)
