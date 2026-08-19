#!/usr/bin/env python3
"""Hintergruende der Visual Novel, im Tuschestil der Urmel-Buecher.

Vorlagen: in/u1, in/u2, in/u3 (siehe doc/stil-tuschezeichnung.md). Was diese
Bilder als Szene ausmacht, sind drei Dinge:

1. Es gibt keinen Horizont und keine Waende. Die Gegenstaende stehen auf
   weissem Papier.
2. Der Boden ist nur angedeutet: lockere waagerechte Schraffur, ein paar
   Steinchen, Tuschespritzer. Nie eine gefuellte Flaeche.
3. Geraete und Moebel sind offene, leicht schiefe Umrisse mit wenigen
   Details: Knoepfe als Kreise, Nieten und Tasten als Punktreihen,
   Holzlatten als drei parallele Striche.

Dazu kommt eine Bedingung aus dem Spiel selbst: die Puppen sind transparente
Strichgrafik, der Hintergrund scheint also durch sie hindurch. Alles, was in
der Bildmitte liegt, erscheint mitten im Gesicht der Figuren. Deshalb stehen
die Gegenstaende am linken und rechten Rand, und die Mitte bleibt Papier.
Das ist keine Notloesung, sondern genau der Aufbau der Vorlagen.

Aufruf:
  python3 tools/szenen.py              # alle Hintergruende
  python3 tools/szenen.py sarah-buero  # nur einen
"""

import csv
import os
import sys

from ink import Pen

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "doc", "img", "szenen")
MANIFEST = os.path.join(ROOT, "game", "data", "art.csv")

BREITE, HOEHE = 1024, 684

# Die Dialogbox verdeckt etwa das untere Fuenftel, die Ortsmarke die obere
# linke Ecke. Dazwischen liegt das, was man wirklich sieht.
# Die Bodenandeutung liegt bewusst tief: weiter oben kreuzt sie die Figuren
# auf Halshoehe. Bei 560 verlaeuft sie hinter der Brust und teilweise hinter
# der Dialogbox, was genau der Wirkung der Vorlagen entspricht.
BODEN = 560
LINKS, RECHTS = 150, 874   # Mitten der beiden Seitenzonen

FEIN = (0, 2.6, 0)
KRAEFTIG = (0, 5.5, 0)
KEIL = (6.0, 2.4, 0)


# --------------------------------------------------------------- Grundformen

def zug(p, pts, w=FEIN, amp=1.2, cuts=None):
    """Konturzug mit offenen Enden."""
    p.stroke(pts, w=w, amp=amp, cuts=cuts)


def kasten(p, x, y, b, h, w=FEIN, offen=True):
    """Leicht schiefer Kasten.

    Nur eine Kante bricht auf, und die Linien schiessen ueber die Ecken
    hinaus. Braechen alle vier Kanten symmetrisch in der Mitte, entstuenden
    vier Eckwinkel statt einer Form."""
    zug(p, [(x - 3, y), (x + b + 4, y - 2)], w=w)
    zug(p, [(x + b, y - 3), (x + b + 2, y + h + 4)], w=w,
        cuts=[(0.0, 0.58), (0.70, 1.0)] if offen else None)
    zug(p, [(x + b + 4, y + h), (x - 4, y + h + 2)], w=w)
    zug(p, [(x - 1, y + h + 3), (x, y - 4)], w=w)
    # Akzentstrich an der Unterkante: ohne ihn wirkt der Kasten leer.
    p.stroke([(x + b * 0.12, y + h + 2), (x + b * 0.62, y + h + 3)],
             w=(5.5, 1.4, 0), amp=0.5)


