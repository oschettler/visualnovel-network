"""Bildinhalte der sechs Figurenportraets.

Stil: doc/stil-tuschezeichnung.md -- Technik: tools/ink.py
Aufruf:  python3 tools/portraits.py [name ...]
"""

import os
import sys

from ink import Pen

OUT = os.path.join(os.path.dirname(__file__), "..", "doc", "img")
W, H = 400, 520

FINE = (0, 3.0, 0)      # Konturstrich
FINER = (0, 2.0, 0)     # Detailstrich
BOLD = (0, 9.0, 0)      # Akzentstrich
WEDGE = (7.5, 4.0, 0)   # Keil: dick angesetzt, spitz aus


def kontur(p, pts, w=FINE, amp=1.5, cuts=None, druck=None, druck_w=5.0):
    """Konturzug mit Druckstellen: ueber Teilstuecken laeuft ein zweiter,
    schwererer Strich mit -- so entsteht die ungleiche Gewichtung echter
    Federzuege, statt einer gleichmaessig starken Linie."""
    p.stroke(pts, w=w, amp=amp, cuts=cuts)
    for a, b in (druck or []):
        p.stroke(pts, w=(0, druck_w, 0), amp=amp * 0.7, cuts=[(a, b)])


def ohr(p, x, y, s=1.0, flip=1):
    p.stroke([(x, y), (x - 9 * s * flip, y + 9 * s), (x + 1 * s * flip, y + 22 * s)],
             w=(0, 2.0, 0), amp=0.7)


def auge(p, x, y, r=7.5, tilt=0.0, lid=True):
    """Mandel mit Punktpupille -- kein Augapfel-Oval."""
    p.stroke([(x - r, y + tilt), (x - r * 0.3, y - r * 0.62),
              (x + r * 0.45, y - r * 0.5), (x + r, y - tilt * 0.5)],
             w=(0, 2.0, 0), amp=0.4)
    p.stroke([(x - r * 0.8, y + tilt + 1), (x, y + r * 0.5), (x + r * 0.85, y + 1)],
             w=(0, 1.5, 0), amp=0.4)
    p.dot(x + r * 0.05, y - r * 0.08, 2.5)
    if lid:
        p.stroke([(x - r * 1.1, y - r * 0.9), (x, y - r * 1.35), (x + r * 0.9, y - r * 1.0)],
                 w=(0, 1.3, 0), amp=0.4)


def nase(p, x, y0, y1, w=8):
    p.stroke([(x + 2, y0), (x - 2, y0 + (y1 - y0) * 0.55), (x - w, y1),
              (x - w * 0.2, y1 + 5), (x + 3, y1 + 3)],
             w=(0, 2.4, 0), amp=0.6)


def mund(p, x0, y0, x1, y1, bow=4, punkte=True):
    p.stroke([(x0, y0), ((x0 + x1) / 2, (y0 + y1) / 2 + bow), (x1, y1)],
             w=(0, 2.2, 0), amp=0.5)
    if punkte:
        p.dot(x0, y0, 1.9)
        p.dot(x1, y1, 1.9)


def hals_schultern(p, schulter_l=None, schulter_r=None):
    p.stroke([(177, 348), (174, 374), (177, 398)], w=(0, 2.8, 0), amp=0.8)
    p.stroke([(224, 344), (228, 372), (227, 396)], w=(0, 2.6, 0), amp=0.8)
    # Schatten unter dem Kinn -- die dunkelste Stelle des Gesichts
    p.stroke([(176, 352), (200, 370), (224, 351)], w=(2.5, 11.0, 2.0), amp=0.9)
    p.hatch(184, 372, 4, 13, 1.35, 9, w=(0, 1.7, 0))
    sl = schulter_l or [(150, 402), (103, 425), (66, 467), (52, 520)]
    sr = schulter_r or [(253, 399), (299, 423), (335, 465), (349, 520)]
    kontur(p, sl, w=FINE, amp=1.8, cuts=[(0.0, 0.62), (0.70, 1.0)],
           druck=[(0.16, 0.50)], druck_w=5.5)
    kontur(p, sr, w=FINE, amp=1.8, cuts=[(0.0, 0.55), (0.63, 1.0)],
           druck=[(0.62, 0.94)], druck_w=5.0)


