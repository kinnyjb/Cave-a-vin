#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Construit l'appli Cave à partir de app-src/cave.src.html.

    py tools/build_appli.py

Sortie : app/index.html (+ version du cache hors ligne dans sw.js).
"""
import json
import os
import re
import shutil
import sys

if hasattr(sys.stdout, "reconfigure"):      # Windows : console en cp1252
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def bump_cache(chemin, prefixe):
    """Monte le numéro de cache d'un service worker, sinon le téléphone garde
    l'ancienne page en mémoire et ne voit jamais la mise à jour."""
    sw = open(chemin, encoding="utf-8").read()
    v = int(re.search(prefixe + r"-v(\d+)", sw).group(1))
    open(chemin, "w", encoding="utf-8").write(
        sw.replace("%s-v%d" % (prefixe, v), "%s-v%d" % (prefixe, v + 1)))
    return v + 1


def construire_cave():
    src = os.path.join(ROOT, "app-src", "cave.src.html")
    dst = os.path.join(ROOT, "app")
    os.makedirs(dst, exist_ok=True)

    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from accord import charger_bouteilles
    bouteilles = charger_bouteilles()                                    # la cave de la maison
    accords = open(os.path.join(ROOT, "tools", "accords.json"), encoding="utf-8").read()

    page = open(src, encoding="utf-8").read()
    page = (page.replace("/*__BOUTEILLES__*/[]", json.dumps(bouteilles, ensure_ascii=False))
                .replace("/*__ACCORDS__*/{plats:{},cepages:{}}", accords))
    open(os.path.join(dst, "index.html"), "w", encoding="utf-8").write(page)

    # les photos des bouteilles, servies à côté de la page (jamais intégrées
    # dedans : une photo en base64 alourdirait la page entière à chaque ouverture)
    photos_src = os.path.join(ROOT, "bouteilles", "photos")
    photos_dst = os.path.join(dst, "photos")
    n_photos = 0
    if os.path.isdir(photos_src):
        os.makedirs(photos_dst, exist_ok=True)
        for f in os.listdir(photos_src):
            if f.startswith("."):
                continue
            a, b = os.path.join(photos_src, f), os.path.join(photos_dst, f)
            if not os.path.exists(b) or os.path.getmtime(a) > os.path.getmtime(b):
                shutil.copy2(a, b)
            n_photos += 1

    v = bump_cache(os.path.join(dst, "sw.js"), "cave")
    print("🍷 appli Cave construite · %d bouteilles · %d photos · cache v%d"
          % (len(bouteilles), n_photos, v))


if __name__ == "__main__":
    construire_cave()