def boden(p, x0, x1, y=BODEN, dichte=26):
    """Lockere waagerechte Schraffur statt einer Linie, plus Steinchen."""
    rng = p.rng
    for _ in range(dichte):
        bx = rng.uniform(x0, x1)
        by = y + rng.uniform(-7, 16)
        ln = rng.uniform(18, 70)
        p.stroke([(bx, by), (bx + ln, by + rng.uniform(-2, 2))],
                 w=(0, rng.uniform(1.2, 2.4), 0), amp=0.5)
    for _ in range(int(dichte * 0.45)):
        sx = rng.uniform(x0, x1)
        sy = y + rng.uniform(2, 24)
        p.blob(sx, sy, rng.uniform(1.6, 4.0), 0.5, 7)
    # Ein schwerer Zug traegt die Bodenlinie, sonst zerfaellt sie zu Fusseln.
    p.stroke([(x0 + (x1 - x0) * 0.18, y + 4), (x0 + (x1 - x0) * 0.62, y + 6)],
             w=(7.0, 2.0, 0), amp=0.7)


def schatten(p, x, y, b):
    """Wenige kurze Striche dicht unter dem Gegenstand, nie ein Block."""
    p.hatch(x + b * 0.12, y, 4, b * 0.2, 0.42, b / 9.0, w=(0, 1.7, 0))


def punktreihe(p, x, y, n, abstand, r=1.6):
    for i in range(n):
        p.dot(x + i * abstand, y + p.rng.uniform(-1.2, 1.2), r)


def tisch(p, x, y, b, h=96):
    """Tischplatte mit zwei Beinen, Beine unten offen."""
    zug(p, [(x, y), (x + b, y - 3)], w=KRAEFTIG, amp=0.8)
    zug(p, [(x + 4, y + 7), (x + b - 6, y + 5)], w=FEIN, amp=0.6)
    zug(p, [(x + 14, y + 8), (x + 10, y + h)], w=FEIN, cuts=[(0.0, 0.85)])
    zug(p, [(x + b - 16, y + 8), (x + b - 10, y + h)], w=FEIN, cuts=[(0.0, 0.85)])
    schatten(p, x + 10, y + h + 6, b)


def stuhl(p, x, y, s=1.0):
    """Stuhl mit Lattenlehne, wie der Kuechenstuhl in u1."""
    h = 168 * s
    b = 88 * s
    zug(p, [(x - 4, y), (x + b + 5, y - 2)], w=(7.0, 2.6, 0), amp=0.7)
    for i in range(3):
        zug(p, [(x + 6 + i * (b - 16) / 3.0, y - 4), (x + 4 + i * (b - 16) / 3.0, y - h * 0.62)],
            w=FEIN, cuts=[(0.05, 0.95)])
    zug(p, [(x + 2, y - h * 0.66), (x + b - 8, y - h * 0.7)], w=KRAEFTIG, amp=0.7)
    zug(p, [(x + 5, y + 4), (x + 1, y + h * 0.42)], w=FEIN, cuts=[(0.0, 0.9)])
    zug(p, [(x + b - 8, y + 4), (x + b - 3, y + h * 0.42)], w=FEIN, cuts=[(0.0, 0.9)])
    schatten(p, x, y + h * 0.46, b)


def monitor(p, x, y, b=120, h=86):
    kasten(p, x, y, b, h, w=KRAEFTIG)
    zug(p, [(x + 8, y + h * 0.28), (x + b - 14, y + h * 0.26)], w=(0, 1.6, 0), amp=0.5)
    zug(p, [(x + 8, y + h * 0.52), (x + b - 30, y + h * 0.5)], w=(0, 1.6, 0), amp=0.5)
    zug(p, [(x + b * 0.42, y + h + 3), (x + b * 0.46, y + h + 20)], w=FEIN)
    zug(p, [(x + b * 0.2, y + h + 21), (x + b * 0.74, y + h + 19)], w=KRAEFTIG, amp=0.6)


def fenster(p, x, y, b, h):
    """Fensterkreuz, aussen kraeftig, Sprossen fein."""
    kasten(p, x, y, b, h, w=KRAEFTIG)
    zug(p, [(x + b / 2.0, y + 4), (x + b / 2.0 + 3, y + h - 4)], w=FEIN)
    zug(p, [(x + 4, y + h / 2.0), (x + b - 4, y + h / 2.0 - 3)], w=FEIN)