def michael(p):
    # Kopf leicht gedreht: linke Wange voller, rechte Seite knapper
    # --- Schaedel: kahl, Kontur laeuft ueber den Scheitel
    kontur(p, [(133, 190), (135, 141), (153, 104), (186, 84), (221, 86),
               (248, 107), (263, 145), (267, 194)],
           w=(0, 3.2, 0), amp=1.6,
           cuts=[(0.0, 0.31), (0.37, 0.79), (0.85, 1.0)],
           druck=[(0.04, 0.24)], druck_w=5.2)
    # --- Wangen und Kiefer
    kontur(p, [(133, 196), (131, 246), (140, 297), (158, 332), (181, 355), (204, 364)],
           w=(0, 3.3, 0), amp=1.7, cuts=[(0.0, 0.56), (0.63, 1.0)],
           druck=[(0.42, 0.86)], druck_w=6.0)
    kontur(p, [(200, 365), (227, 351), (246, 321), (259, 277), (267, 231), (267, 190)],
           w=(0, 3.0, 0), amp=1.7, cuts=[(0.0, 0.73), (0.80, 1.0)],
           druck=[(0.10, 0.42)], druck_w=5.0)

    ohr(p, 130, 220, 1.05, 1)
    ohr(p, 270, 214, 0.95, -1)

    # --- Restliches Haar: nach hinten-unten gestrichen, Scheitel kahl
    p.hairs([(150, 126), (136, 148), (129, 175), (132, 200)], 34, 27,
            w=(3.4, 1.8, 0), spread=0.30, curl=0.35, angle=2.62,
            curl_bias=0.6, length_var=0.55)
    p.hairs([(152, 132), (140, 156), (134, 182)], 16, 15,
            w=(2.6, 1.4, 0), spread=0.34, curl=0.3, angle=2.45, length_var=0.5)
    p.hairs([(250, 124), (264, 146), (271, 172), (269, 197)], 30, 25,
            w=(3.2, 1.7, 0), spread=0.30, curl=0.35, angle=0.54,
            curl_bias=-0.6, length_var=0.55)
    p.hairs([(248, 130), (260, 154), (266, 180)], 14, 14,
            w=(2.5, 1.4, 0), spread=0.34, curl=0.3, angle=0.70, length_var=0.5)

    # --- Stirnfalten
    p.stroke([(158, 158), (198, 149), (238, 159)], w=(0, 1.9, 0), amp=0.9,
             cuts=[(0.04, 0.46), (0.56, 0.96)])
    p.stroke([(163, 171), (198, 163), (236, 172)], w=(0, 1.6, 0), amp=0.9,
             cuts=[(0.1, 0.88)])

    # --- Brauen: schwere Keile, asymmetrisch
    p.stroke([(143, 197), (166, 187), (187, 193)], w=(1.8, 6.0, 0), amp=0.7)
    p.stroke([(213, 190), (235, 184), (256, 195)], w=(0, 6.4, 1.8), amp=0.7)

    auge(p, 165, 221, 7.8, tilt=1.0)
    auge(p, 235, 216, 7.0, tilt=-0.5)

    # --- Brille: schiefe Ovale, offen gezeichnet
    p.stroke([(142, 219), (150, 201), (171, 197), (188, 207), (189, 227),
              (174, 241), (152, 238), (143, 225), (145, 212)],
             w=(0, 3.0, 0), amp=0.9)
    p.stroke([(213, 214), (221, 197), (243, 194), (259, 203), (261, 222),
              (246, 236), (225, 234), (215, 221), (217, 209)],
             w=(0, 2.8, 0), amp=0.9)
    p.stroke([(189, 212), (200, 205), (213, 210)], w=(0, 2.6, 0), amp=0.5)
    p.stroke([(142, 215), (130, 210)], w=(3.0, 1.8, 0), amp=0.4)
    p.stroke([(261, 209), (272, 205)], w=(2.8, 1.7, 0), amp=0.4)

    nase(p, 200, 227, 274, w=10)

    # --- Schnauzbart: von der Mitte nach aussen gestrichen
    p.hairs([(196, 283), (184, 285), (172, 290)], 20, 15,
            w=(3.4, 1.7, 0), spread=0.34, curl=0.3, angle=2.95,
            curl_bias=0.8, length_var=0.5)
    p.hairs([(200, 283), (212, 285), (225, 290)], 20, 15,
            w=(3.4, 1.7, 0), spread=0.34, curl=0.3, angle=0.22,
            curl_bias=-0.8, length_var=0.5)
    p.blob(198, 288, 5.0, 0.45, 9, spikes=2, spike_len=1.6)

    mund(p, 178, 309, 221, 305, bow=4)

    # --- Nasolabialfalten, Kraehenfuesse
    p.stroke([(182, 275), (174, 293), (168, 304)], w=(0, 2.0, 0), amp=0.6)
    p.stroke([(219, 273), (227, 291), (232, 301)], w=(0, 1.9, 0), amp=0.6)
    p.hatch(138, 230, 3, 10, 0.35, 5, w=(0, 1.6, 0))
    p.hatch(259, 227, 3, 9, 2.75, 5, w=(0, 1.5, 0))

    hals_schultern(p)

    # --- Sakko: Revers mit kraeftigen Akzentstrichen
    p.stroke([(152, 402), (176, 440), (200, 470)], w=(2.0, 8.5, 0), amp=1.0)
    p.stroke([(250, 400), (226, 438), (202, 470)], w=(2.0, 8.0, 0), amp=1.0)
    p.stroke([(163, 404), (186, 436), (200, 462)], w=(0, 2.0, 0), amp=0.8)
    p.stroke([(240, 402), (218, 434), (203, 462)], w=(0, 2.0, 0), amp=0.8)
    # Hemdkragen
    p.stroke([(182, 398), (196, 420), (200, 432)], w=(0, 2.2, 0), amp=0.6)
    p.stroke([(220, 396), (206, 418), (201, 432)], w=(0, 2.2, 0), amp=0.6)
    # Falten am Aermelansatz
    p.stroke([(96, 452), (118, 476), (128, 508)], w=(0, 6.5, 0), amp=1.2)
    p.stroke([(306, 450), (286, 474), (277, 506)], w=(0, 6.0, 0), amp=1.2)
    p.hatch(84, 486, 4, 16, 1.15, 7, w=(0, 1.6, 0))

    p.spatter([(74, 300, 52, 9), (330, 306, 50, 9),
               (206, 486, 120, 7), (200, 66, 108, 5)])


