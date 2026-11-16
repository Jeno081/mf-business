#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Construit le catalogue MF Business à partir de GSMArena.

- récupère les fiches modèles (specs + visuel),
- télécharge les visuels en local et les convertit en WebP,
- génère js/catalog.js et CREDITS.md,
- laisse un placeholder propre si une image manque.

Usage :
    python tools/catalog_build.py --map-only
    python tools/catalog_build.py
    python tools/catalog_build.py --limit 5
"""
from __future__ import annotations

import argparse
import hashlib
import html as html_mod
import io
import json
import re
import shutil
import time
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.parse import urljoin

from lxml import html
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = ROOT / "assets" / "img" / "products"
PHOTO_DIR = IMG_DIR / "photos"
DATA_DIR = ROOT / "data"
for folder in (IMG_DIR, PHOTO_DIR, DATA_DIR):
    folder.mkdir(parents=True, exist_ok=True)

BASE = "https://www.gsmarena.com/"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
    "Referer": BASE,
}

BRAND_PAGES = {
    "Apple": ("apple", 48, 3),
    "Samsung": ("samsung", 9, 3),
    "Huawei": ("huawei", 58, 3),
    "Google": ("google", 107, 1),
    "Xiaomi": ("xiaomi", 80, 2),
    "Tecno": ("tecno", 120, 2),
    "Itel": ("itel", 131, 2),
    "Infinix": ("infinix", 119, 2),
    "Oppo": ("oppo", 82, 2),
    "Realme": ("realme", 118, 2),
    "OnePlus": ("oneplus", 95, 2),
    "Honor": ("honor", 121, 2),
}

SELECTION = {
    "Apple": [
        "iPhone Duo", "iPhone 18 Pro Max", "iPhone 18 Pro",
        "iPhone 17 Pro Max", "iPhone 17 Pro", "iPhone Air", "iPhone 17", "iPhone 17e",
        "iPhone 16 Pro Max", "iPhone 16 Pro", "iPhone 16 Plus", "iPhone 16", "iPhone 16e",
        "iPhone 15 Pro Max", "iPhone 15 Pro", "iPhone 15", "iPhone 14", "iPhone 13",
        "iPhone SE (2022)",
        "iPad mini (2026)", "iPad Air 13 (2026)", "iPad Air 11 (2026)",
        "iPad Pro 13 (2025)", "iPad Pro 11 (2025)", "iPad (2025)", "iPad mini (2024)",
    ],
    "Samsung": [
        "Galaxy S26 Ultra", "Galaxy S26+", "Galaxy S26", "Galaxy S26 FE",
        "Galaxy S25 Ultra", "Galaxy S25+", "Galaxy S25", "Galaxy S25 FE", "Galaxy S25 Edge",
        "Galaxy S24 Ultra", "Galaxy S24+", "Galaxy S24", "Galaxy S24 FE",
        "Galaxy Z Fold8 Ultra", "Galaxy Z Fold8", "Galaxy Z Flip8",
        "Galaxy Z Fold7", "Galaxy Z Flip7",
        "Galaxy Z Fold6", "Galaxy Z Flip6", "Galaxy Z Fold5", "Galaxy Z Flip5",
        "Galaxy A57", "Galaxy A56", "Galaxy A55", "Galaxy A37", "Galaxy A36", "Galaxy A26",
        "Galaxy A17", "Galaxy A07",
        "Galaxy M47", "Galaxy M36",
        "Galaxy Tab S12 Ultra", "Galaxy Tab S12+", "Galaxy Tab S10 FE",
        "Galaxy Tab S9 FE", "Galaxy Tab A11+",
    ],
    "Huawei": [
        "Pura 90 Pro Max", "Pura 90 Pro", "Pura 90", "Pura 90 Plus",
        "Pura 80 Ultra", "Pura 80 Pro",
        "Pura 70 Ultra", "Pura 70 Pro", "Pura 70",
        "Mate 90 Pro Max", "Mate 90 Pro", "Mate 90",
        "Mate 80 Pro", "Mate 70 Pro", "Mate 60 Pro",
        "Mate XT 2 Ultimate", "Mate X7", "Mate X6", "Mate X5",
        "nova 16 Pro", "nova 16", "nova 13",
        "MatePad Pro 12 (2026)", "MatePad 11.5 (2026)",
    ],
    "Google": [
        "Pixel 11 Pro Fold", "Pixel 11 Pro XL", "Pixel 11 Pro", "Pixel 11",
        "Pixel 10 Pro Fold", "Pixel 10 Pro XL", "Pixel 10 Pro", "Pixel 10", "Pixel 10a",
        "Pixel 9 Pro XL", "Pixel 9 Pro", "Pixel 9", "Pixel 9a", "Pixel 9 Pro Fold",
        "Pixel 8 Pro", "Pixel 8", "Pixel 8a", "Pixel Fold", "Pixel Tablet",
    ],
    "Xiaomi": [
        "18 Pro Max", "18 Pro", "18 Fold", "17T Pro", "17T", "17 Max",
        "Redmi Note 17 Pro Max", "Redmi Note 17 Pro", "Redmi Note 17",
        "Poco F9 Ultra", "Poco F9 Pro", "Poco X8", "Pad 9 Pro",
    ],
    "Tecno": [
        "Camon 50 Ultra", "Camon 50 Pro", "Camon 50 4G",
        "Camon 40 Premier", "Camon 40 Pro", "Camon 40",
        "Pova 8 Pro", "Spark 50 Pro", "Megapad 2",
    ],
    "Itel": ["A300+", "Zeno 300", "Zeno 200", "A100 Pro", "Power 80", "S25 Ultra", "A80", "VistaTab 12"],
    "Infinix": [
        "Note 60 Ultra", "Note 60 Pro", "Note 60", "Hot 70 Pro", "Hot 60 Pro+",
        "Zero 40", "GT 50 Pro", "Xpad 30 Pro",
    ],
    "Oppo": ["Find X10 Pro Max", "Find X10", "Reno16 Pro", "Reno16", "A7 Pro", "Pad 6", "Find N6"],
    "Realme": ["GT 8 Pro", "16 Pro+", "16 Pro", "16", "Narzo 90", "Pad 3"],
    "OnePlus": ["16", "15", "15R", "Nord 6", "Pad 3 Pro"],
    "Honor": ["Magic9 Pro Max", "Magic9", "600 Pro", "X80 Pro Max", "Pad 20 Pro"],
}

FEATURED = {
    "iPhone 18 Pro Max", "Galaxy S26 Ultra", "Pixel 11 Pro", "Pura 90 Pro Max",
    "iPhone 17", "Galaxy Z Fold8", "Tecno Camon 50 Ultra", "iPad Pro 13 (2025)",
}

TINT = {
    "Apple": ("#F1E9DC", "#E2D3BE"),
    "Samsung": ("#EEEBF3", "#DCD5E7"),
    "Huawei": ("#F4EDE7", "#E6D7C9"),
    "Google": ("#EEF2EC", "#DCE5DD"),
    "Xiaomi": ("#FBEFE6", "#F3D9C6"),
    "Tecno": ("#E8F2EE", "#D4E8E0"),
    "Itel": ("#E9F1FB", "#D5E4F7"),
    "Infinix": ("#F0EDF7", "#DED6EF"),
    "Oppo": ("#EAF2EE", "#D6E8DF"),
    "Realme": ("#FDF0D9", "#F6DEB8"),
    "OnePlus": ("#FBE9E4", "#F5D3C9"),
    "Honor": ("#EDF0F4", "#DDE3EA"),
}

COLOR_HEX = {
    "black": "#1C1C1E", "noir": "#1C1C1E", "white": "#F1EFE8", "blanc": "#F1EFE8",
    "silver": "#C9C9C9", "argent": "#C9C9C9", "gray": "#8A8A8A", "grey": "#8A8A8A",
    "graphite": "#4A4A4C", "blue": "#2F5DA8", "bleu": "#2F5DA8", "navy": "#243B63",
    "green": "#2F5D50", "vert": "#2F5D50", "mint": "#BFD8C9", "mint green": "#BFD8C9",
    "purple": "#7A5A8E", "violet": "#7A5A8E", "lavender": "#C9B8D6",
    "gold": "#D9AE5F", "or": "#D9AE5F", "rose": "#D9A6A0", "pink": "#E3A7B4",
    "red": "#B23A3A", "rouge": "#B23A3A", "orange": "#D9773F", "coral": "#E07A5F",
    "titanium": "#B8B0A3", "titane": "#B8B0A3", "natural": "#B8B0A3",
    "desert": "#C8A57A", "graphite titanium": "#4A4A4C", "cream": "#EFE6D6",
    "yellow": "#E8C766", "bronze": "#A97142", "copper": "#B9663A",
}

CATEGORY_LABEL = {
    "smartphones": "smartphone",
    "tablettes": "tablette",
    "audio": "audio",
    "accessoires": "accessoire",
}


def clean(text: str) -> str:
    return " ".join((text or "").replace("\xa0", " ").split())


def fetch(url: str, tries: int = 3) -> bytes:
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=25) as response:
                return response.read()
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(0.6 + attempt * 0.8)
    raise last  # type: ignore[misc]


def brand_page_url(base: str, brand_id: int, page: int) -> str:
    if page == 1:
        return f"{BASE}{base}-phones-{brand_id}.php"
    return f"{BASE}{base}-phones-f-{brand_id}-0-p{page}.php"


def build_model_map() -> dict[str, dict[str, str]]:
    mapping: dict[str, dict[str, str]] = {}
    for brand, (base, brand_id, pages) in BRAND_PAGES.items():
        brand_map: dict[str, str] = {}
        for page in range(1, pages + 1):
            url = brand_page_url(base, brand_id, page)
            try:
                doc = html.fromstring(fetch(url))
            except Exception as exc:  # noqa: BLE001
                print(f"  ! page {brand} {page} indisponible : {exc}")
                continue
            for anchor in doc.xpath('//div[@class="makers"]//li//a'):
                name = clean(anchor.text_content())
                href = anchor.get("href")
                if name and href and name not in brand_map:
                    brand_map[name] = urljoin(BASE, href)
            time.sleep(0.1)
        mapping[brand] = brand_map
        print(f"  {brand}: {len(brand_map)} modèles indexés")
    return mapping


def price_for(name: str, brand: str, category: str) -> int:
    n = name.lower()
    if category == "tablettes":
        if "ipad" in n:
            if "pro 13" in n:
                return 1299
            if "pro 11" in n:
                return 1099
            if "air 13" in n:
                return 899
            if "air 11" in n:
                return 699
            if "mini (2026)" in n:
                return 599
            if "mini (2024)" in n:
                return 499
            if "2025" in n:
                return 349
            return 399
        if "tab s12 ultra" in n:
            return 1199
        if "tab s12+" in n:
            return 999
        if "tab s10 fe" in n:
            return 549
        if "tab s9 fe" in n:
            return 449
        if "tab a11" in n:
            return 249
        if "matepad pro 12" in n:
            return 899
        if "matepad 11.5" in n:
            return 349
        if "pad 9 pro" in n:
            return 599
        if "megapad 2" in n:
            return 249
        if "vistatab 12" in n:
            return 199
        if "xpad 30 pro" in n:
            return 349
        if "pad 6" in n:
            return 399
        if "pad 3" in n:
            return 349
        if "pad 20 pro" in n:
            return 499
        if "pixel tablet" in n:
            return 499
        return 399

    if brand == "Apple":
        if "duo" in n:
            return 1799
        if "ipad" in n:
            return 399
        gen_match = re.search(r"iphone (\d+)", n)
        gen = int(gen_match.group(1)) if gen_match else 0
        if "se" in n:
            return 429
        if "air" in n:
            return 1099
        if n.endswith("e") or " 17e" in n or " 16e" in n:
            return {17: 699, 16: 599}.get(gen, 599)
        if "pro max" in n:
            return {18: 1499, 17: 1399, 16: 1199, 15: 1099, 14: 899}.get(gen, 999)
        if "pro" in n:
            return {18: 1299, 17: 1199, 16: 999, 15: 999, 14: 799}.get(gen, 899)
        if "plus" in n:
            return {16: 899, 15: 799, 14: 649}.get(gen, 799)
        return {18: 999, 17: 899, 16: 799, 15: 699, 14: 599, 13: 499}.get(gen, 599)

    if brand == "Samsung":
        if "s26 ultra" in n: return 1299
        if "s26+" in n: return 999
        if "s26 fe" in n: return 699
        if "s26" in n: return 899
        if "s25 ultra" in n: return 1099
        if "s25+" in n: return 899
        if "s25 fe" in n: return 649
        if "s25 edge" in n: return 899
        if "s25" in n: return 799
        if "s24 ultra" in n: return 899
        if "s24+" in n: return 749
        if "s24 fe" in n: return 599
        if "s24" in n: return 649
        if "fold8 ultra" in n: return 1999
        if "fold8" in n: return 1799
        if "flip8" in n: return 1099
        if "fold7" in n: return 1699
        if "flip7" in n: return 999
        if "fold6" in n: return 1499
        if "flip6" in n: return 999
        if "fold5" in n: return 1299
        if "flip5" in n: return 899
        if "a57" in n: return 399
        if "a56" in n: return 349
        if "a55" in n: return 329
        if "a37" in n: return 299
        if "a36" in n: return 279
        if "a26" in n: return 229
        if "a17" in n: return 179
        if "a07" in n: return 129
        if "m47" in n: return 299
        if "m36" in n: return 249
        return 299

    if brand == "Huawei":
        if "pura 90 pro max" in n: return 1199
        if "pura 90 pro" in n: return 999
        if "pura 90 plus" in n: return 799
        if "pura 90" in n: return 899
        if "pura 80 ultra" in n: return 1099
        if "pura 80 pro" in n: return 899
        if "pura 70 ultra" in n: return 999
        if "pura 70 pro" in n: return 799
        if "pura 70" in n: return 699
        if "mate 90 pro max" in n: return 1299
        if "mate 90 pro" in n: return 1099
        if "mate 90" in n: return 999
        if "mate 80 pro" in n: return 1099
        if "mate 70 pro" in n: return 899
        if "mate 60 pro" in n: return 699
        if "xt 2" in n: return 2499
        if "x7" in n: return 1999
        if "x6" in n: return 1799
        if "x5" in n: return 1599
        if "nova 16 pro" in n: return 499
        if "nova 16" in n: return 399
        if "nova 13" in n: return 349
        return 499

    if brand == "Google":
        if "11 pro fold" in n: return 1799
        if "11 pro xl" in n: return 1199
        if "11 pro" in n: return 1099
        if "11" in n: return 899
        if "10 pro fold" in n: return 1699
        if "10 pro xl" in n: return 1099
        if "10 pro" in n: return 999
        if "10a" in n: return 499
        if "10" in n: return 799
        if "9 pro xl" in n: return 899
        if "9 pro fold" in n: return 1499
        if "9 pro" in n: return 799
        if "9a" in n: return 449
        if "9" in n: return 699
        if "8 pro" in n: return 699
        if "8a" in n: return 399
        if "8" in n: return 599
        if "fold" in n: return 1299
        return 499

    if brand == "Xiaomi":
        if "18 pro max" in n: return 1299
        if "18 pro" in n: return 1099
        if "18 fold" in n: return 1799
        if "17t pro" in n: return 699
        if "17t" in n: return 599
        if "17 max" in n: return 499
        if "note 17 pro max" in n: return 399
        if "note 17 pro" in n: return 349
        if "note 17" in n: return 279
        if "f9 ultra" in n: return 699
        if "f9 pro" in n: return 549
        if "x8" in n: return 349
        return 299

    if brand == "Tecno":
        if "camon 50 ultra" in n: return 599
        if "camon 50 pro" in n: return 449
        if "camon 50" in n: return 349
        if "camon 40 premier" in n: return 399
        if "camon 40 pro" in n: return 299
        if "camon 40" in n: return 249
        if "pova 8 pro" in n: return 299
        if "spark 50 pro" in n: return 199
        return 199

    if brand == "Itel":
        if "a300+" in n: return 179
        if "zeno 300" in n: return 199
        if "zeno 200" in n: return 149
        if "a100 pro" in n: return 109
        if "power 80" in n: return 139
        if "s25 ultra" in n: return 159
        if "a80" in n: return 99
        return 119

    if brand == "Infinix":
        if "note 60 ultra" in n: return 499
        if "note 60 pro" in n: return 399
        if "note 60" in n: return 299
        if "hot 70 pro" in n: return 249
        if "hot 60 pro+" in n: return 179
        if "zero 40" in n: return 299
        if "gt 50 pro" in n: return 399
        return 249

    if brand == "Oppo":
        if "find x10 pro max" in n: return 1299
        if "find x10" in n: return 999
        if "find n6" in n: return 1799
        if "reno16 pro" in n: return 599
        if "reno16" in n: return 499
        if "a7 pro" in n: return 249
        return 349

    if brand == "Realme":
        if "gt 8 pro" in n: return 799
        if "16 pro+" in n: return 599
        if "16 pro" in n: return 499
        if "16" in n: return 399
        if "narzo 90" in n: return 249
        return 299

    if brand == "OnePlus":
        if "16" in n: return 899
        if "15r" in n: return 599
        if "15" in n: return 799
        if "nord 6" in n: return 499
        return 399

    if brand == "Honor":
        if "magic9 pro max" in n: return 1199
        if "magic9" in n: return 999
        if "600 pro" in n: return 399
        if "x80 pro max" in n: return 499
        return 349

    return 299


def parse_number(text: str) -> str:
    text = clean(text)
    text = text.replace("GB", " Go").replace("RAM", "RAM")
    text = re.sub(r"(\d+)\s*Go", r"\1 Go", text)
    return text


def extract_specs(doc) -> dict[str, str]:
    data: dict[str, str] = {}
    for td in doc.xpath('//*[@id="specs-list"]//td[@data-spec]'):
        key = td.get("data-spec")
        if key and key not in data:
            data[key] = clean(td.text_content())
    return data


def shorten_screen(data: dict[str, str]) -> tuple[str, str]:
    size_raw = data.get("displaysize", "")
    type_raw = data.get("displaytype", "")
    match = re.search(r"([\d.]+)\s*inch", size_raw)
    size = match.group(1).replace(".", ",") + '"' if match else ""
    parts = [clean(p) for p in type_raw.split(",") if clean(p)]
    parts = [p for p in parts if "nits" not in p.lower() and "hdr" not in p.lower()]
    type_short = " · ".join(parts[:3])
    type_short = type_short.replace("120Hz", "120 Hz").replace("90Hz", "90 Hz").replace("144Hz", "144 Hz")
    type_short = re.sub(r"\s+", " ", type_short)
    if len(type_short) > 58:
        type_short = type_short[:55].rstrip(" ,·") + "…"
    screen = " · ".join(x for x in (size, type_short) if x)
    return screen, type_short


def storage_text(data: dict[str, str]) -> str:
    raw = data.get("internalmemory", "")
    first = clean(raw.split(",")[0])
    first = re.sub(r"(\d+)\s*GB", r"\1 Go", first)
    first = re.sub(r"(\d+)\s*TB", r"\1 To", first)
    first = re.sub(r"^(.*?(?:Go|To))\s+(\d+\s*Go\s*RAM)$", r"\1 · \2", first)
    first = first.replace("  ", " ")
    return first or "Stockage selon version"


def battery_text(data: dict[str, str]) -> str:
    raw = data.get("batdescription1") or data.get("batdescription") or ""
    match = re.search(r"([\d,]+)\s*mAh", raw)
    return (match.group(1).replace(",", " ") + " mAh") if match else clean(raw) or "—"


def camera_text(data: dict[str, str]) -> str:
    raw = data.get("cam1modules", "")
    mps = re.findall(r"(\d+)\s*MP", raw)
    if not mps:
        return "—"
    return " + ".join(mps[:3]) + " Mpx"


def color_list(data: dict[str, str]) -> list[dict[str, str]]:
    raw = data.get("colors", "")
    names = [clean(x) for x in raw.split(",") if clean(x)][:3]
    result = []
    for name in names:
        low = name.lower()
        hex_value = "#B8B0A3"
        for key, value in COLOR_HEX.items():
            if key in low:
                hex_value = value
                break
        result.append({"name": name, "hex": hex_value})
    if not result:
        result = [{"name": "Coloris standard", "hex": "#B8B0A3"}]
    return result


def series_for(name: str, brand: str, category: str) -> str:
    n = name.lower()
    if brand == "Apple":
        if n.startswith("ipad"):
            return "iPad"
        return "iPhone"
    if brand == "Samsung":
        if "tab" in n: return "Galaxy Tab"
        if "fold" in n or "flip" in n: return "Galaxy Z"
        if "galaxy s" in n: return "Galaxy S"
        if "galaxy a" in n: return "Galaxy A"
        if "galaxy m" in n: return "Galaxy M"
        return "Galaxy"
    if brand == "Huawei":
        if "matepad" in n: return "MatePad"
        if "pura" in n: return "Pura"
        if "mate x" in n or "mate xt" in n: return "Mate X"
        if "mate" in n: return "Mate"
        if "nova" in n: return "nova"
        return "Huawei"
    if brand == "Google":
        return "Pixel Tablet" if "tablet" in n else "Pixel"
    if brand == "Xiaomi":
        if "redmi" in n: return "Redmi"
        if "poco" in n: return "Poco"
        if "pad" in n: return "Xiaomi Pad"
        return "Xiaomi"
    if brand == "Tecno":
        if "camon" in n: return "Camon"
        if "pova" in n: return "Pova"
        if "spark" in n: return "Spark"
        if "megapad" in n: return "Megapad"
        return "Tecno"
    if brand == "Itel":
        if "vistatab" in n: return "VistaTab"
        if "zeno" in n: return "Zeno"
        if "power" in n: return "Power"
        return "Itel"
    if brand == "Infinix":
        if "note" in n: return "Note"
        if "hot" in n: return "Hot"
        if "zero" in n: return "Zero"
        if "gt" in n: return "GT"
        if "xpad" in n: return "Xpad"
        return "Infinix"
    if brand == "Oppo":
        if "find" in n: return "Find"
        if "reno" in n: return "Reno"
        if "pad" in n: return "Oppo Pad"
        return "Oppo"
    if brand == "Realme":
        if "gt" in n: return "GT"
        if "narzo" in n: return "Narzo"
        if "pad" in n: return "Realme Pad"
        return "Realme"
    if brand == "OnePlus":
        if "nord" in n: return "Nord"
        if "pad" in n: return "OnePlus Pad"
        return "OnePlus"
    if brand == "Honor":
        if "magic" in n: return "Magic"
        if "pad" in n: return "Honor Pad"
        return "Honor"
    return brand


def display_name_for(selection: str, brand: str) -> str:
    low = selection.lower()
    keep_prefixes = (
        "iphone", "ipad", "galaxy", "pura", "mate", "nova", "pixel",
        "redmi", "poco", "camon", "spark", "pova", "megapad", "note",
        "hot", "zero", "gt", "xpad", "vistatab", "zeno", "power",
        "find", "reno", "nord", "magic", "pad",
    )
    if low.startswith(keep_prefixes):
        return selection
    if brand in ("Xiaomi", "Itel", "Realme", "OnePlus", "Honor"):
        return f"{brand} {selection}"
    return selection


def category_for(name: str, brand: str) -> str:
    n = name.lower()
    if any(k in n for k in ("ipad", "tab", "matepad", "pad", "megapad", "vistatab", "xpad", "pixel tablet")):
        return "tablettes"
    return "smartphones"


def french_article(name: str, category: str) -> str:
    if category == "tablettes":
        return "L’" if name.lower().startswith(("ipad", "honor pad", "oppo pad")) else "La "
    return "L’" if name[:1].lower() in "aeiouéèêàâîïôû" else "Le "


def make_description(name: str, brand: str, category: str, specs: dict[str, str], screen: str, storage: str, chipset: str, battery: str, camera: str) -> str:
    kind = CATEGORY_LABEL.get(category, "produit")
    article = french_article(name, category)
    if category == "tablettes":
        return (
            f"{article}{name} associe un écran {screen or 'généreux'} à la puce {chipset or 'dernière génération'}, "
            f"avec {storage} de stockage. Une tablette {brand} pensée pour lire, créer et travailler sans compromis."
        )
    return (
        f"{article}{name} réunit un écran {screen or 'immersif'}, la puce {chipset or 'haute performance'} "
        f"et {storage}. Un {kind} {brand} taillé pour le quotidien, la photo et les journées chargées, "
        f"avec une batterie de {battery or 'grande capacité'}."
    )


def make_features(name: str, screen: str, chipset: str, storage: str, battery: str, camera: str, colors: list[dict[str, str]]) -> list[str]:
    features = []
    if screen:
        features.append(f"Écran {screen}")
    if chipset:
        features.append(f"Puce {chipset}")
    if storage:
        features.append(f"Mémoire {storage}")
    if battery:
        features.append(f"Batterie {battery}")
    if camera and camera != "—":
        features.append(f"Photo {camera}")
    features.append("Produit neuf scellé, garantie 12 mois")
    return features[:5]


def specs_rows(name: str, screen: str, chipset: str, storage: str, battery: str, camera: str, os_name: str, colors: list[dict[str, str]]) -> list[list[str]]:
    rows = []
    if screen: rows.append(["Écran", screen])
    if chipset: rows.append(["Puce", chipset])
    if storage: rows.append(["Mémoire", storage])
    if battery: rows.append(["Batterie", battery])
    if camera and camera != "—": rows.append(["Photo", camera])
    if os_name: rows.append(["Système", os_name])
    if colors:
        rows.append(["Coloris", ", ".join(c["name"] for c in colors)])
    return rows[:6]


def slug_for(href: str, brand: str) -> str:
    slug = href.split("/")[-1].replace(".php", "")
    slug = re.sub(r"-\d+$", "", slug)
    for prefix in ("apple_", "samsung_", "huawei_", "google_", "xiaomi_", "tecno_", "itel_", "infinix_", "oppo_", "realme_", "oneplus_", "honor_"):
        if slug.startswith(prefix):
            slug = slug[len(prefix):]
            break
    slug = slug.replace("_", "-").replace("(", "").replace(")", "")
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def placeholder_svg(product_id: str, name: str, category: str, brand: str) -> str:
    c1, c2 = TINT.get(brand, ("#F1E9DC", "#E2D3BE"))
    safe_name = html_mod.escape(name)
    shape = {
        "tablettes": '<rect x="285" y="150" width="230" height="480" rx="26" fill="#0E2A22" opacity="0.9"/><rect x="300" y="170" width="200" height="440" rx="16" fill="#F5F0E6" opacity="0.9"/>',
        "audio": '<rect x="320" y="330" width="160" height="150" rx="40" fill="#0E2A22"/><circle cx="360" cy="300" r="34" fill="#0E2A22"/><circle cx="440" cy="300" r="34" fill="#0E2A22"/>',
        "accessoires": '<rect x="300" y="250" width="200" height="260" rx="34" fill="#0E2A22"/><rect x="330" y="300" width="140" height="12" rx="6" fill="#D9AE5F"/>',
    }.get(category, '<rect x="270" y="130" width="260" height="520" rx="48" fill="#0E2A22"/><rect x="285" y="150" width="230" height="480" rx="34" fill="#F5F0E6" opacity="0.92"/><rect x="350" y="165" width="90" height="24" rx="12" fill="#0E2A22"/>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" width="800" height="800" role="img">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs>
<circle cx="400" cy="390" r="270" fill="#FFFFFF" opacity="0.35"/>
{shape}
<text x="400" y="720" text-anchor="middle" font-family="Georgia, serif" font-size="30" fill="#0E2A22" opacity="0.75">{safe_name}</text>
<text x="400" y="752" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" letter-spacing="3" fill="#0E2A22" opacity="0.45">VISUEL À VENIR</text>
</svg>"""