def flocken(p, x0, x1, y0, y1, n=26):
    for _ in range(n):
        p.dot(p.rng.uniform(x0, x1), p.rng.uniform(y0, y1), p.rng.uniform(1.0, 2.4))


def regal(p, x, y, b, h):
    """Regal mit Buecherreihen als schraege Striche."""
    kasten(p, x, y, b, h, w=KRAEFTIG)
    for i in range(3):
        by = y + h * (i + 1) / 4.0
        zug(p, [(x + 2, by), (x + b - 2, by - 2)], w=FEIN)
        bx = x + 8
        while bx < x + b - 14:
            neig = p.rng.uniform(-6, 6)
            p.stroke([(bx, by - 4), (bx + neig, by - p.rng.uniform(20, 30))],
                     w=(0, p.rng.uniform(1.8, 3.4), 0), amp=0.4)
            bx += p.rng.uniform(7, 13)


def stapel(p, x, y, n=7, b=70):
    """Papierstapel.

    Nur waagerechte Striche uebereinander sehen aus wie Schraffur. Erst die
    seitlichen Kanten und der schwere Zug oben machen daraus einen Stapel."""
    versatz = []
    for i in range(n):
        dy = y - i * 8
        dx = p.rng.uniform(-6, 6)
        versatz.append((dx, dy))
        zug(p, [(x + dx, dy), (x + b + dx, dy - p.rng.uniform(-2, 2))],
            w=(0, 2.2, 0), amp=0.4)
    dx0, dy0 = versatz[0]
    dxn, dyn = versatz[-1]
    zug(p, [(x + dx0 - 1, dy0 + 2), (x + dxn - 1, dyn - 2)], w=(0, 2.4, 0), amp=0.8)
    zug(p, [(x + b + dx0, dy0 + 2), (x + b + dxn, dyn - 2)], w=(0, 2.4, 0), amp=0.8)
    p.stroke([(x + dxn + 6, dyn - 1), (x + dxn + b * 0.7, dyn - 2)],
             w=(5.0, 1.4, 0), amp=0.4)
    schatten(p, x, y + 8, b)


def serverschrank(p, x, y, b=104, h=210):
    """Schrank mit Einschueben, Punktreihen als Anzeigen."""
    kasten(p, x, y, b, h, w=KRAEFTIG)
    for i in range(6):
        ey = y + 16 + i * (h - 26) / 6.0
        zug(p, [(x + 6, ey), (x + b - 6, ey - 1)], w=FEIN)
        punktreihe(p, x + 12, ey - 7, 4, 9, 1.4)
    for i in range(3):
        zug(p, [(x + b, y + h - 30 - i * 12), (x + b + 26 + i * 8, y + h - 6 - i * 4)],
            w=(0, 2.2, 0), amp=1.6)


def apparat(p, x, y, b=150, h=110):
    """Geraet mit Knoepfen, Zahnrad und Kabeln, nach u2 und u3."""
    kasten(p, x, y, b, h, w=KRAEFTIG)
    p.stroke([(x + 18, y + 26), (x + 34, y + 24)], w=(0, 2.2, 0), amp=0.5)
    for cx, cy, r in ((x + 30, y + 52, 13), (x + 62, y + 52, 9)):
        p.stroke([(cx - r, cy), (cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)],
                 w=(0, 2.2, 0), amp=0.8)
        p.dot(cx, cy, 2.0)
    punktreihe(p, x + 92, y + 30, 5, 11)
    punktreihe(p, x + 92, y + 48, 5, 11)
    zr = 18
    p.stroke([(x + b - 24, y - 6 - zr), (x + b - 24 + zr, y - 6), (x + b - 24, y - 6 + zr),
              (x + b - 24 - zr, y - 6), (x + b - 24, y - 6 - zr)], w=(0, 2.6, 0), amp=1.4)
    for i in range(3):
        zug(p, [(x + b, y + h - 20 - i * 14), (x + b + 30 + i * 10, y + h + 10 - i * 6)],
            w=(0, 2.0, 0), amp=1.8)
    schatten(p, x, y + h + 6, b)


