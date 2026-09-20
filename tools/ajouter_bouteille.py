#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enregistre une bouteille envoyée depuis l'appli (iPhone ou navigateur).

    py tools/ajouter_bouteille.py '{"nom":"Château Truc","couleur":"rouge","quantite":3}'
    py tools/ajouter_bouteille.py --fichier /tmp/bouteille.json
    py tools/ajouter_bouteille.py --modifier 2026-09-20-chateau-truc --fichier /tmp/bouteille.json
    py tools/ajouter_bouteille.py --supprimer 2026-09-20-chateau-truc
    py tools/ajouter_bouteille.py --ouvrir 2026-09-20-chateau-truc [--n 1]

Depuis l'appli, l'opération voyage DANS le JSON — la passerelle /api/robot
transmet la bouteille telle quelle, il n'y a donc rien à changer côté GitHub :

    {"_op": "modifier",  "id": "2026-09-20-chateau-truc", "nom": "...", ...}
    {"_op": "supprimer", "id": "2026-09-20-chateau-truc", "par": "Camille"}
    {"_op": "ouvrir",    "id": "2026-09-20-chateau-truc", "n": 1}

Écrit UN FICHIER PAR BOUTEILLE (un « lot » : une même référence, un même
millésime) dans bouteilles/ :

    bouteilles/2026-09-20-chateau-truc.json

Un fichier par lot, et pas un gros fichier commun : c'est ce qui permet à
deux personnes d'ajouter une bouteille chacune de son côté, la même minute,
sans que l'une écrase l'autre.

🔴 La cave ne contient QUE les bouteilles réellement en cave. Ce n'est ni un
   carnet de dégustation de bouteilles déjà bues il y a longtemps, ni une liste
   d'envies — juste ce qu'il y a, physiquement, dans la maison.
