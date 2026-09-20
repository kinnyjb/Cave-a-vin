#!/usr/bin/env python3
"""
Point d'entrée unique de Cave — macOS, Linux et Windows.

    python3 cave.py bouteille '<json>'    (Mac)     ·  py cave.py bouteille '<json>'   (Windows)
    ./lancer bouteille '<json>'           (Mac)     ·  lancer bouteille '<json>'        (Windows)

Commandes :
    bouteille '<json>'    ajoute une bouteille à la cave (bouteilles/)
                           --modifier <id> / --supprimer <id> / --ouvrir <id> pour retoucher
    accord '<plat>'        suggère une bouteille de la cave pour ce plat
    appli                  reconstruit l'appli (page, manifeste, icônes)

Aucune dépendance externe : tout tourne avec le Python déjà installé sur le
système, pas besoin d'environnement virtuel ni de "setup".
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

COMMANDES = {
    "bouteille": "ajouter_bouteille.py",
    "accord": "accord.py",
    "appli": "build_appli.py",
}


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__.strip())
        return 0

    cmd, reste = args[0], args[1:]
    if cmd not in COMMANDES:
        print("❌ Commande inconnue : %s" % cmd)
        print(__doc__.strip())
        return 1

    script = os.path.join(ROOT, "tools", COMMANDES[cmd])
    return subprocess.call([sys.executable, script] + reste)


if __name__ == "__main__":
    sys.exit(main())