def kolben(p, x, y, s=1.0):
    """Rundkolben auf Dreifuss, nach u3."""
    r = 26 * s
    p.stroke([(x - r, y), (x - r * 0.7, y - r * 1.1), (x, y - r * 1.35),
              (x + r * 0.7, y - r * 1.1), (x + r, y), (x + r * 0.6, y + r * 0.7),
              (x, y + r * 0.9), (x - r * 0.6, y + r * 0.7), (x - r, y)],
             w=(0, 2.2, 0), amp=0.9)
    zug(p, [(x - 5 * s, y - r * 1.3), (x - 6 * s, y - r * 2.1)], w=FEIN)
    zug(p, [(x + 5 * s, y - r * 1.3), (x + 7 * s, y - r * 2.1)], w=FEIN)
    zug(p, [(x - r, y + r * 0.5), (x - r * 1.2, y + r * 1.4)], w=FEIN)
    zug(p, [(x + r, y + r * 0.5), (x + r * 1.2, y + r * 1.4)], w=FEIN)


def pflanze(p, x, y, s=1.0):
    kasten(p, x - 22 * s, y, 44 * s, 34 * s, w=FEIN)
    for i in range(7):
        w1 = p.rng.uniform(-1.5, 1.5)
        p.stroke([(x + p.rng.uniform(-8, 8), y),
                  (x + w1 * 22 * s, y - p.rng.uniform(40, 92) * s)],
                 w=(2.4, 1.2, 0), amp=1.4)


def mikrofon(p, x, y):
    zug(p, [(x, y), (x + 2, y - 78)], w=FEIN)
    p.blob(x + 3, y - 88, 11, 0.4, 8)
    zug(p, [(x - 20, y), (x + 22, y - 2)], w=KRAEFTIG, amp=0.7)


def tuerrahmen(p, x, y, b=120, h=250):
    zug(p, [(x, y + h), (x - 2, y)], w=KRAEFTIG, cuts=[(0.02, 0.98)])
    zug(p, [(x, y), (x + b, y - 3)], w=KRAEFTIG, cuts=[(0.03, 0.97)])
    zug(p, [(x + b, y), (x + b + 3, y + h)], w=KRAEFTIG, cuts=[(0.02, 0.98)])


def sofa(p, x, y, b=200):
    kasten(p, x, y, b, 64, w=KRAEFTIG)
    zug(p, [(x + 6, y), (x + 10, y - 54)], w=FEIN)
    zug(p, [(x + 10, y - 54), (x + b - 10, y - 58)], w=KRAEFTIG, amp=0.8)
    zug(p, [(x + b - 8, y - 56), (x + b - 4, y)], w=FEIN)
    schatten(p, x, y + 70, b)


def spritzer(p, zonen, seed):
    p.spatter(zonen, rng_seed=seed)


# ------------------------------------------------------------------- Szenen

def sarah_buero(p):
    """Siebter Stock, Fenster zur verschneiten Stadt, Schreibtisch."""
    fenster(p, 58, 96, 200, 176)
    flocken(p, 40, 290, 70, 300, 30)
    tisch(p, 40, 396, 240)
    monitor(p, 96, 300, 118, 84)
    stapel(p, 806, 388, 8, 78)
    stuhl(p, 880, 400)
    boden(p, 30, 300)
    boden(p, 780, 1000)


def innovation_lab(p):
    """Serverschrank, Geraet mit Kabeln, Kolben auf dem Tisch."""
    serverschrank(p, 52, 176)
    apparat(p, 812, 260)
    tisch(p, 790, 402, 200)
    kolben(p, 858, 384, 0.8)
    boden(p, 30, 260)
    boden(p, 760, 1004)


def michael_buero(p):
    """Buecherregal, Papierstapel, alter Stuhl."""
    regal(p, 44, 130, 190, 300)
    stapel(p, 260, 452, 6, 62)
    tisch(p, 800, 400, 190)
    stapel(p, 838, 386, 9, 74)
    stuhl(p, 906, 470, 0.9)
    boden(p, 30, 320)
    boden(p, 770, 1000)


