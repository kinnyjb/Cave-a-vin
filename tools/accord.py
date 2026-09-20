#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Le moteur d'accords mets-vin.

Une seule règle : suggérer à partir de ce qu'il y a VRAIMENT en cave, jamais
inventer une bouteille idéale qu'on n'a pas. La table tools/accords.json donne,
pour une soixantaine de plats et une trentaine de cépages, la couleur et le
corps attendus — ce sont des repères d'œnologie classiques, pas un jugement sur
tel ou tel vin de la maison.

    py tools/accord.py "gigot d'agneau"
    py tools/accord.py "plateau de fromages" --top 3

⚠️ Ce sont des repères, pas une règle absolue : la meilleure bouteille reste
celle qu'on a envie d'ouvrir ce soir-là.
"""
import argparse
import json
import os
import sys
import unicodedata
from datetime import date

if hasattr(sys.stdout, "reconfigure"):      # Windows : console en cp1252
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(ROOT, "tools", "accords.json")


def _sans_accent(s):
    s = unicodedata.normalize("NFD", str(s).lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").strip()


def charger_table():
    d = json.load(open(TABLE, encoding="utf-8"))
    plats = {_sans_accent(k): v for k, v in d["plats"].items()}
    cepages = {_sans_accent(k): v for k, v in d["cepages"].items()}
    return plats, cepages


def chercher_plat(texte, plats):
    """Trouve le plat le plus proche dans la table. None si rien de crédible.

    Même algorithme que le moteur nutrition : exact, puis inclusion (en
    préférant ce qui vient en tête du texte), puis mots en commun. Ça permet à
    « un gros gigot d'agneau de 7 heures » de retomber sur « gigot d'agneau ».
    """
    n = _sans_accent(texte)
    if not n:
        return None, None
    if n in plats:
        return n, plats[n]

    candidats = [(cle, p) for cle, p in plats.items() if cle in n or n in cle]
    if candidats:
        def rang(x):
            cle = x[0]
            pos = n.find(cle)
            return (pos if pos >= 0 else len(n), -len(cle))
        cle, p = min(candidats, key=rang)
        return cle, p

    mots = {m for m in n.replace("'", " ").split() if len(m) > 3}
    meilleur, meilleure_cle, score = None, None, 0
    for cle, p in plats.items():
        commun = len(mots & {m for m in cle.replace("'", " ").split() if len(m) > 3})
        if commun > score:
            meilleur, meilleure_cle, score = p, cle, commun
    return meilleure_cle, meilleur


def charger_bouteilles(dossier=None):
    """Toutes les bouteilles de la cave, telles qu'écrites sur le disque."""
    d = dossier or os.path.join(ROOT, "bouteilles")
    if not os.path.isdir(d):
        return []
    out = []
    for f in sorted(os.listdir(d)):
        if not f.endswith(".json"):
            continue
        try:
            b = json.load(open(os.path.join(d, f), encoding="utf-8"))
        except (ValueError, OSError):
            print("⚠️  bouteille illisible, ignorée : %s" % f)
            continue
        b.setdefault("id", f[:-5])
        out.append(b)
    return out


def suggerer(plat_texte, bouteilles, plats=None, top=5):
    """Classe les bouteilles de la cave pour un plat donné.

    Renvoie (plat_trouve, cible, classement) où classement est une liste de
    (bouteille, score) triée du meilleur accord au moins bon. Score bas = bon.
    Ne filtre jamais les bouteilles à 0 : mieux vaut le dire à l'écran que
    cacher une référence qu'on garde en mémoire (historique de service).
    """
    if plats is None:
        plats, _ = charger_table()
    _, cible = chercher_plat(plat_texte, plats)
    if not cible:
        return None, None, []

    couleurs = cible["couleur"]
    puissance_cible = cible["puissance"]

    def score(b):
        couleur = b.get("couleur")
        if couleur in couleurs:
            base = couleurs.index(couleur) * 0.5       # 0 = couleur idéale, 0.5 = alternative
        else:
            base = 3                                     # couleur hors accord : pénalité forte
        base += abs(int(b.get("puissance") or 3) - puissance_cible) * 0.4
        if not b.get("quantite"):
            base += 10                                   # en dernier : on n'en a plus
        return base

    classement = sorted(bouteilles, key=score)
    return cible, puissance_cible, [(b, score(b)) for b in classement[:top]]


def main():
    ap = argparse.ArgumentParser(description="Accord mets-vin depuis la cave de la maison")
    ap.add_argument("plat", help="ce qu'on mange, en texte libre")
    ap.add_argument("--top", type=int, default=5)
    a = ap.parse_args()

    plats, _ = charger_table()
    bouteilles = charger_bouteilles()
    if not bouteilles:
        sys.exit("🍷 La cave est vide pour l'instant — rien à suggérer.")

    cle, puissance, classement = suggerer(a.plat, bouteilles, plats, a.top)
    if not cle:
        sys.exit("🤷 Plat non reconnu : « %s ». Essaie une description plus simple "
                  "(« bœuf », « fromage de chèvre », « dessert au chocolat »…)." % a.plat)

    print("\n🍽  %s → on cherche du %s, corps %d/5\n" % (a.plat, cle, puissance))
    for b, s in classement:
        reste = "%d en cave" % b.get("quantite", 0) if b.get("quantite") else "plus en cave"
        millesime = " %s" % b["millesime"] if b.get("millesime") else ""
        print("   %-32s %s%s · %s" % (b.get("nom", "?"), b.get("couleur", "?"), millesime, reste))
    print("\n   (repères d'accord classiques — la meilleure bouteille reste celle dont on a envie)")


if __name__ == "__main__":
    main()