def sarah(p):
    """Dunkles, glattes Haar bis auf die Schultern, muede und entschlossen."""
    kontur(p, [(141, 176), (138, 232), (147, 288), (163, 328), (182, 353), (203, 363)],
           w=(0, 3.2, 0), amp=1.6, cuts=[(0.0, 0.58), (0.65, 1.0)],
           druck=[(0.44, 0.88)], druck_w=5.6)
    kontur(p, [(200, 364), (226, 351), (243, 322), (255, 280), (262, 232), (261, 176)],
           w=(0, 3.0, 0), amp=1.6, cuts=[(0.0, 0.74), (0.81, 1.0)],
           druck=[(0.08, 0.40)], druck_w=5.0)

    # --- Haar: Scheitel und je zwei Straehnenklumpen mit weisser Luecke
    p.patch([(143, 154), (152, 110), (182, 88), (216, 89), (248, 110),
             (259, 156), (240, 130), (212, 119), (182, 122), (158, 132)])
    p.patch([(140, 146), (114, 190), (104, 252), (110, 316), (124, 372),
             (152, 380), (152, 310), (146, 246), (150, 186)])
    p.patch([(261, 146), (287, 190), (297, 252), (291, 316), (277, 372),
             (249, 380), (249, 310), (255, 246), (251, 186)])
    # Ausgefranste Raender und auslaufende Spitzen
    p.hairs([(140, 158), (118, 208), (110, 268), (118, 340)], 32, 21,
            w=(3.2, 1.7, 0), spread=0.26, curl=0.3, angle=1.90,
            curl_bias=0.7, length_var=0.5)
    p.hairs([(262, 158), (284, 208), (292, 268), (284, 340)], 32, 21,
            w=(3.2, 1.7, 0), spread=0.26, curl=0.3, angle=1.24,
            curl_bias=-0.7, length_var=0.5)
    p.hairs([(118, 368), (148, 380)], 16, 24, w=(3.0, 1.6, 0), spread=0.30,
            curl=0.25, angle=1.62, length_var=0.6)
    p.hairs([(284, 368), (254, 380)], 16, 24, w=(3.0, 1.6, 0), spread=0.30,
            curl=0.25, angle=1.52, length_var=0.6)
    # Scheitel: Straehnen nach beiden Seiten, Kante aufgerauht
    p.hairs([(198, 106), (174, 114), (152, 134)], 18, 27, w=(2.8, 1.5, 0),
            spread=0.26, curl=0.3, angle=2.55, curl_bias=0.6, length_var=0.45)
    p.hairs([(202, 106), (226, 114), (249, 134)], 18, 27, w=(2.8, 1.5, 0),
            spread=0.26, curl=0.3, angle=0.60, curl_bias=-0.6, length_var=0.45)
    p.hairs([(160, 96), (200, 87), (242, 97)], 16, 13, w=(2.4, 1.3, 0),
            spread=0.4, curl=0.4, out_dir=-1, curl_bias=0.4, length_var=0.6)

    ohr(p, 137, 224, 0.9, 1)
    ohr(p, 265, 220, 0.9, -1)

    p.stroke([(150, 200), (172, 193), (190, 199)], w=(1.5, 4.6, 0), amp=0.6)
    p.stroke([(212, 197), (232, 191), (252, 199)], w=(0, 4.8, 1.5), amp=0.6)

    auge(p, 170, 224, 7.6, tilt=0.8)
    auge(p, 234, 220, 7.2, tilt=-0.4)
    # Muede Schatten unter den Augen
    p.stroke([(159, 238), (172, 243), (184, 239)], w=(0, 1.6, 0), amp=0.5)
    p.stroke([(220, 235), (233, 240), (245, 236)], w=(0, 1.5, 0), amp=0.5)

    nase(p, 202, 230, 274, w=8)
    mund(p, 181, 310, 222, 306, bow=3)
    p.stroke([(186, 278), (179, 294)], w=(0, 1.7, 0), amp=0.5)
    p.stroke([(218, 276), (225, 292)], w=(0, 1.6, 0), amp=0.5)

    hals_schultern(p)
    # Blazer mit Revers
    p.stroke([(152, 402), (177, 442), (201, 472)], w=(2.0, 8.5, 0), amp=1.0)
    p.stroke([(251, 400), (227, 440), (203, 472)], w=(2.0, 8.0, 0), amp=1.0)
    p.stroke([(166, 404), (188, 438), (201, 464)], w=(0, 2.2, 0), amp=0.8)
    p.stroke([(238, 402), (217, 436), (204, 464)], w=(0, 2.2, 0), amp=0.8)
    p.stroke([(100, 450), (120, 476), (130, 508)], w=(0, 6.5, 0), amp=1.2)
    p.stroke([(303, 448), (283, 474), (274, 506)], w=(0, 6.0, 0), amp=1.2)

    p.spatter([(72, 300, 50, 8), (332, 306, 48, 8),
               (206, 488, 118, 7), (200, 70, 100, 5)])


