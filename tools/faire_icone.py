#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fabrique les icônes PNG de l'appli Cave, sans aucune dépendance.

    py tools/faire_icone.py app

Écrit icon-180.png, icon-192.png et icon-512.png : ce sont elles qui donnent à
l'appli son icône propre sur l'écran d'accueil du téléphone — distincte de
Cuisine et d'Entraînement, sinon on ne les distingue pas sur l'écran d'accueil.

Pas de Pillow, pas d'ImageMagick : on écrit le PNG à la main (zlib + CRC), ce
qui tient en trente lignes et marche partout, y compris dans GitHub Actions.
"""
import os
import struct
import sys
import zlib

# palette de l'appli Cave (cf. cave.src.html) : ardoise et bordeaux
FOND = (26, 20, 22)         # --paper, ardoise très sombre
VERRE = (167, 46, 58)       # --accent, bordeaux


def ecrire_png(chemin, taille, pixels):
    """pixels(x, y) -> (r, g, b). Écrit un PNG RGB sans transparence."""
    lignes = bytearray()
    for y in range(taille):
        lignes.append(0)                      # filtre « None » pour la ligne
        for x in range(taille):
            lignes.extend(pixels(x, y))

    def bloc(nom, data):
        c = nom + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c))

    png = (b"\x89PNG\r\n\x1a\n"
           + bloc(b"IHDR", struct.pack(">IIBBBBB", taille, taille, 8, 2, 0, 0, 0))
           + bloc(b"IDAT", zlib.compress(bytes(lignes), 9))
           + bloc(b"IEND", b""))
    open(chemin, "wb").write(png)
    return len(png)


def icone_cave(taille):
    """Un verre à vin en ligne claire, sur fond ardoise. Lisible à 40 px.

    Dessiné sur une grille 100×100 puis mis à l'échelle (`ech`) : la coupe,
    le pied et la base d'un verre à vin, dans le même esprit que la marmite
    de l'appli Cuisine — une silhouette simple, pas un dessin réaliste.
    """
    ech = taille / 100.0
    c = taille / 2.0
    trait = max(1.4, 3 * ech)

    y_bord = 22 * ech            # haut de la coupe
    y_ventre = 46 * ech          # le renflement le plus large de la coupe
    y_pied_haut = 58 * ech       # où la coupe se referme sur la tige
    y_pied_bas = 82 * ech        # bas de la tige, au-dessus de la base
    y_base = 86 * ech            # la base, posée
    largeur_bord = 21 * ech
    largeur_ventre = 26 * ech
    largeur_base = 16 * ech

    def largeur_coupe(y):
        """Le rayon de la coupe à la hauteur y : s'évase du col au ventre,
        puis se resserre du ventre au pied — une parabole simple par moitié."""
        if y <= y_ventre:
            t = (y - y_bord) / max(1.0, (y_ventre - y_bord))
            return largeur_bord + (largeur_ventre - largeur_bord) * (t ** 0.6)
        t = (y - y_ventre) / max(1.0, (y_pied_haut - y_ventre))
        t = min(1.0, max(0.0, t))
        return largeur_ventre * (1 - t) ** 1.3

    def dist_segment(px_, py_, x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        l2 = dx * dx + dy * dy
        t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((px_ - x1) * dx + (py_ - y1) * dy) / l2))
        return ((px_ - (x1 + t * dx)) ** 2 + (py_ - (y1 + t * dy)) ** 2) ** 0.5

    def px(x, y):
        cx, cy = x + 0.5, y + 0.5

        # la coupe : deux bords qui suivent le profil du verre
        if y_bord - trait <= cy <= y_pied_haut + trait:
            r = largeur_coupe(min(max(cy, y_bord), y_pied_haut))
            if abs(abs(cx - c) - r) <= trait:
                return VERRE
        # le rebord du verre, un arc fermant le haut de la coupe
        if y_bord - trait <= cy <= y_bord + trait and abs(cx - c) <= largeur_bord + trait:
            return VERRE
        # la tige
        if y_pied_haut <= cy <= y_pied_bas and abs(cx - c) <= trait:
            return VERRE
        # la base
        if y_base - trait <= cy <= y_base + trait and abs(cx - c) <= largeur_base:
            return VERRE

        return FOND

    return px


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: faire_icone.py <dossier de l'appli>")
    dossier = sys.argv[1]
    if not os.path.isdir(dossier):
        sys.exit("❌ Dossier introuvable : " + dossier)
    for t in (180, 192, 512):
        p = os.path.join(dossier, "icon-%d.png" % t)
        n = ecrire_png(p, t, icone_cave(t))
        print("🎨 %s · %d×%d · %.1f Ko" % (os.path.basename(p), t, t, n / 1024))


if __name__ == "__main__":
    main()