def konferenzraum(p):
    """Langer Tisch, Stuhlreihe, Projektionsflaeche."""
    kasten(p, 62, 120, 214, 140, w=KRAEFTIG)
    zug(p, [(80, 220), (250, 214)], w=(0, 1.8, 0), amp=0.6)
    zug(p, [(80, 240), (208, 236)], w=(0, 1.8, 0), amp=0.6)
    tisch(p, 30, 430, 300, 80)
    stuhl(p, 852, 452, 0.9)
    stuhl(p, 932, 440, 0.9)
    boden(p, 20, 340)
    boden(p, 800, 1010)


def bri_akademie(p):
    """Pinnwand mit Zetteln, Pflanze, Tisch."""
    kasten(p, 52, 140, 200, 150, w=KRAEFTIG)
    for i in range(6):
        zx = 66 + (i % 3) * 62
        zy = 160 + (i // 3) * 62
        kasten(p, zx, zy, 44, 40, w=(0, 1.6, 0))
    pflanze(p, 906, 452, 1.1)
    tisch(p, 782, 420, 200)
    boden(p, 30, 300)
    boden(p, 760, 1000)


def cafe_bonn(p):
    """Rundes Tischchen, zwei Tassen, Stuhl."""
    zug(p, [(72, 400), (250, 396)], w=KRAEFTIG, amp=0.9)
    zug(p, [(160, 404), (156, 500)], w=FEIN, cuts=[(0.0, 0.9)])
    zug(p, [(120, 500), (200, 498)], w=FEIN)
    for cx in (110, 200):
        p.stroke([(cx - 13, 384), (cx - 11, 396), (cx + 11, 396), (cx + 13, 384)],
                 w=(0, 2.2, 0), amp=0.6)
        p.stroke([(cx + 13, 388), (cx + 23, 392), (cx + 15, 397)], w=(0, 1.8, 0), amp=0.5)
    stuhl(p, 878, 440)
    boden(p, 40, 300)
    boden(p, 800, 1000)


def lena_buero(p):
    """Redaktion: Monitor, Pinnwand mit Faeden, Stapel."""
    monitor(p, 60, 300, 130, 92)
    tisch(p, 34, 404, 230)
    kasten(p, 812, 150, 176, 150, w=KRAEFTIG)
    for i in range(5):
        kasten(p, 826 + (i % 3) * 52, 168 + (i // 3) * 60, 38, 34, w=(0, 1.5, 0))
    zug(p, [(840, 200), (944, 240)], w=(0, 1.4, 0), amp=1.6)
    zug(p, [(852, 250), (930, 190)], w=(0, 1.4, 0), amp=1.6)
    boden(p, 30, 290)
    boden(p, 790, 1000)


def ccc_halle(p):
    """Congress: Traversen, Kabel, Bildschirmwand."""
    zug(p, [(30, 92), (300, 84)], w=KRAEFTIG, amp=1.0)
    for i in range(5):
        zug(p, [(50 + i * 58, 86), (66 + i * 58, 132)], w=FEIN)
    kasten(p, 60, 150, 190, 120, w=KRAEFTIG)
    punktreihe(p, 76, 176, 9, 19)
    punktreihe(p, 76, 206, 9, 19)
    serverschrank(p, 856, 220, 116, 200)
    for i in range(4):
        zug(p, [(300 + i * 12, 96), (340 + i * 20, 150 + i * 26)], w=(0, 1.8, 0), amp=2.2)
    boden(p, 30, 300)
    boden(p, 800, 1010)


def sarahs_wohnung(p):
    """Sofa, Stehlampe, niedriger Tisch."""
    sofa(p, 36, 402, 230)
    zug(p, [(880, 470), (886, 300)], w=FEIN)
    p.stroke([(852, 300), (886, 262), (920, 300)], w=(0, 2.6, 0), amp=0.8)
    zug(p, [(858, 470), (912, 468)], w=KRAEFTIG, amp=0.7)
    tisch(p, 770, 440, 170, 60)
    boden(p, 20, 300)
    boden(p, 750, 1000)


def jamals_wohnung(p):
    """Kuechentisch, Laptop, Foto an der Wand."""
    tisch(p, 44, 400, 230)
    kasten(p, 92, 352, 118, 44, w=KRAEFTIG)
    zug(p, [(92, 352), (76, 300)], w=FEIN)
    kasten(p, 848, 150, 120, 96, w=KRAEFTIG)
    zug(p, [(862, 170), (952, 226)], w=(0, 1.6, 0), amp=0.8)
    boden(p, 30, 300)
    boden(p, 800, 1000)


def goerlitz_kinderzimmer(p):
    """Schmales Fenster, Bett, Kiste."""
    fenster(p, 66, 120, 130, 190)
    kasten(p, 810, 400, 190, 76, w=KRAEFTIG)
    zug(p, [(824, 400), (828, 352)], w=FEIN)
    zug(p, [(828, 352), (960, 348)], w=KRAEFTIG, amp=0.8)
    kasten(p, 748, 452, 60, 54, w=FEIN)
    boden(p, 40, 280)
    boden(p, 720, 1010)


def toms_wg(p):
    """Matratze, Kabelsalat, Poster."""
    kasten(p, 40, 432, 240, 56, w=KRAEFTIG)
    for i in range(4):
        zug(p, [(60 + i * 20, 490), (110 + i * 30, 520)], w=(0, 1.8, 0), amp=2.4)
    kasten(p, 838, 132, 140, 176, w=KRAEFTIG)
    zug(p, [(856, 176), (960, 268)], w=(0, 2.0, 0), amp=1.4)
    zug(p, [(856, 268), (960, 176)], w=(0, 2.0, 0), amp=1.4)
    tisch(p, 800, 420, 180, 70)
    monitor(p, 852, 336, 96, 72)
    boden(p, 30, 300)
    boden(p, 780, 1000)


def kats_wg(p):
    """Kueche: Haengeschrank, Tisch, zwei Tassen."""
    kasten(p, 46, 128, 200, 90, w=KRAEFTIG)
    zug(p, [(146, 132), (148, 214)], w=FEIN)
    tisch(p, 40, 412, 230)
    for cx in (92, 168):
        p.stroke([(cx - 12, 396), (cx - 10, 408), (cx + 10, 408), (cx + 12, 396)],
                 w=(0, 2.2, 0), amp=0.6)
    pflanze(p, 908, 448, 0.9)
    boden(p, 30, 300)
    boden(p, 790, 1000)


def nairobi_hub(p):
    """Helles Fenster, Palme, Sendemast in der Ferne."""
    fenster(p, 52, 110, 210, 170)
    for i in range(6):
        zug(p, [(158, 200), (158 + p.rng.uniform(-70, 70), 200 - p.rng.uniform(30, 70))],
            w=(2.6, 1.0, 0), amp=1.6)
    zug(p, [(902, 452), (908, 216)], w=KRAEFTIG)
    for i in range(4):
        y = 250 + i * 46
        zug(p, [(880 - i * 4, y), (930 + i * 4, y - 4)], w=(0, 1.8, 0), amp=0.6)
    serverschrank(p, 786, 300, 84, 150)
    boden(p, 30, 300)
    boden(p, 760, 1004)


def pressekonferenz(p):
    """Rednerpult, Mikrofone, Kamerastativ."""
    kasten(p, 60, 350, 150, 150, w=KRAEFTIG)
    mikrofon(p, 108, 350)
    mikrofon(p, 148, 354)
    zug(p, [(896, 470), (900, 300)], w=KRAEFTIG)
    zug(p, [(860, 470), (940, 466)], w=FEIN)
    kasten(p, 862, 236, 82, 62, w=KRAEFTIG)
    p.stroke([(944, 250), (972, 240), (972, 292), (944, 282)], w=(0, 2.4, 0), amp=0.7)
    boden(p, 30, 280)
    boden(p, 800, 1000)


def landgericht(p):
    """Richterbank, Wappen, Schranke."""
    kasten(p, 40, 300, 250, 130, w=KRAEFTIG)
    zug(p, [(40, 300), (290, 292)], w=KRAEFTIG, amp=0.9)
    p.stroke([(164, 200), (140, 240), (164, 274), (190, 240), (164, 200)],
             w=(0, 2.6, 0), amp=1.0)
    for i in range(6):
        zug(p, [(800 + i * 34, 470), (802 + i * 34, 380)], w=FEIN)
    zug(p, [(790, 386), (1000, 380)], w=KRAEFTIG, amp=0.8)
    boden(p, 20, 320)
    boden(p, 780, 1010)


def bad_godesberg(p):
    """Arbeitszimmer: Schreibtischlampe, Buecher, Fenster mit Nacht."""
    fenster(p, 60, 110, 170, 150)
    flocken(p, 70, 224, 124, 250, 14)
    tisch(p, 36, 400, 220)
    zug(p, [(96, 396), (100, 336)], w=FEIN)
    p.stroke([(72, 336), (100, 306), (128, 336)], w=(0, 2.4, 0), amp=0.7)
    regal(p, 830, 180, 160, 240)
    boden(p, 30, 290)
    boden(p, 800, 1000)


def uebersicht(p):
    """Neutrale Flaeche fuer die Uebersichtskarte: nur Boden und Spritzer."""
    boden(p, 60, 380, dichte=16)
    boden(p, 660, 980, dichte=16)


SZENEN = {
    "sarah-buero": (sarah_buero, 301),
    "innovation-lab": (innovation_lab, 302),
    "michael-buero": (michael_buero, 303),
    "konferenzraum": (konferenzraum, 304),
    "bri-akademie": (bri_akademie, 305),
    "cafe-bonn": (cafe_bonn, 306),
    "lena-buero": (lena_buero, 307),
    "ccc-halle": (ccc_halle, 308),
    "sarahs-wohnung": (sarahs_wohnung, 309),
    "jamals-wohnung": (jamals_wohnung, 310),
    "goerlitz-kinderzimmer": (goerlitz_kinderzimmer, 311),
    "toms-wg": (toms_wg, 312),
    "kats-wg": (kats_wg, 313),
    "nairobi-hub": (nairobi_hub, 314),
    "pressekonferenz": (pressekonferenz, 315),
    "landgericht": (landgericht, 316),
    "bad-godesberg": (bad_godesberg, 317),
    "uebersicht": (uebersicht, 318),
}


def zeichne(name, fn, seed):
    p = Pen(seed)
    fn(p)
    spritzer(p, [(LINKS, 300, 150, 9), (RECHTS, 320, 150, 9),
                 (512, 540, 300, 7)], seed)
    pfad = os.path.join(OUT, f"{name}.svg")
    with open(pfad, "w") as fh:
        fh.write(p.svg(BREITE, HOEHE))
    print("geschrieben:", os.path.relpath(pfad, ROOT), f"({len(p.paths)} Pfade)")
    return (f"doc/img/szenen/{name}.svg", f"hintergruende/{name}.gif",
            str(BREITE), str(HOEHE), "0")


def schreibe_manifest(neue):
    behalten = []
    if os.path.exists(MANIFEST):
        with open(MANIFEST, newline="", encoding="utf-8") as fh:
            leser = csv.reader(fh)
            next(leser, None)
            for zeile in leser:
                if zeile and not zeile[0].startswith("doc/img/szenen/"):
                    behalten.append(zeile)
    with open(MANIFEST, "w", newline="", encoding="utf-8") as fh:
        s = csv.writer(fh)
        s.writerow(["svg", "gif", "breite", "hoehe", "transparent"])
        for z in behalten:
            s.writerow(z)
        for z in neue:
            s.writerow(z)
    print(f"Manifest geschrieben: game/data/art.csv ({len(behalten) + len(neue)} Zeilen)")


def main(argv):
    os.makedirs(OUT, exist_ok=True)
    namen = argv or list(SZENEN)
    zeilen = []
    for name in namen:
        fn, seed = SZENEN[name]
        zeilen.append(zeichne(name, fn, seed))
    if not argv:
        schreibe_manifest(zeilen)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