def jamal(p):
    """Kurzes Haar, graue Schlaefen, Dreitagebart, Kapuzenpulli."""
    kontur(p, [(136, 184), (133, 238), (142, 292), (159, 330), (181, 354), (203, 363)],
           w=(0, 3.2, 0), amp=1.6, cuts=[(0.0, 0.57), (0.64, 1.0)],
           druck=[(0.44, 0.88)], druck_w=5.8)
    kontur(p, [(200, 364), (227, 350), (246, 320), (258, 277), (265, 231), (264, 184)],
           w=(0, 3.0, 0), amp=1.6, cuts=[(0.0, 0.73), (0.80, 1.0)],
           druck=[(0.08, 0.42)], druck_w=5.2)

    # --- Kurzhaarschnitt: flach anliegende Masse, kaum Hoehe
    p.patch([(136, 176), (142, 130), (170, 104), (206, 99), (241, 109),
             (262, 137), (266, 180), (254, 150), (226, 133), (188, 131),
             (157, 143)])
    p.hairs([(144, 136), (172, 110), (206, 102), (241, 113), (263, 143)], 46, 9,
            w=(2.8, 1.5, 0), spread=0.26, curl=0.25, out_dir=-1,
            curl_bias=0.5, length_var=0.45)
    p.hairs([(140, 168), (146, 138)], 10, 8, w=(2.2, 1.2, 0), spread=0.3,
            curl=0.3, angle=2.7, length_var=0.5)
    p.hairs([(263, 172), (258, 142)], 10, 8, w=(2.2, 1.2, 0), spread=0.3,
            curl=0.3, angle=0.45, length_var=0.5)
    # Graue Schlaefen: nur duenne Einzelstriche, kaum Masse
    p.hairs([(139, 176), (136, 152), (146, 130)], 9, 14, w=(1.8, 1.0, 0),
            spread=0.24, curl=0.3, angle=2.55, length_var=0.5)
    p.hairs([(263, 172), (265, 148), (256, 128)], 8, 13, w=(1.8, 1.0, 0),
            spread=0.24, curl=0.3, angle=0.60, length_var=0.5)

    ohr(p, 132, 222, 1.0, 1)
    ohr(p, 268, 218, 1.0, -1)

    p.stroke([(146, 202), (169, 194), (188, 200)], w=(1.6, 5.2, 0), amp=0.6)
    p.stroke([(212, 198), (233, 192), (254, 201)], w=(0, 5.4, 1.6), amp=0.6)

    auge(p, 167, 226, 7.6, tilt=0.9)
    auge(p, 235, 222, 7.2, tilt=-0.4)

    nase(p, 201, 232, 276, w=9)
    mund(p, 180, 312, 221, 308, bow=2)

    # --- Dreitagebart: kurze Striche und Punkte laengs des Kiefers
    p.hairs([(150, 300), (168, 332), (200, 352), (232, 330), (250, 298)], 60, 7,
            w=(2.0, 1.1, 0), spread=0.8, curl=0.4, out_dir=1,
            curl_bias=0.0, curl_var=1.0, length_var=0.55)
    for _ in range(26):
        a = p.rng.uniform(0, 6.28)
        rr = p.rng.uniform(0, 1)
        x = 200 + (rr ** 0.5) * 52 * (1 if a < 3.14 else -1) * abs(p.rng.gauss(0, 0.7))
        y = 318 + p.rng.uniform(-24, 26)
        p.dot(max(150, min(252, x)), y, p.rng.uniform(0.7, 1.4))

    p.stroke([(184, 280), (177, 296)], w=(0, 1.8, 0), amp=0.5)
    p.stroke([(219, 278), (226, 294)], w=(0, 1.7, 0), amp=0.5)

    hals_schultern(p)
    # Kapuze und Kordeln
    p.stroke([(150, 404), (176, 420), (200, 424), (226, 419), (252, 402)],
             w=(0, 4.4, 0), amp=1.2)
    p.stroke([(158, 400), (182, 414), (201, 418), (222, 413), (245, 399)],
             w=(0, 2.0, 0), amp=0.9)
    p.stroke([(188, 424), (185, 452), (183, 470)], w=(2.6, 2.0, 0), amp=0.7)
    p.stroke([(214, 424), (218, 452), (220, 470)], w=(2.6, 2.0, 0), amp=0.7)
    p.dot(183, 472, 3.0)
    p.dot(220, 472, 3.0)
    p.stroke([(104, 452), (124, 478), (133, 508)], w=(0, 6.0, 0), amp=1.2)
    p.stroke([(300, 450), (280, 476), (272, 506)], w=(0, 5.6, 0), amp=1.2)

    p.spatter([(74, 300, 50, 9), (330, 306, 48, 8),
               (206, 488, 116, 7), (200, 70, 100, 5)])


