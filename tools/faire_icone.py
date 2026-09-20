#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fabrique les icônes PNG de l'appli Cave, sans aucune dépendance.

    py tools/faire_icone.py app

Écrit icon-180.png, icon-192.png et icon-512.png : ce sont elles qui donnent à
l'appli son icône propre sur l'écran d'accueil du téléphone — distincte de
Cuisine et d'Entraînement, sinon on ne les distingue pas sur l'écran d'accueil.

Pas de Pillow, pas d'ImageMagick : on écrit le PNG à la main (zlib + CRC), avec
un anti-aliasing par supersampling (chaque pixel est moyenné sur une grille de
sous-points) pour un trait net plutôt que crénelé. Ça marche partout, y compris
dans GitHub Actions.
"""
import math
import os
import struct
import sys
import zlib

# palette de l'icône : parchemin et bordeaux — celle de l'écran clair de
# l'appli, choisie pour rester lisible et sobre à la taille d'une icône.
FOND = (243, 236, 231)      # crème, comme --paper en thème clair
ENCRE = (122, 46, 58)       # bordeaux, comme --accent


def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def melange(fond, encre, t):
    return tuple(round(fond[i] + (encre[i] - fond[i]) * t) for i in range(3))


def ecrire_png(chemin, taille, couverture, fond=FOND, encre=ENCRE, ss=4):
    """couverture(x, y) -> 0..1 (part d'encre à ce pixel). Supersample ss×ss
    pour un anti-aliasing propre, sans aucune dépendance externe."""
    lignes = bytearray()
    for y in range(taille):
        lignes.append(0)                      # filtre « None » pour la ligne
        for x in range(taille):
            acc = 0.0
            for sy in range(ss):
                for sx in range(ss):
                    acc += couverture(x + (sx + 0.5) / ss, y + (sy + 0.5) / ss)
            lignes.extend(melange(fond, encre, clamp(acc / (ss * ss))))

    def bloc(nom, data):
        c = nom + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c))

    png = (b"\x89PNG\r\n\x1a\n"
           + bloc(b"IHDR", struct.pack(">IIBBBBB", taille, taille, 8, 2, 0, 0, 0))
           + bloc(b"IDAT", zlib.compress(bytes(lignes), 9))
           + bloc(b"IEND", b""))
    open(chemin, "wb").write(png)
    return len(png)


def couvrance_segment(px, py, x1, y1, x2, y2, epaisseur):
    """La couverture d'un trait de cette épaisseur entre (x1,y1) et (x2,y2)."""
    dx, dy = x2 - x1, y2 - y1
    l2 = dx * dx + dy * dy
    t = 0.0 if l2 == 0 else clamp(((px - x1) * dx + (py - y1) * dy) / l2)
    d = math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))
    return clamp(epaisseur / 2 - d + 0.5)


def _bezier(p0, p1, p2, p3, t):
    u = 1 - t
    x = u**3 * p0[0] + 3 * u*u*t * p1[0] + 3 * u*t*t * p2[0] + t**3 * p3[0]
    y = u**3 * p0[1] + 3 * u*u*t * p1[1] + 3 * u*t*t * p2[1] + t**3 * p3[1]
    return x, y


def icone_cave(taille):
    """Un verre à vin effilé, en trait fin. Lisible à 40 px.

    Le galbe de la coupe est une courbe de Bézier échantillonnée puis tracée
    comme une ligne brisée (même technique que pour un ruban ou une vrille) :
    ça donne un contour lisse, sans le coude qu'une formule en deux morceaux
    laisserait au raccord. Silhouette sobre, pas un dessin réaliste — dans le
    même esprit que la marmite en ligne claire de Cuisine.
    """
    ech = taille / 100.0
    c = taille / 2.0
    trait = 2.0 * ech

    y_bord, y_pied_haut, y_pied_bas, y_base = 18 * ech, 60 * ech, 80 * ech, 84 * ech
    l_bord, l_base = 16 * ech, 12 * ech

    # le galbe de la coupe, du bord au raccord avec la tige (x=0, sur l'axe)
    p0 = (l_bord, y_bord)
    p1 = (23 * ech, 34 * ech)
    p2 = (19 * ech, 50 * ech)
    p3 = (0.0, y_pied_haut)
    galbe = [_bezier(p0, p1, p2, p3, i / 48) for i in range(49)]

    def cov(px, py):
        meilleure = 0.0
        for i in range(len(galbe) - 1):
            x1, y1 = galbe[i]
            x2, y2 = galbe[i + 1]
            if abs(py - (y1 + y2) / 2) > 6 * ech:
                continue
            meilleure = max(meilleure, couvrance_segment(px, py, c + x1, y1, c + x2, y2, trait))
            meilleure = max(meilleure, couvrance_segment(px, py, c - x1, y1, c - x2, y2, trait))
        # le rebord, qui ferme le haut de la coupe
        meilleure = max(meilleure, couvrance_segment(px, py, c - l_bord, y_bord, c + l_bord, y_bord, trait))
        # la tige
        meilleure = max(meilleure, couvrance_segment(px, py, c, y_pied_haut, c, y_pied_bas, trait))
        # la base
        meilleure = max(meilleure, couvrance_segment(px, py, c - l_base, y_base, c + l_base, y_base, trait))
        return meilleure

    return cov


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