def download_image(image_url: str, product_id: str, name: str, category: str, brand: str, credits: list[str]) -> str:
    try:
        raw = fetch(image_url, tries=2)
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        img = ImageOps.contain(img, (860, 860), Image.LANCZOS)
        canvas = Image.new("RGB", (900, 900), "white")
        canvas.paste(img, ((900 - img.width) // 2, (900 - img.height) // 2))
        target = PHOTO_DIR / f"{product_id}.webp"
        canvas.save(target, "WEBP", quality=88, method=6)
        credits.append(f"- `{product_id}.webp` — [{name}]({image_url}) — GSMArena")
        return f"assets/img/products/photos/{product_id}.webp"
    except Exception as exc:  # noqa: BLE001
        print(f"    ! image manquante pour {name}: {exc}")
        svg_path = IMG_DIR / f"{product_id}.svg"
        svg_path.write_text(placeholder_svg(product_id, name, category, brand), encoding="utf-8")
        credits.append(f"- `{product_id}.svg` — placeholder MF Business (visuel réel indisponible)")
        return f"assets/img/products/{product_id}.svg"


def build_product(brand: str, selection_name: str, spec_url: str, credits: list[str]) -> dict | None:
    try:
        doc = html.fromstring(fetch(spec_url))
    except Exception as exc:  # noqa: BLE001
        print(f"    ! fiche indisponible {selection_name}: {exc}")
        return None
    data = extract_specs(doc)
    if not data:
        print(f"    ! specs vides {selection_name}")
        return None

    name = display_name_for(selection_name, brand)
    category = category_for(selection_name, brand)
    screen, _ = shorten_screen(data)
    storage = storage_text(data)
    chipset = clean(data.get("chipset", "")) or "—"
    battery = battery_text(data)
    camera = camera_text(data)
    os_name = clean(data.get("os", "")).split(",")[0]
    colors = color_list(data)
    series = series_for(selection_name, brand, category)
    price = price_for(selection_name, brand, category)
    product_id = slug_for(spec_url, brand)

    image_url = ""
    candidates = doc.xpath('//div[contains(@class,"specs-photo-main")]//img/@src') + doc.xpath('//meta[@property="og:image"]/@content')
    if candidates:
        image_url = candidates[0]
    image_path = download_image(image_url, product_id, name, category, brand, credits) if image_url else ""
    if not image_path:
        svg_path = IMG_DIR / f"{product_id}.svg"
        svg_path.write_text(placeholder_svg(product_id, name, category, brand), encoding="utf-8")
        image_path = f"assets/img/products/{product_id}.svg"
        credits.append(f"- `{product_id}.svg` — placeholder MF Business (visuel réel indisponible)")

    digest = int(hashlib.sha1(product_id.encode("utf-8")).hexdigest()[:8], 16)
    rating = 4.5 + (digest % 5) / 10
    reviews = 24 + digest % 260
    stock = 3 + digest % 18
    featured = selection_name in FEATURED
    badge = ""
    badge_tone = ""
    if featured:
        badge, badge_tone = "Coup de cœur", "best"
    elif re.search(r"(18|17|S26|Pixel 11|Pura 90|Mate 90)", selection_name):
        badge, badge_tone = "Nouveau", "new"
    elif price <= 150:
        badge, badge_tone = "Petit prix", "budget"

    description = make_description(name, brand, category, data, screen, storage, chipset, battery, camera)
    features = make_features(name, screen, chipset, storage, battery, camera, colors)
    specs = specs_rows(name, screen, chipset, storage, battery, camera, os_name, colors)
    capacity_match = re.match(r"(\d+\s?(?:Go|To))", storage)
    capacity = capacity_match.group(1) if capacity_match else storage
    subtitle = capacity
    if colors:
        subtitle = (capacity + " · " + colors[0]["name"]) if capacity else colors[0]["name"]

    keywords = " ".join([
        selection_name, name, brand, series, storage, os_name,
        " ".join(c["name"] for c in colors),
        str(price),
    ])

    return {
        "id": product_id,
        "name": name,
        "subtitle": subtitle,
        "brand": brand,
        "category": category,
        "series": series,
        "price": price,
        "badge": badge,
        "badgeTone": badge_tone,
        "rating": round(rating, 1),
        "reviews": reviews,
        "stock": stock,
        "featured": featured,
        "tint": list(TINT.get(brand, ("#F1E9DC", "#E2D3BE"))),
        "colors": colors,
        "description": description,
        "features": features,
        "specs": specs,
        "keywords": keywords,
        "image": image_path,
    }


ACCESSORIES = [
    {
        "id": "airpods-pro-2", "name": "AirPods Pro (2ᵉ gén.)", "brand": "Apple", "category": "audio",
        "series": "AirPods", "price": 249, "subtitle": "Boîtier USB-C · Blanc",
        "description": "La réduction de bruit active la plus naturelle de sa catégorie, un son spatial qui enveloppe et un boîtier USB-C. Le compagnon audio idéal de votre iPhone.",
        "features": ["Réduction de bruit active adaptative", "Audio spatial personnalisé", "6 h d’écoute · 30 h avec le boîtier", "Résistance IP54 · USB-C"],
        "specs": [["Type", "Intra-auriculaire sans fil"], ["Puce", "Apple H2"], ["Autonomie", "6 h · 30 h avec boîtier"], ["Boîtier", "USB-C · MagSafe"], ["Étanchéité", "IP54"], ["Audio", "Spatial personnalisé"]],
        "colors": [{"name": "Blanc", "hex": "#F4F4F2"}], "image": "assets/img/products/airpods-pro-2.svg",
        "rating": 4.9, "reviews": 156, "stock": 16, "featured": False, "badge": "Best-seller", "badgeTone": "best",
        "tint": ["#F5F3EE", "#E9E4DA"], "keywords": "airpods apple ecouteurs audio anc bluetooth",
    },
    {
        "id": "galaxy-buds3-pro", "name": "Galaxy Buds3 Pro", "brand": "Samsung", "category": "audio",
        "series": "Galaxy Buds", "price": 249, "subtitle": "ANC · Argent",
        "description": "Le son Samsung le plus précis, avec réduction de bruit adaptative et suivi de tête. Une paire d’écouteurs taillée pour les appels et les longues sessions.",
        "features": ["ANC adaptative", "Audio 24 bits", "6 h · 30 h avec boîtier", "IP57"],
        "specs": [["Type", "Intra-auriculaire"], ["Autonomie", "6 h · 30 h"], ["Bluetooth", "5.4"], ["Étanchéité", "IP57"], ["ANC", "Oui"], ["Coloris", "Argent"]],
        "colors": [{"name": "Argent", "hex": "#C9C9C9"}], "image": "assets/img/products/galaxy-buds3-pro.svg",
        "rating": 4.8, "reviews": 94, "stock": 14, "featured": False, "badge": "", "badgeTone": "",
        "tint": ["#EFF0F3", "#DFE2E8"], "keywords": "galaxy buds samsung ecouteurs audio anc",
    },
    {
        "id": "galaxy-buds-fe", "name": "Galaxy Buds FE", "brand": "Samsung", "category": "audio",
        "series": "Galaxy Buds", "price": 99, "subtitle": "ANC · Anthracite",
        "description": "L’essentiel du sans-fil Samsung : réduction de bruit, son clair et une autonomie confortable, à un prix qui laisse de la place pour les accessoires.",
        "features": ["Réduction de bruit active", "6 h · 21 h avec le boîtier", "Bluetooth 5.2", "Trois tailles d’embouts incluses"],
        "specs": [["Type", "Intra-auriculaire sans fil"], ["Autonomie", "6 h · 21 h"], ["Bluetooth", "5.2"], ["Étanchéité", "IPX2"], ["ANC", "Oui"], ["Coloris", "2"]],
        "colors": [{"name": "Anthracite", "hex": "#3A3D42"}, {"name": "Blanc", "hex": "#F1F0EC"}], "image": "assets/img/products/galaxy-buds-fe.svg",
        "rating": 4.6, "reviews": 88, "stock": 21, "featured": False, "badge": "", "badgeTone": "",
        "tint": ["#EFF0F3", "#DFE2E8"], "keywords": "galaxy buds fe samsung ecouteurs audio anc",
    },
    {
        "id": "jbl-tune-buds", "name": "JBL Tune Buds", "brand": "JBL", "category": "audio",
        "series": "Tune", "price": 79, "subtitle": "ANC · Bleu",
        "description": "Le son JBL généreux, une réduction de bruit efficace et 40 heures d’autonomie avec le boîtier. Des écouteurs robustes pour la route et la salle de sport.",
        "features": ["Son JBL Pure Bass", "Réduction de bruit active", "10 h · 40 h avec boîtier", "IP54"],
        "specs": [["Type", "Intra-auriculaire"], ["Autonomie", "10 h · 40 h"], ["Bluetooth", "5.3"], ["Étanchéité", "IP54"], ["ANC", "Oui"], ["Application", "JBL Headphones"]],
        "colors": [{"name": "Bleu", "hex": "#2F5DA8"}, {"name": "Noir", "hex": "#1F2124"}], "image": "assets/img/products/jbl-tune-buds.svg",
        "rating": 4.5, "reviews": 64, "stock": 19, "featured": False, "badge": "", "badgeTone": "",
        "tint": ["#EBF1FB", "#D8E3F6"], "keywords": "jbl tune buds ecouteurs audio anc",
    },
    {
        "id": "jbl-go-4", "name": "JBL Go 4", "brand": "JBL", "category": "audio",
        "series": "Go", "price": 49, "subtitle": "Enceinte portable · Orange",
        "description": "Une enceinte de poche qui envoie du son, tient sept heures et survit à la poussière comme aux éclaboussures. À emporter partout.",
        "features": ["Son JBL Pro", "7 h d’autonomie", "Étanchéité IP67", "Bluetooth 5.3"],
        "specs": [["Type", "Enceinte Bluetooth"], ["Autonomie", "7 h"], ["Étanchéité", "IP67"], ["Bluetooth", "5.3"], ["Recharge", "USB-C"], ["Poids", "190 g"]],
        "colors": [{"name": "Orange", "hex": "#E45B2B"}, {"name": "Noir", "hex": "#202124"}], "image": "assets/img/products/jbl-go-4.svg",
        "rating": 4.7, "reviews": 52, "stock": 23, "featured": False, "badge": "", "badgeTone": "",
        "tint": ["#FCEEE8", "#F6DACE"], "keywords": "jbl go 4 enceinte bluetooth audio",
    },
    {
        "id": "pochette-cuir", "name": "Pochette en cuir", "brand": "MF Atelier", "category": "accessoires",
        "series": "MF Atelier", "price": 29, "subtitle": "Cuir pleine fleur · Cognac",
        "description": "Une pochette en cuir pleine fleur, doublée de microfibre, qui protège votre téléphone avec élégance. Elle se patine avec le temps.",
        "features": ["Cuir pleine fleur", "Doublure microfibre", "Poche pour carte", "Fermeture aimantée"],
        "specs": [["Matière", "Cuir pleine fleur"], ["Doublure", "Microfibre"], ["Format", "Jusqu’à 6,9\""], ["Fermeture", "Aimantée"], ["Série", "MF Atelier"]],
        "colors": [{"name": "Cognac", "hex": "#A8642F"}, {"name": "Noir", "hex": "#22201E"}], "image": "assets/img/products/pochette-cuir.svg",
        "rating": 4.6, "reviews": 41, "stock": 12, "featured": False, "badge": "", "badgeTone": "",
        "tint": ["#F4E9DD", "#E8D3BF"], "keywords": "pochette cuir accessoire protection",
    },
    {
        "id": "chargeur-65w", "name": "Chargeur GaN 65 W", "brand": "Anker", "category": "accessoires",
        "series": "Anker", "price": 39, "subtitle": "3 ports · Blanc",
        "description": "Un seul chargeur pour le téléphone, la tablette et l’ordinateur portable. La technologie GaN le garde compact et froid.",
        "features": ["65 W · technologie GaN", "2 ports USB-C + 1 USB-A", "Charge un laptop", "Protection surchauffe"],
        "specs": [["Puissance", "65 W"], ["Ports", "2 × USB-C · 1 × USB-A"], ["Technologie", "GaN"], ["Compatibilité", "iPhone, Android, laptop"], ["Câble", "Non inclus"]],
        "colors": [{"name": "Blanc", "hex": "#F2F0EA"}, {"name": "Noir", "hex": "#26282B"}], "image": "assets/img/products/chargeur-65w.svg",
        "rating": 4.8, "reviews": 132, "stock": 27, "featured": False, "badge": "", "badgeTone": "",
        "tint": ["#F3F1EB", "#E6E2D7"], "keywords": "chargeur anker gan 65w usb-c accessoire",
    },
    {
        "id": "powerbank-20000", "name": "Power bank 20 000 mAh", "brand": "Anker", "category": "accessoires",
        "series": "Anker", "price": 45, "subtitle": "30 W · Noir",
        "description": "De quoi recharger un téléphone quatre à cinq fois, ou la tablette en voyage. La charge 30 W remplit vite.",
        "features": ["20 000 mAh, charge 30 W", "Affichage LED", "Deux USB-A et un USB-C", "Compatible cabine"],
        "specs": [["Capacité", "20 000 mAh"], ["Puissance", "30 W"], ["Ports", "USB-C · 2 × USB-A"], ["Affichage", "LED"], ["Recharge", "≈ 3 h"]],
        "colors": [{"name": "Noir", "hex": "#242629"}, {"name": "Blanc", "hex": "#EFEDE7"}], "image": "assets/img/products/powerbank-20000.svg",
        "rating": 4.7, "reviews": 97, "stock": 15, "featured": False, "badge": "", "badgeTone": "",
        "tint": ["#EEF0F3", "#DEE2E7"], "keywords": "power bank anker batterie accessoire",
    },
    {
        "id": "coque-magsafe", "name": "Coque MagSafe", "brand": "MF Atelier", "category": "accessoires",
        "series": "MF Atelier", "price": 19, "subtitle": "Transparente · Antichoc",
        "description": "Une coque transparente qui laisse voir votre iPhone tout en le protégeant des chutes. Les aimants MagSafe restent puissants.",
        "features": ["Anneau MagSafe", "Protection 2 m", "Boutons métal", "Compatible iPhone 15/14/13"],
        "specs": [["Matière", "Polycarbonate + TPU"], ["MagSafe", "Compatible"], ["Protection", "2 m"], ["Compatibilité", "iPhone 15/14/13"], ["Série", "MF Atelier"]],
        "colors": [{"name": "Transparent", "hex": "#E9E6DE"}], "image": "assets/img/products/coque-magsafe.svg",
        "rating": 4.5, "reviews": 73, "stock": 31, "featured": False, "badge": "", "badgeTone": "",
        "tint": ["#F2F4F5", "#E2E7E9"], "keywords": "coque magsafe protection accessoire",
    },
    {
        "id": "cable-usbc", "name": "Câble USB-C 100 W", "brand": "MF Atelier", "category": "accessoires",
        "series": "MF Atelier", "price": 12, "subtitle": "2 m · Nylon tressé",
        "description": "Un câble costaud, souple et rapide : 100 W pour charger un ordinateur, 480 Mb/s pour transférer vos fichiers.",
        "features": ["Charge 100 W", "Nylon tressé", "Transfert 480 Mb/s", "Longueur 2 m"],
        "specs": [["Connecteurs", "USB-C vers USB-C"], ["Puissance", "100 W"], ["Longueur", "2 m"], ["Gaine", "Nylon tressé"], ["Garantie", "24 mois"]],
        "colors": [{"name": "Gris tressé", "hex": "#8C8C8C"}], "image": "assets/img/products/cable-usbc.svg",
        "rating": 4.6, "reviews": 188, "stock": 48, "featured": False, "badge": "", "badgeTone": "",
        "tint": ["#F1F1F0", "#E2E2E0"], "keywords": "cable usb-c charge accessoire",
    },
    {
        "id": "montre-connectee", "name": "Galaxy Fit 3", "brand": "Samsung", "category": "accessoires",
        "series": "Galaxy Fit", "price": 79, "subtitle": "Bracelet connecté · Noir",
        "description": "Le suivi du sommeil, du cœur et de plus de 100 sports, dans un bracelet léger qui tient presque deux semaines.",
        "features": ["Écran AMOLED 1,6\"", "Jusqu’à 13 jours", "IP68 et 5 ATM", "100+ modes sport"],
        "specs": [["Écran", "AMOLED 1,6\""], ["Autonomie", "13 jours"], ["Étanchéité", "IP68 · 5 ATM"], ["Capteurs", "Cardio, sommeil, stress"], ["Compatibilité", "Android"]],
        "colors": [{"name": "Noir", "hex": "#222426"}, {"name": "Argent", "hex": "#D5D5D5"}], "image": "assets/img/products/montre-connectee.svg",
        "rating": 4.4, "reviews": 58, "stock": 13, "featured": False, "badge": "", "badgeTone": "",
        "tint": ["#F0F1F2", "#DFE1E3"], "keywords": "galaxy fit samsung montre bracelet accessoire",
    },
]


def build_accessories() -> list[dict]:
    products = []
    for item in ACCESSORIES:
        item = dict(item)
        item.setdefault("oldPrice", None)
        products.append(item)
    return products


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map-only", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    print("Indexation des pages marques…")
    model_map = build_model_map()
    missing = []
    total = 0
    for brand, names in SELECTION.items():
        for name in names:
            total += 1
            if name not in model_map.get(brand, {}):
                missing.append(f"{brand} / {name}")
    print(f"\nSélection : {total} modèles, {len(missing)} introuvables")
    for miss in missing:
        print("  ?", miss)
    (DATA_DIR / "catalog_missing.json").write_text(json.dumps(missing, ensure_ascii=False, indent=1), encoding="utf-8")

    if args.map_only:
        return

    credits: list[str] = []
    products: list[dict] = []
    count = 0
    for brand, names in SELECTION.items():
        print(f"\n### {brand}")
        for name in names:
            if args.limit and count >= args.limit:
                break
            spec_url = model_map.get(brand, {}).get(name)
            if not spec_url:
                continue
            count += 1
            print(f"  [{count}] {name}")
            product = build_product(brand, name, spec_url, credits)
            if product:
                products.append(product)
            time.sleep(0.12)
        if args.limit and count >= args.limit:
            break

    products.extend(build_accessories())
    # dédoublonnage par id
    seen = set()
    unique = []
    for product in products:
        if product["id"] in seen:
            continue
        seen.add(product["id"])
        unique.append(product)

    (DATA_DIR / "catalog.json").write_text(json.dumps(unique, ensure_ascii=False, indent=1), encoding="utf-8")
    js = "/* Catalogue MF Business — généré par tools/catalog_build.py */\nMF.PRODUCTS = " + json.dumps(unique, ensure_ascii=False, indent=1) + ";\n"
    (ROOT / "js" / "catalog.js").write_text(js, encoding="utf-8")

    credits_text = "# Crédits visuels\n\nLes visuels téléchargés proviennent des fiches GSMArena et servent de visuels de démonstration. Pour une publication commerciale, remplacez-les par vos propres photos ou par des images sous licence.\n\n" + "\n".join(credits) + "\n"
    (ROOT / "CREDITS.md").write_text(credits_text, encoding="utf-8")

    print(f"\n{len(unique)} produits générés dans js/catalog.js")
    by_brand = {}
    for p in unique:
        by_brand[p["brand"]] = by_brand.get(p["brand"], 0) + 1
    print(by_brand)
    print("Images :", len(list(PHOTO_DIR.glob("*.webp"))), "webp")


if __name__ == "__main__":
    main()