def kat(p):
    """Kurzer, zerzauster Schnitt mit Undercut, Sommersprossen, warm."""
    kontur(p, [(140, 182), (137, 234), (147, 288), (164, 326), (183, 350), (203, 359)],
           w=(0, 3.2, 0), amp=1.6, cuts=[(0.0, 0.57), (0.64, 1.0)],
           druck=[(0.42, 0.86)], druck_w=5.6)
    kontur(p, [(200, 360), (226, 347), (244, 318), (256, 276), (262, 230), (261, 182)],
           w=(0, 3.0, 0), amp=1.6, cuts=[(0.0, 0.72), (0.79, 1.0)],
           druck=[(0.08, 0.40)], druck_w=5.0)

    # --- Zerzaust: Masse am Scheitel, kurze Seiten, Spitzen nach aussen
    p.patch([(128, 214), (131, 164), (145, 125), (173, 100), (206, 95),
             (240, 106), (261, 133), (271, 168), (273, 214), (259, 180),
             (250, 148), (222, 130), (186, 128), (156, 146), (145, 180)])
    p.hairs([(146, 128), (175, 101), (208, 96), (240, 108), (261, 138)], 40, 18,
            w=(3.4, 1.8, 0), spread=0.42, curl=0.45, out_dir=-1,
            curl_bias=0.5, curl_var=0.7, length_var=0.6)
    p.hairs([(160, 112), (200, 100), (238, 114)], 18, 20, w=(3.0, 1.6, 0),
            spread=0.5, curl=0.5, out_dir=-1, curl_bias=-0.4, length_var=0.6)
    # Kurz geschorene Seiten: ausgefranste Kante ueber den Ohren
    p.hairs([(137, 190), (136, 214), (143, 236)], 18, 9, w=(2.4, 1.3, 0),
            spread=0.4, curl=0.3, angle=2.75, length_var=0.55)
    p.hairs([(265, 192), (266, 216), (259, 238)], 18, 9, w=(2.4, 1.3, 0),
            spread=0.4, curl=0.3, angle=0.40, length_var=0.55)

    ohr(p, 136, 220, 0.95, 1)
    ohr(p, 265, 216, 0.95, -1)

    p.stroke([(148, 200), (170, 192), (189, 198)], w=(1.4, 4.4, 0), amp=0.6)
    p.stroke([(212, 196), (233, 190), (253, 199)], w=(0, 4.6, 1.4), amp=0.6)

    auge(p, 169, 224, 8.2, tilt=0.8)
    auge(p, 234, 220, 7.8, tilt=-0.4)

    nase(p, 201, 230, 272, w=8)
    # Warmes Laecheln: Bogen mit betonten Mundwinkeln
    p.stroke([(176, 302), (200, 316), (226, 300)], w=(0, 2.6, 0), amp=0.5)
    p.dot(176, 302, 2.2)
    p.dot(226, 300, 2.2)
    p.stroke([(182, 280), (176, 294)], w=(0, 1.7, 0), amp=0.5)
    p.stroke([(220, 278), (226, 292)], w=(0, 1.6, 0), amp=0.5)

    # --- Sommersprossen
    for _ in range(22):
        side = p.rng.choice((-1, 1))
        x = 200 + side * p.rng.uniform(28, 62)
        y = p.rng.uniform(238, 272)
        p.dot(x, y, p.rng.uniform(0.7, 1.4))
    for _ in range(4):
        p.dot(200 + p.rng.uniform(-14, 14), p.rng.uniform(250, 262),
              p.rng.uniform(0.6, 1.1))

    hals_schultern(p)
    # Rundhalsshirt
    p.stroke([(152, 404), (176, 424), (201, 429), (227, 423), (251, 402)],
             w=(0, 4.6, 0), amp=1.2)
    p.stroke([(161, 402), (182, 418), (201, 422), (221, 417), (243, 400)],
             w=(0, 2.0, 0), amp=0.9)
    p.stroke([(102, 452), (122, 478), (131, 508)], w=(0, 6.2, 0), amp=1.2)
    p.stroke([(302, 450), (282, 476), (273, 506)], w=(0, 5.8, 0), amp=1.2)

    p.spatter([(72, 302, 50, 9), (332, 306, 48, 8),
               (206, 488, 116, 7), (200, 66, 104, 5)])