"""
import argparse
import json
import os
import re
import sys
import unicodedata
from datetime import date

if hasattr(sys.stdout, "reconfigure"):      # Windows : console en cp1252
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER = os.path.join(ROOT, "bouteilles")

COULEURS = ["rouge", "blanc", "rose", "effervescent", "doux"]
# corps par défaut quand la couleur seule doit trancher (pas de cépage connu)
PUISSANCE_DEFAUT = {"rouge": 3, "blanc": 2, "rose": 1, "effervescent": 1, "doux": 2}


def slug(texte):
    t = unicodedata.normalize("NFD", str(texte).lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t[:60] or "bouteille"


def liste_propre(valeur, maxi=6):
    """Normalise un champ liste venu du formulaire (str ou list) : les cépages."""
    if isinstance(valeur, str):
        valeur = re.split(r"[,;]", valeur)
    out = []
    for v in (valeur or []):
        v = slug(v)
        if not v or v in out:
            continue
        out.append(v)
    return out[:maxi]


def _sans_accent(s):
    s = unicodedata.normalize("NFD", str(s).lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").strip()


def deduire_couleur(cepages):
    """Devine la couleur à partir des cépages connus de tools/accords.json."""
    try:
        table = json.load(open(os.path.join(ROOT, "tools", "accords.json"), encoding="utf-8"))
        connus = table.get("cepages") or {}
    except (OSError, ValueError):
        return None
    for c in cepages:
        if c in connus:
            return connus[c].get("couleur")
    return None


def deduire_puissance(couleur, cepages):
    try:
        table = json.load(open(os.path.join(ROOT, "tools", "accords.json"), encoding="utf-8"))
        connus = table.get("cepages") or {}
    except (OSError, ValueError):
        connus = {}
    for c in cepages:
        if c in connus and connus[c].get("puissance"):
            return connus[c]["puissance"]
    return PUISSANCE_DEFAUT.get(couleur, 3)


def nettoyer(brut):
    """Valide et normalise la bouteille reçue. Sort en erreur si inexploitable."""
    nom = str(brut.get("nom") or "").strip()[:120]
    if not nom:
        sys.exit("❌ Bouteille sans nom — rien d'enregistré.")

    cepages = liste_propre(brut.get("cepages"))

    couleur = slug(brut.get("couleur") or "")
    if couleur not in COULEURS:
        couleur = deduire_couleur(cepages) or "rouge"

    millesime = None
    try:
        if str(brut.get("millesime") or "").strip():
            millesime = int(float(brut.get("millesime")))
            if not (1900 <= millesime <= date.today().year):
                millesime = None
    except (TypeError, ValueError):
        millesime = None

    try:
        quantite = int(float(brut.get("quantite"))) if str(brut.get("quantite") or "").strip() else 1
    except (TypeError, ValueError):
        quantite = 1
    quantite = max(0, min(60, quantite))

    puissance = None
    try:
        if str(brut.get("puissance") or "").strip():
            puissance = int(float(brut.get("puissance")))
            if not (1 <= puissance <= 5):
                puissance = None
    except (TypeError, ValueError):
        puissance = None
    if puissance is None:
        puissance = deduire_puissance(couleur, cepages)

    prix = None
    try:
        if str(brut.get("prix") or "").strip():
            prix = round(max(0.0, float(str(brut.get("prix")).replace(",", "."))), 2)
    except (TypeError, ValueError):
        prix = None

    return {
        "nom": nom,
        "producteur": str(brut.get("producteur") or "").strip()[:120],
        "region": str(brut.get("region") or "").strip()[:80],
        "pays": str(brut.get("pays") or "").strip()[:60],
        "millesime": millesime,
        "couleur": couleur,
        "cepages": cepages,
        "puissance": puissance,
        "quantite": quantite,
        "prix": prix,
        "garde": str(brut.get("garde") or "").strip()[:60],
        "note": str(brut.get("note") or "").strip()[:1500],
        "photo": os.path.basename(str(brut.get("photo") or "").strip())[:80],
        "par": str(brut.get("par") or "").strip()[:40] or "inconnu",
        "le": str(brut.get("le") or date.today().isoformat())[:10],
    }


def fichier_de(identifiant):
    """Le chemin de la bouteille portant cet identifiant, ou None.

    🔴 On compare aux fichiers réellement présents plutôt que de reconstruire
    le nom : c'est ce qui empêche un identifiant fabriqué (« ../PROFILE »)
    d'aller taper ailleurs que dans le dossier des bouteilles.
    """
    ident = str(identifiant or "").strip()
    if not ident or not os.path.isdir(DOSSIER):
        return None
    for f in sorted(os.listdir(DOSSIER)):
        if f.endswith(".json") and f[:-5] == ident:
            return os.path.join(DOSSIER, f)
    return None


def supprimer(identifiant, par=""):
    p = fichier_de(identifiant)
    if not p:
        sys.exit("❌ Bouteille introuvable : %s" % identifiant)
    nom = json.load(open(p, encoding="utf-8")).get("nom", identifiant)
    os.remove(p)
    print("🗑  bouteille retirée de la cave : %s%s" % (nom, (" — par %s" % par) if par else ""))


def modifier(identifiant, donnees):
    """Réécrit une bouteille EN PLACE : même fichier, même identifiant.

    🔑 Garder le fichier, c'est garder le lien : l'historique (fois servie,
    dernier service) n'est pas perdu en corrigeant une faute de frappe.
    Ce qui n'est pas dans le formulaire (la photo, la date d'ajout, l'historique
    de service) est repris de l'ancienne version plutôt que perdu.
    """
    p = fichier_de(identifiant)
    if not p:
        sys.exit("❌ Bouteille introuvable : %s" % identifiant)
    ancienne = json.load(open(p, encoding="utf-8"))

    for champ in ("le", "photo", "fois_servie", "dernier_service"):
        if champ not in donnees and champ in ancienne:
            donnees[champ] = ancienne[champ]

    bouteille = nettoyer(donnees)
    bouteille["id"] = ancienne.get("id") or os.path.basename(p)[:-5]
    if ancienne.get("fois_servie"):
        bouteille["fois_servie"] = ancienne["fois_servie"]
    if ancienne.get("dernier_service"):
        bouteille["dernier_service"] = ancienne["dernier_service"]
    bouteille["modifie_le"] = date.today().isoformat()
    if bouteille["par"] != ancienne.get("par"):
        # on ne réécrit pas la signature d'origine : on note qui a retouché
        bouteille["par"], bouteille["modifie_par"] = ancienne.get("par", "inconnu"), bouteille["par"]
    ecrire(bouteille, p)
    print("✏️  bouteille modifiée : %s" % bouteille["nom"])


def ouvrir_bouteille(identifiant, n=1):
    """Décrémente le stock : une bouteille de moins, une fois de plus servie."""
    p = fichier_de(identifiant)
    if not p:
        sys.exit("❌ Bouteille introuvable : %s" % identifiant)
    b = json.load(open(p, encoding="utf-8"))
    dispo = int(b.get("quantite") or 0)
    if dispo <= 0:
        sys.exit("❌ Plus aucune bouteille en cave : %s" % b.get("nom", identifiant))
    n = max(1, min(dispo, int(n) if str(n or "").strip() else 1))
    b["quantite"] = dispo - n
    b["fois_servie"] = int(b.get("fois_servie") or 0) + n
    b["dernier_service"] = date.today().isoformat()
    ecrire(b, p)
    print("🍷 bouteille ouverte : %s — reste %d en cave" % (b.get("nom", identifiant), b["quantite"]))


def ecrire(bouteille, chemin):
    json.dump(bouteille, open(chemin, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


def chemin_libre(bouteille):
    """bouteilles/AAAA-MM-JJ-nom.json, suffixé au besoin pour ne rien écraser."""
    base = "%s-%s" % (bouteille["le"], slug(bouteille["nom"]))
    p = os.path.join(DOSSIER, base + ".json")
    n = 2
    while os.path.exists(p):
        p = os.path.join(DOSSIER, "%s-%d.json" % (base, n))
        n += 1
    return p


def main():
    ap = argparse.ArgumentParser(description="Ajoute une bouteille à la cave partagée")
    ap.add_argument("bouteille", nargs="?", help="la bouteille, en JSON")
    ap.add_argument("--fichier", help="fichier JSON à lire à la place")
    ap.add_argument("--modifier",
                    help="identifiant de la bouteille à réécrire (elle garde son fichier)")
    ap.add_argument("--supprimer", help="identifiant de la bouteille à retirer")
    ap.add_argument("--ouvrir", help="identifiant de la bouteille à ouvrir (décrémente le stock)")
    ap.add_argument("--n", type=int, default=1, help="nombre de bouteilles ouvertes (--ouvrir)")
    a = ap.parse_args()

    os.makedirs(DOSSIER, exist_ok=True)

    if a.supprimer:
        supprimer(a.supprimer)
        return
    if a.ouvrir:
        ouvrir_bouteille(a.ouvrir, a.n)
        return

    brut = a.bouteille
    if a.fichier:
        brut = open(a.fichier, encoding="utf-8").read()
    if not brut:
        sys.exit("usage: ajouter_bouteille.py '<json>'  ·  ou --fichier <chemin>")

    try:
        donnees = json.loads(brut) if isinstance(brut, str) else brut
    except ValueError as e:
        sys.exit("❌ JSON invalide : %s" % e)

    # l'appli envoie l'opération DANS la bouteille : la passerelle la transmet
    # telle quelle, il n'y a donc rien de plus à faire circuler côté GitHub
    op = str(donnees.pop("_op", "") or "").strip().lower()
    ident = a.modifier or donnees.pop("id", "")

    if op == "supprimer" or (a.supprimer and not op):
        supprimer(ident, str(donnees.get("par") or "")[:40])
        return
    if op == "ouvrir":
        ouvrir_bouteille(ident, donnees.get("n") or 1)
        return
    if op == "modifier" or a.modifier:
        modifier(ident, donnees)
        return

    bouteille = nettoyer(donnees)
    p = chemin_libre(bouteille)
    bouteille["id"] = os.path.basename(p)[:-5]
    ecrire(bouteille, p)

    print("🍷 bouteille ajoutée à la cave : %s — par %s"
          % (bouteille["nom"], bouteille["par"]))


if __name__ == "__main__":
    main()
