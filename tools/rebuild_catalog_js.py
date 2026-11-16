#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Régénère js/catalog.js à partir de data/catalog.json."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
data = json.loads((ROOT / "data" / "catalog.json").read_text(encoding="utf-8"))
if not isinstance(data, list) or not data:
    raise SystemExit("catalog.json vide ou invalide")

required = {"id", "name", "brand", "category", "price", "image"}
for item in data:
    missing = required - set(item)
    if missing:
        raise SystemExit(f"{item.get('id', '?')} : champs manquants {sorted(missing)}")

js = "/* Catalogue MF Business — généré par tools/rebuild_catalog_js.py */\nMF.PRODUCTS = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n"
(ROOT / "js" / "catalog.js").write_text(js, encoding="utf-8")
print(f"{len(data)} produits écrits dans js/catalog.js")