def lena(p):
    """Scharfer Bob mit geradem Pony, wacher und skeptischer Blick."""
    kontur(p, [(144, 186), (141, 238), (150, 290), (166, 326), (184, 350), (203, 359)],
           w=(0, 3.2, 0), amp=1.6, cuts=[(0.0, 0.56), (0.63, 1.0)],
           druck=[(0.44, 0.86)], druck_w=5.6)
    kontur(p, [(200, 360), (225, 347), (242, 318), (253, 276), (259, 232), (258, 186)],
           w=(0, 3.0, 0), amp=1.6, cuts=[(0.0, 0.72), (0.79, 1.0)],
           druck=[(0.08, 0.40)], druck_w=5.0)

    # --- Bob: Klumpen mit Lueckenlicht, Pony, kinnlang
    p.patch([(142, 168), (146, 118), (176, 92), (210, 89), (244, 103),
             (261, 138), (262, 174), (246, 146), (216, 130), (182, 132),
             (158, 144)])
    p.patch([(141, 156), (122, 200), (118, 258), (128, 316), (146, 352),
             (170, 356), (158, 300), (150, 244), (152, 194)])
    p.patch([(262, 156), (281, 200), (285, 258), (275, 316), (257, 352),
             (233, 356), (245, 300), (253, 244), (251, 194)])
    # Pony: kurze Kante ueber der Stirn
    p.hairs([(150, 150), (182, 136), (216, 136), (252, 150)], 34, 11,
            w=(3.0, 1.6, 0), spread=0.24, curl=0.22, out_dir=1,
            curl_bias=0.4, length_var=0.45)
    p.hairs([(146, 348), (166, 354)], 12, 20, w=(3.0, 1.6, 0), spread=0.28,
            curl=0.25, angle=1.66, length_var=0.55)
    p.hairs([(276, 348), (256, 354)], 12, 20, w=(3.0, 1.6, 0), spread=0.28,
            curl=0.25, angle=1.48, length_var=0.55)

    # Skeptisch: eine Braue hoeher als die andere
    p.stroke([(152, 202), (173, 195), (191, 200)], w=(1.4, 4.4, 0), amp=0.6)
    p.stroke([(211, 191), (232, 183), (251, 192)], w=(0, 4.8, 1.4), amp=0.6)

    auge(p, 171, 226, 7.4, tilt=1.0)
    auge(p, 233, 219, 7.0, tilt=-0.6)

    nase(p, 202, 232, 274, w=8)
    # Schmaler, leicht schiefer Mund
    p.stroke([(180, 310), (200, 313), (224, 305)], w=(0, 2.4, 0), amp=0.5)
    p.dot(180, 310, 2.0)
    p.dot(224, 305, 2.0)
    p.stroke([(184, 282), (178, 296)], w=(0, 1.7, 0), amp=0.5)
    p.stroke([(218, 280), (224, 294)], w=(0, 1.6, 0), amp=0.5)
    p.hatch(148, 250, 3, 9, 0.4, 5, w=(0, 1.4, 0))
    p.hatch(252, 246, 3, 8, 2.7, 5, w=(0, 1.3, 0))

    hals_schultern(p)
    # Jacke mit aufgestelltem Kragen
    p.stroke([(148, 398), (166, 428), (200, 440)], w=(2.2, 7.5, 0), amp=1.0)
    p.stroke([(254, 396), (236, 426), (202, 440)], w=(2.2, 7.0, 0), amp=1.0)
    p.stroke([(160, 400), (178, 424), (200, 434)], w=(0, 2.2, 0), amp=0.8)
    p.stroke([(243, 398), (225, 422), (203, 434)], w=(0, 2.2, 0), amp=0.8)
    p.stroke([(126, 424), (144, 446), (150, 470)], w=(0, 5.5, 0), amp=1.1)
    p.stroke([(276, 422), (258, 444), (253, 468)], w=(0, 5.2, 0), amp=1.1)
    p.stroke([(100, 452), (120, 478), (129, 508)], w=(0, 6.0, 0), amp=1.2)
    p.stroke([(303, 450), (283, 476), (275, 506)], w=(0, 5.6, 0), amp=1.2)

    p.spatter([(72, 302, 50, 9), (332, 308, 48, 8),
               (206, 488, 116, 7), (200, 66, 102, 5)])


def tom(p):
    """Wilde Locken, jung, energisch -- offenes Grinsen."""
    kontur(p, [(142, 190), (139, 240), (149, 290), (166, 324), (184, 346), (203, 355)],
           w=(0, 3.2, 0), amp=1.6, cuts=[(0.0, 0.56), (0.63, 1.0)],
           druck=[(0.42, 0.86)], druck_w=5.4)
    kontur(p, [(200, 356), (224, 344), (241, 316), (252, 274), (258, 232), (257, 190)],
           w=(0, 3.0, 0), amp=1.6, cuts=[(0.0, 0.72), (0.79, 1.0)],
           druck=[(0.08, 0.40)], druck_w=4.8)

    # --- Lockenkopf: einzelne Kleckse mit weissen Zwischenraeumen
    p.curls([(138, 202), (132, 152), (156, 108), (196, 90), (238, 98),
             (264, 140), (264, 198)], 28, 9.5, size_var=0.38, jitter=4.0)
    p.curls([(150, 162), (174, 124), (212, 116), (246, 148)], 14, 8.0,
            size_var=0.4, jitter=5.0)
    p.curls([(180, 100), (216, 102)], 5, 7.5, size_var=0.38, jitter=5.0)
    p.hairs([(150, 124), (182, 100), (220, 100), (252, 126)], 22, 14,
            w=(2.6, 1.4, 0), spread=0.6, curl=0.6, out_dir=-1,
            curl_bias=0.3, curl_var=0.9, length_var=0.6)

    ohr(p, 138, 226, 0.95, 1)
    ohr(p, 262, 222, 0.95, -1)

    p.stroke([(150, 206), (172, 197), (190, 203)], w=(1.4, 4.2, 0), amp=0.6)
    p.stroke([(212, 201), (233, 195), (252, 204)], w=(0, 4.4, 1.4), amp=0.6)

    auge(p, 170, 230, 8.4, tilt=0.8)
    auge(p, 234, 226, 8.0, tilt=-0.4)

    nase(p, 201, 236, 274, w=7)

    # --- Offenes Grinsen: Bogen mit dunkler Mundoeffnung
    p.stroke([(172, 300), (200, 320), (228, 298)], w=(0, 3.0, 0), amp=0.5)
    p.patch([(180, 304), (200, 316), (220, 302), (200, 308)], wob=1.2)
    p.dot(172, 300, 2.2)
    p.dot(228, 298, 2.2)
    p.stroke([(180, 282), (174, 294)], w=(0, 1.6, 0), amp=0.5)
    p.stroke([(221, 280), (227, 292)], w=(0, 1.5, 0), amp=0.5)

    for _ in range(10):
        side = p.rng.choice((-1, 1))
        p.dot(200 + side * p.rng.uniform(30, 56), p.rng.uniform(244, 268),
              p.rng.uniform(0.6, 1.2))

    hals_schultern(p)
    # T-Shirt
    p.stroke([(152, 404), (176, 424), (201, 429), (227, 423), (251, 402)],
             w=(0, 4.6, 0), amp=1.2)
    p.stroke([(161, 402), (182, 418), (201, 422), (221, 417), (243, 400)],
             w=(0, 2.0, 0), amp=0.9)
    p.stroke([(104, 454), (124, 478), (133, 508)], w=(0, 6.0, 0), amp=1.2)
    p.stroke([(300, 452), (280, 478), (272, 506)], w=(0, 5.6, 0), amp=1.2)
    p.hatch(150, 486, 4, 15, 1.2, 8, w=(0, 1.6, 0))

    p.spatter([(72, 304, 50, 9), (332, 308, 48, 8),
               (206, 490, 116, 7), (200, 62, 106, 5)])


FIGUREN = {
    "sarah-hoffmann": (sarah, 11),
    "jamal-al-rashid": (jamal, 23),
    "michael-weber": (michael, 4),
    "katharina-mueller": (kat, 37),
    "lena-kowalski": (lena, 52),
    "tom-schneider": (tom, 68),
}


def main(argv):
    names = argv or list(FIGUREN)
    for name in names:
        fn, seed = FIGUREN[name]
        p = Pen(seed)
        fn(p)
        path = os.path.normpath(os.path.join(OUT, name + ".svg"))
        with open(path, "w") as fh:
            fh.write(p.svg(W, H))
        print("geschrieben:", path, f"({len(p.paths)} Pfade)")


if __name__ == "__main__":
    main(sys.argv[1:])
