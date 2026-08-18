"""Bildinhalte der sechs Figurenportraets, inklusive Emote-Varianten.

Stil: doc/stil-tuschezeichnung.md -- Technik: tools/ink.py
Die Gesichtsgeometrie jeder Figur (Augen, Brauen, Nase, Mund) steht als
Dictionary in GEO. Wie ein Emote diese Geometrie veraendert (Mundbogen,
Brauenneigung, Lidstellung, Pupillenversatz, Augengroesse) steht als Tabelle
in game/data/emotes.csv -- siehe plans/graphic-novel-plan.md, Abschnitt 7.
Haare, Silhouette, Kleidung, Ohren und Tuschespritzer bleiben figurenspezifischer
Code, unberuehrt von den Emotes.

Aufruf:
  python3 tools/portraits.py                # alles: Ansichten, Emotes, Manifest
  python3 tools/portraits.py sarah-hoffmann  # nur diese Figur
"""

import csv
import os
import sys

from ink import Pen

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "doc", "img")
EMOTE_OUT = os.path.join(OUT, "emotes")
MANIFEST = os.path.join(ROOT, "game", "data", "art.csv")
EMOTES_CSV = os.path.join(ROOT, "game", "data", "emotes.csv")
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


def ohren(p, links, rechts, s=1.0):
    """Bei gedrehtem Kopf verschwindet das abgewandte Ohr hinter der Wange:
    zeigt die Nase nach rechts, bleibt nur das linke Ohr sichtbar."""
    if p.turn > -0.12:
        ohr(p, links[0], links[1], s, 1)
    if p.turn < 0.12:
        ohr(p, rechts[0], rechts[1], s, -1)


def auge(p, x, y, r=7.5, tilt=0.0, lid=True, pupil_dx=0.0, pupil_dy=0.0,
         gross=1.0, blink=False):
    """Mandel mit Punktpupille -- kein Augapfel-Oval.

    `blink` ersetzt Mandel, Pupille und Lid durch einen einzelnen
    geschlossenen Bogen -- fuer die Blinzelbilder."""
    r = r * gross
    if blink:
        p.stroke([(x - r, y + tilt * 0.3), (x - r * 0.15, y + tilt * 0.3 + 2.0),
                  (x + r, y + tilt * 0.3)], w=(0, 1.6, 0), amp=0.5)
        return
    p.stroke([(x - r, y + tilt), (x - r * 0.3, y - r * 0.62),
              (x + r * 0.45, y - r * 0.5), (x + r, y - tilt * 0.5)],
             w=(0, 2.0, 0), amp=0.4)
    p.stroke([(x - r * 0.8, y + tilt + 1), (x, y + r * 0.5), (x + r * 0.85, y + 1)],
             w=(0, 1.5, 0), amp=0.4)
    p.dot(x + r * 0.05 + pupil_dx, y - r * 0.08 + pupil_dy, 2.5)
    if lid:
        p.stroke([(x - r * 1.1, y - r * 0.9), (x, y - r * 1.35), (x + r * 0.9, y - r * 1.0)],
                 w=(0, 1.3, 0), amp=0.4)


def nase(p, x, y0, y1, w=8):
    """Hakenstrich mit Nasenfluegel auf der abgewandten Seite.

    Der Haken muss auf die Seite zeigen, zu der sich das Gesicht wendet --
    bei nach rechts gedrehtem Kopf also gespiegelt. Von Emotes unberuehrt."""
    s = -1 if p.turn > 0.05 else 1
    p.stroke([(x + 2 * s, y0), (x - 2 * s, y0 + (y1 - y0) * 0.55), (x - w * s, y1),
              (x - w * 0.2 * s, y1 + 5), (x + 3 * s, y1 + 3)],
             w=(0, 2.4, 0), amp=0.6)


def hals_schultern(p, schulter_l=None, schulter_r=None):
    kopf = p.turn
    # Hals folgt dem Kopf zum Teil, der Rumpf dreht kaum mit
    p.set_turn(kopf * 0.6, R=80.0)
    p.stroke([(177, 348), (174, 374), (177, 398)], w=(0, 2.8, 0), amp=0.8)
    p.stroke([(224, 344), (228, 372), (227, 396)], w=(0, 2.6, 0), amp=0.8)
    # Schatten unter dem Kinn -- die dunkelste Stelle des Gesichts
    p.stroke([(176, 352), (200, 370), (224, 351)], w=(2.5, 11.0, 2.0), amp=0.9)
    p.hatch(184, 372, 4, 13, 1.35, 9, w=(0, 1.7, 0))
    p.set_turn(kopf * 0.25, R=115.0)
    sl = schulter_l or [(150, 402), (103, 425), (66, 467), (52, 520)]
    sr = schulter_r or [(253, 399), (299, 423), (335, 465), (349, 520)]
    kontur(p, sl, w=FINE, amp=1.8, cuts=[(0.0, 0.62), (0.70, 1.0)],
           druck=[(0.16, 0.50)], druck_w=5.5)
    kontur(p, sr, w=FINE, amp=1.8, cuts=[(0.0, 0.55), (0.63, 1.0)],
           druck=[(0.62, 0.94)], druck_w=5.0)
    p.set_turn(kopf * 0.25, R=115.0)


# ------------------------------------------------------- Gesicht aus Daten
#
# Die Gesichtsgeometrie (Augen, Brauen, Nase, Mund) steht hier als
# Dictionary je Figur. Ein Emote moduliert diese Geometrie ueber die Zeilen
# aus game/data/emotes.csv -- siehe braue(), augen() und mundzug() unten.
# Jede Brauen-Stuetzpunktliste laeuft bei allen sechs Figuren gleich:
# die linke Braue von aussen (Schlaefe) nach innen (Nasenwurzel), die
# rechte von innen nach aussen -- daher aussen_erst=True/False.

GEO = {
    "michael": {
        "auge_l": dict(x=165, y=221, r=7.8, tilt=1.0),
        "auge_r": dict(x=235, y=216, r=7.0, tilt=-0.5),
        "braue_l": dict(pts=[(143, 197), (166, 187), (187, 193)],
                         w=(1.8, 6.0, 0), amp=0.7, aussen_erst=True),
        "braue_r": dict(pts=[(213, 190), (235, 184), (256, 195)],
                         w=(0, 6.4, 1.8), amp=0.7, aussen_erst=False),
        "nase": dict(x=200, y0=227, y1=274, w=10),
        "mund": dict(x0=178, y0=309, x1=221, y1=305, bow=4),
    },
    "sarah": {
        "auge_l": dict(x=170, y=224, r=7.6, tilt=0.8),
        "auge_r": dict(x=234, y=220, r=7.2, tilt=-0.4),
        "braue_l": dict(pts=[(150, 200), (172, 193), (190, 199)],
                         w=(1.5, 4.6, 0), amp=0.6, aussen_erst=True),
        "braue_r": dict(pts=[(212, 197), (232, 191), (252, 199)],
                         w=(0, 4.8, 1.5), amp=0.6, aussen_erst=False),
        "nase": dict(x=202, y0=230, y1=274, w=8),
        "mund": dict(x0=181, y0=310, x1=222, y1=306, bow=3),
    },
    "jamal": {
        "auge_l": dict(x=167, y=226, r=7.6, tilt=0.9),
        "auge_r": dict(x=235, y=222, r=7.2, tilt=-0.4),
        "braue_l": dict(pts=[(146, 202), (169, 194), (188, 200)],
                         w=(1.6, 5.2, 0), amp=0.6, aussen_erst=True),
        "braue_r": dict(pts=[(212, 198), (233, 192), (254, 201)],
                         w=(0, 5.4, 1.6), amp=0.6, aussen_erst=False),
        "nase": dict(x=201, y0=232, y1=276, w=9),
        "mund": dict(x0=180, y0=312, x1=221, y1=308, bow=2),
    },
    "kat": {
        "auge_l": dict(x=169, y=224, r=8.2, tilt=0.8),
        "auge_r": dict(x=234, y=220, r=7.8, tilt=-0.4),
        "braue_l": dict(pts=[(148, 200), (170, 192), (189, 198)],
                         w=(1.4, 4.4, 0), amp=0.6, aussen_erst=True),
        "braue_r": dict(pts=[(212, 196), (233, 190), (253, 199)],
                         w=(0, 4.6, 1.4), amp=0.6, aussen_erst=False),
        "nase": dict(x=201, y0=230, y1=272, w=8),
        "mund": dict(x0=176, y0=302, x1=226, y1=300, bow=15),
    },
    "lena": {
        "auge_l": dict(x=171, y=226, r=7.4, tilt=1.0),
        "auge_r": dict(x=233, y=219, r=7.0, tilt=-0.6),
        "braue_l": dict(pts=[(152, 202), (173, 195), (191, 200)],
                         w=(1.4, 4.4, 0), amp=0.6, aussen_erst=True),
        "braue_r": dict(pts=[(211, 191), (232, 183), (251, 192)],
                         w=(0, 4.8, 1.4), amp=0.6, aussen_erst=False),
        "nase": dict(x=202, y0=232, y1=274, w=8),
        "mund": dict(x0=180, y0=310, x1=224, y1=305, bow=5.5),
    },
    "tom": {
        "auge_l": dict(x=170, y=230, r=8.4, tilt=0.8),
        "auge_r": dict(x=234, y=226, r=8.0, tilt=-0.4),
        "braue_l": dict(pts=[(150, 206), (172, 197), (190, 203)],
                         w=(1.4, 4.2, 0), amp=0.6, aussen_erst=True),
        "braue_r": dict(pts=[(212, 201), (233, 195), (252, 204)],
                         w=(0, 4.4, 1.4), amp=0.6, aussen_erst=False),
        "nase": dict(x=201, y0=236, y1=274, w=7),
        "mund": dict(x0=172, y0=300, x1=228, y1=298, bow=21),
    },
}


def braue(p, spec, row):
    """Ein Brauenstrich, an den Enden je nach Emote verschoben.

    Das innere Ende (nahe der Nase) wandert um `braue_innen`, das aeussere
    (zur Schlaefe hin) um `braue_aussen`, die Punkte dazwischen linear
    interpoliert -- der urspruengliche Keilstrich bleibt dabei erhalten,
    nur seine Neigung aendert sich."""
    pts = spec["pts"]
    n = len(pts)
    aussen_erst = spec.get("aussen_erst", True)
    neu = []
    for i, (x, y) in enumerate(pts):
        t = i / (n - 1)
        s0 = row["braue_aussen"] if aussen_erst else row["braue_innen"]
        s1 = row["braue_innen"] if aussen_erst else row["braue_aussen"]
        neu.append((x, y + s0 * (1 - t) + s1 * t))
    p.stroke(neu, w=spec["w"], amp=spec.get("amp", 0.6))


def brauen(p, geo, row):
    braue(p, geo["braue_l"], row)
    braue(p, geo["braue_r"], row)


def augen(p, geo, row, blink=False):
    for spec in (geo["auge_l"], geo["auge_r"]):
        auge(p, spec["x"], spec["y"], spec["r"], tilt=spec.get("tilt", 0.0),
             lid=bool(row["lid"]), pupil_dx=row["pupille_x"], pupil_dy=row["pupille_y"],
             gross=row["augen_gross"], blink=blink)


def wirksamer_bogen(spec, row):
    """Mundbogen aus figureneigener Grundkruemmung und Emote-Abweichung.

    Ohne die Grundkruemmung waeren alle sechs Figuren im neutralen Ausdruck
    gleich, und Kat, Lena und Tom haetten ihren Gesichtsausdruck verloren.
    Wie stark sie in ein Emote hineinwirkt, steht als "bogen_daempfung" in
    der Emote-Tabelle: ausdrucksstarke Emotes wie "ent" verdraengen sie fast
    ganz (sonst grinst Tom auch entschlossen noch), weiche wie "freude"
    behalten sie."""
    neutral_bow = EMOTES["neutral"]["bow"]
    basis = spec.get("bow", neutral_bow)
    if row.get("emote") == "neutral":
        return basis
    return row["bow"] + row["bogen_daempfung"] * (basis - neutral_bow)


def mundzug(p, geo, row):
    """Mund aus Eckpunkten plus Emote-Bogen.

    `mund_offen` ersetzt den Strich durch eine kleine, unregelmaessige
    Mundoeffnung -- fuer Sprechbilder und den Schock-Ausdruck."""
    spec = geo["mund"]
    x0, y0, x1, y1 = spec["x0"], spec["y0"], spec["x1"], spec["y1"]
    bow = wirksamer_bogen(spec, row)
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2 + bow
    if row["mund_offen"]:
        p.stroke([(x0, y0), (mx, my - 4.5), (x1, y1)], w=(0, 2.0, 0), amp=0.5)
        p.patch([(x0 + 4, y0 + 1), (mx, my + 6), (x1 - 4, y1 + 1), (mx, my - 3)], wob=1.3)
    else:
        p.stroke([(x0, y0), (mx, my), (x1, y1)], w=(0, 2.2, 0), amp=0.5)
    p.dot(x0, y0, 1.9)
    p.dot(x1, y1, 1.9)


def michael(p, turn=0.0, row=None, blink=False):
    row = row or EMOTES["neutral"]
    p.set_turn(turn)
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

    ohren(p, (130, 220), (270, 214), 1.05)

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

    geo = GEO["michael"]
    brauen(p, geo, row)
    augen(p, geo, row, blink=blink)

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

    nase(p, **geo["nase"])

    # --- Schnauzbart: von der Mitte nach aussen gestrichen
    p.hairs([(196, 283), (184, 285), (172, 290)], 20, 15,
            w=(3.4, 1.7, 0), spread=0.34, curl=0.3, angle=2.95,
            curl_bias=0.8, length_var=0.5)
    p.hairs([(200, 283), (212, 285), (225, 290)], 20, 15,
            w=(3.4, 1.7, 0), spread=0.34, curl=0.3, angle=0.22,
            curl_bias=-0.8, length_var=0.5)
    p.blob(198, 288, 5.0, 0.45, 9, spikes=2, spike_len=1.6)

    mundzug(p, geo, row)

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
               (206, 486, 120, 7), (200, 66, 108, 5)], rng_seed=p.seed)


def sarah(p, turn=0.0, row=None, blink=False):
    """Dunkles, glattes Haar bis auf die Schultern, muede und entschlossen."""
    row = row or EMOTES["neutral"]
    p.set_turn(turn)
    kontur(p, [(141, 176), (138, 232), (147, 288), (163, 328), (182, 353), (203, 363)],
           w=(0, 3.2, 0), amp=1.6, cuts=[(0.0, 0.58), (0.65, 1.0)],
           druck=[(0.44, 0.88)], druck_w=5.6)
    kontur(p, [(200, 364), (226, 351), (243, 322), (255, 280), (262, 232), (261, 176)],
           w=(0, 3.0, 0), amp=1.6, cuts=[(0.0, 0.74), (0.81, 1.0)],
           druck=[(0.08, 0.40)], druck_w=5.0)

    # --- Haar: durchgehende Einzelstraehnen vom Scheitel bis auf die Schulter
    # Beide Leitkurven beginnen im selben Scheitelpunkt -- setzt die innere
    # tiefer an als die aeussere, klafft am Oberkopf eine V-Kerbe
    p.strands([(200, 88), (176, 114), (158, 168), (152, 248), (152, 330),
               (151, 404)],
              [(196, 90), (150, 108), (122, 176), (110, 258), (114, 338),
               (126, 410)],
              28, w=(1.7, 2.6, 0), off=2.0, kurz=0.12, spaet=0.01)
    p.strands([(200, 88), (224, 114), (243, 168), (249, 248), (249, 330),
               (250, 404)],
              [(204, 90), (250, 108), (279, 176), (291, 258), (287, 338),
               (275, 410)],
              28, w=(1.7, 2.6, 0), off=2.0, kurz=0.12, spaet=0.01)
    # Scheitel: schmale Trennung, von dort deckt das Haar den ganzen
    # Schaedel bis zum Ansatz -- sonst wirkt der Oberkopf kahl
    p.strands([(200, 89), (170, 95), (147, 119), (139, 154)],
              [(200, 101), (184, 120), (170, 140), (162, 156)],
              20, w=(1.5, 2.2, 0), off=1.9, kurz=0.16, spaet=0.02)
    p.strands([(200, 89), (230, 95), (253, 119), (261, 154)],
              [(200, 101), (216, 120), (230, 140), (238, 156)],
              20, w=(1.5, 2.2, 0), off=1.9, kurz=0.16, spaet=0.02)

    # Pony nach demselben Prinzip wie bei Lena -- haengende Buendel, Neigung
    # nach aussen zunehmend. Bei ihr aber als Curtain Bangs: in der Mitte
    # offen, sodass der Scheitel auf der Stirn weiterlaeuft, und nach aussen
    # deutlich laenger. Das haelt sie von Lenas vollem Pony unterscheidbar.
    for basis, winkel, zahl, laenge in (
            ([(158, 130), (174, 119)], 1.78, 10, 92),
            ([(176, 116), (190, 107)], 1.70, 10, 70),
            ([(210, 107), (224, 116)], 1.44, 10, 70),
            ([(226, 119), (242, 130)], 1.36, 10, 92)):
        p.hairs(basis, zahl, laenge, w=(1.5, 1.7, 0), spread=0.15,
                curl=0.20, angle=winkel, curl_bias=0.0, curl_var=0.9,
                length_var=0.24, jitter=2.2)

    ohren(p, (137, 224), (265, 220), 0.9)

    geo = GEO["sarah"]
    brauen(p, geo, row)
    augen(p, geo, row, blink=blink)
    # Muede Schatten unter den Augen
    p.stroke([(159, 238), (172, 243), (184, 239)], w=(0, 1.6, 0), amp=0.5)
    p.stroke([(220, 235), (233, 240), (245, 236)], w=(0, 1.5, 0), amp=0.5)

    nase(p, **geo["nase"])
    mundzug(p, geo, row)
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
               (206, 488, 118, 7), (200, 70, 100, 5)], rng_seed=p.seed)


def jamal(p, turn=0.0, row=None, blink=False):
    """Kurzes Haar, graue Schlaefen, Dreitagebart, Kapuzenpulli."""
    row = row or EMOTES["neutral"]
    p.set_turn(turn)
    kontur(p, [(136, 184), (133, 238), (142, 292), (159, 330), (181, 354), (203, 363)],
           w=(0, 3.2, 0), amp=1.6, cuts=[(0.0, 0.57), (0.64, 1.0)],
           druck=[(0.44, 0.88)], druck_w=5.8)
    kontur(p, [(200, 364), (227, 350), (246, 320), (258, 277), (265, 231), (264, 184)],
           w=(0, 3.0, 0), amp=1.6, cuts=[(0.0, 0.73), (0.80, 1.0)],
           druck=[(0.08, 0.42)], druck_w=5.2)

    # --- Kurzhaarschnitt: kurze Einzelzuege, flach anliegend
    # Kappe laeuft ohne Absatz von Schlaefe zu Schlaefe ueber den Scheitel --
    # getrennte Seitenstuecke wirken sonst wie angeklebte Koteletten
    # kurz und spaet gleich gross halten: die Leitkurven laufen von links
    # nach rechts, ein groesseres kurz frisst sonst allein die rechte Seite
    p.strands([(148, 180), (154, 148), (188, 132), (222, 134), (252, 150),
               (258, 182)],
              [(135, 178), (139, 138), (180, 92), (226, 94), (266, 140),
               (265, 180)],
              56, w=(1.7, 2.4, 0), off=2.0, kurz=0.04, spaet=0.04)
    # Graue Schlaefen: duenne, lichte Striche am Rand der Kappe
    p.hairs([(141, 172), (139, 150), (149, 132)], 8, 11, w=(1.6, 0.9, 0),
            spread=0.24, curl=0.3, angle=2.55, length_var=0.5)
    p.hairs([(255, 168), (257, 146), (248, 128)], 7, 10, w=(1.6, 0.9, 0),
            spread=0.24, curl=0.3, angle=0.60, length_var=0.5)

    ohren(p, (132, 222), (268, 218), 1.0)

    geo = GEO["jamal"]
    brauen(p, geo, row)
    augen(p, geo, row, blink=blink)

    nase(p, **geo["nase"])
    mundzug(p, geo, row)

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
               (206, 488, 116, 7), (200, 70, 100, 5)], rng_seed=p.seed)


def kat(p, turn=0.0, row=None, blink=False):
    """Kurzer, zerzauster Schnitt mit Undercut, Sommersprossen, warm."""
    row = row or EMOTES["neutral"]
    p.set_turn(turn)
    kontur(p, [(140, 182), (137, 234), (147, 288), (164, 326), (183, 350), (203, 359)],
           w=(0, 3.2, 0), amp=1.6, cuts=[(0.0, 0.57), (0.64, 1.0)],
           druck=[(0.42, 0.86)], druck_w=5.6)
    kontur(p, [(200, 360), (226, 347), (244, 318), (256, 276), (262, 230), (261, 182)],
           w=(0, 3.0, 0), amp=1.6, cuts=[(0.0, 0.72), (0.79, 1.0)],
           druck=[(0.08, 0.40)], druck_w=5.0)

    # --- Zerzaust: Masse am Scheitel, kurze Seiten, Spitzen nach aussen
    # Kappe in einem Zug von Schlaefe zu Schlaefe, ohne abgesetzte Seitenteile
    p.strands([(150, 208), (147, 168), (158, 140), (190, 128), (222, 130),
               (252, 146), (256, 172), (252, 208)],
              [(133, 210), (131, 162), (140, 124), (180, 94), (226, 96),
               (266, 128), (270, 166), (269, 210)],
              58, w=(1.8, 2.5, 0), off=2.4, kurz=0.04, spaet=0.04, amp=1.0)
    # Zerzaust: kurze Straehnen legen sich schraeg ueber die Kappe,
    # statt senkrecht davon abzustehen
    p.hairs([(142, 126), (176, 96), (222, 94), (262, 128)], 26, 9,
            w=(2.4, 1.3, 0), spread=0.34, curl=0.5, out_dir=-1,
            curl_bias=0.9, curl_var=0.4, length_var=0.5)
    # Kurz geschorene Seiten: ausgefranste Kante ueber den Ohren
    p.hairs([(137, 190), (136, 214), (143, 236)], 18, 9, w=(2.4, 1.3, 0),
            spread=0.4, curl=0.3, angle=2.75, length_var=0.55)
    p.hairs([(259, 194), (260, 216), (254, 236)], 18, 9, w=(2.4, 1.3, 0),
            spread=0.4, curl=0.3, angle=0.40, length_var=0.55)

    ohren(p, (136, 220), (265, 216), 0.95)

    geo = GEO["kat"]
    brauen(p, geo, row)
    augen(p, geo, row, blink=blink)

    nase(p, **geo["nase"])
    mundzug(p, geo, row)
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
               (206, 488, 116, 7), (200, 66, 104, 5)], rng_seed=p.seed)


def lena(p, turn=0.0, row=None, blink=False):
    """Scharfer Bob mit geradem Pony, wacher und skeptischer Blick."""
    row = row or EMOTES["neutral"]
    p.set_turn(turn)
    kontur(p, [(144, 186), (141, 238), (150, 290), (166, 326), (184, 350), (203, 359)],
           w=(0, 3.2, 0), amp=1.6, cuts=[(0.0, 0.56), (0.63, 1.0)],
           druck=[(0.44, 0.86)], druck_w=5.6)
    kontur(p, [(200, 360), (225, 347), (242, 318), (253, 276), (259, 232), (258, 186)],
           w=(0, 3.0, 0), amp=1.6, cuts=[(0.0, 0.72), (0.79, 1.0)],
           druck=[(0.08, 0.40)], druck_w=5.0)

    # --- Bob: Einzelstraehnen, kinnlang, mit kurzem Pony
    # Ansaetze stossen am Scheitel dicht zusammen und werden oben kaum
    # beschnitten (kleines spaet) -- sonst klafft dort eine weisse Luecke
    # Beide Leitkurven beginnen im selben Scheitelpunkt -- setzt die innere
    # tiefer an als die aeussere, klafft am Oberkopf eine V-Kerbe
    p.strands([(200, 88), (172, 110), (156, 158), (152, 232), (156, 300),
               (162, 348)],
              [(197, 90), (150, 106), (126, 168), (120, 244), (128, 308),
               (144, 354)],
              30, w=(1.7, 2.6, 0), off=1.8, kurz=0.09, spaet=0.01)
    p.strands([(200, 88), (228, 110), (245, 158), (249, 232), (245, 300),
               (239, 348)],
              [(203, 90), (250, 106), (275, 168), (281, 244), (273, 308),
               (257, 354)],
              30, w=(1.7, 2.6, 0), off=1.8, kurz=0.09, spaet=0.01)
    # Kronenpartie: die Seitenpartien fallen vom Scheitel steil nach aussen
    # ab und der Pony setzt erst tiefer an -- ohne diese Baender bliebe der
    # Oberkopf dazwischen unbedeckt
    p.strands([(200, 87), (172, 94), (150, 110), (140, 136)],
              [(200, 99), (180, 112), (164, 130), (154, 152)],
              22, w=(1.5, 2.2, 0), off=1.9, kurz=0.16, spaet=0.02)
    p.strands([(200, 87), (228, 94), (250, 110), (260, 136)],
              [(200, 99), (220, 112), (236, 130), (246, 152)],
              22, w=(1.5, 2.2, 0), off=1.9, kurz=0.16, spaet=0.02)
    # Pony: fuenf Buendel ueber die Stirnbreite. Jedes haengt nach unten, die
    # Neigung nimmt nach aussen zu -- Haar faellt der Schwerkraft nach,
    # statt sternfoermig vom Scheitel wegzustrahlen. Aussen laenger als in
    # der Mitte, damit der Pony ohne Kante in die Seitenpartien uebergeht.
    for basis, winkel, zahl in (
            ([(160, 126), (176, 116)], 1.72, 12),
            ([(178, 114), (192, 106)], 1.64, 12),
            ([(194, 103), (212, 103)], 1.57, 14),
            ([(214, 106), (228, 114)], 1.50, 12),
            ([(230, 116), (246, 126)], 1.42, 12)):
        p.hairs(basis, zahl, 75, w=(1.5, 1.7, 0), spread=0.15,
                curl=0.20, angle=winkel, curl_bias=0.0, curl_var=0.9,
                length_var=0.26, jitter=2.2)

    geo = GEO["lena"]
    brauen(p, geo, row)
    augen(p, geo, row, blink=blink)

    nase(p, **geo["nase"])
    mundzug(p, geo, row)
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
               (206, 488, 116, 7), (200, 66, 102, 5)], rng_seed=p.seed)


def tom(p, turn=0.0, row=None, blink=False):
    """Wilde Locken, jung, energisch -- offenes Grinsen."""
    row = row or EMOTES["neutral"]
    p.set_turn(turn)
    kontur(p, [(142, 190), (139, 240), (149, 290), (166, 324), (184, 346), (203, 355)],
           w=(0, 3.2, 0), amp=1.6, cuts=[(0.0, 0.56), (0.63, 1.0)],
           druck=[(0.42, 0.86)], druck_w=5.4)
    kontur(p, [(200, 356), (224, 344), (241, 316), (252, 274), (258, 232), (257, 190)],
           w=(0, 3.0, 0), amp=1.6, cuts=[(0.0, 0.72), (0.79, 1.0)],
           druck=[(0.08, 0.40)], druck_w=4.8)

    # --- Lockenkopf: offene Spiralzuege statt voller Kleckse
    p.curls([(140, 200), (134, 152), (158, 110), (196, 92), (238, 100),
             (262, 140), (262, 196)], 26, 9.5, size_var=0.38, jitter=4.5,
            w=(2.4, 1.9, 0))
    p.curls([(152, 160), (176, 126), (212, 118), (246, 148)], 13, 8.0,
            size_var=0.4, jitter=5.5, w=(2.2, 1.7, 0))
    p.curls([(182, 102), (218, 104)], 5, 7.5, size_var=0.38, jitter=5.0,
            w=(2.2, 1.7, 0))
    p.hairs([(150, 124), (182, 100), (220, 100), (252, 126)], 18, 13,
            w=(2.4, 1.3, 0), spread=0.6, curl=0.6, out_dir=-1,
            curl_bias=0.3, curl_var=0.9, length_var=0.6)

    ohren(p, (138, 226), (262, 222), 0.95)

    geo = GEO["tom"]
    brauen(p, geo, row)
    augen(p, geo, row, blink=blink)

    nase(p, **geo["nase"])
    mundzug(p, geo, row)
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
               (206, 490, 116, 7), (200, 62, 106, 5)], rng_seed=p.seed)


FIGUREN = {
    "sarah-hoffmann": (sarah, 11),
    "jamal-al-rashid": (jamal, 23),
    "michael-weber": (michael, 4),
    "katharina-mueller": (kat, 37),
    "lena-kowalski": (lena, 52),
    "tom-schneider": (tom, 68),
}

# Langer Figurenname -> kurzer Puppenname (Ordner unter doc/img/emotes/ und
# game/data/art/figuren/).
PUPPEN = {
    "sarah-hoffmann": "sarah",
    "jamal-al-rashid": "jamal",
    "michael-weber": "michael",
    "katharina-mueller": "kat",
    "lena-kowalski": "lena",
    "tom-schneider": "tom",
}


# Blickwinkel fuer Dialoge. Positiver Wert dreht die Nase nach rechts --
# von links vorne gesehen wendet sich das Gesicht also nach rechts.
# Jede Ansicht bekommt einen eigenen Zufallsstartwert, damit sie wie neu
# gezeichnet wirkt und nicht wie eine verschobene Kopie.
ANSICHTEN = [("", 0.0, 0), ("-von-links", 0.30, 101), ("-von-rechts", -0.30, 202)]

# Reihenfolge der sechs Emotes -- bestimmt auch die Reihenfolge im Manifest.
EMOTE_NAMEN = ["neutral", "denk", "sorge", "ent", "freude", "schock"]
# Fuer diese beiden Emotes wird zusaetzlich ein Blinzelbild erzeugt --
# sie sind laut Plan die, in denen Figuren am laengsten stehen.
BLINK_EMOTES = ["neutral", "ent"]


def lade_emotes():
    """Liest die Emote-Tabelle aus game/data/emotes.csv.

    Das ist der einzige Ort, an dem Mundbogen, Brauenneigung, Lidstellung,
    Pupillenversatz und Augengroesse je Emote festgelegt werden -- siehe
    plans/graphic-novel-plan.md, Abschnitt 4 und 7."""
    zeilen = {}
    with open(EMOTES_CSV, newline="", encoding="utf-8") as fh:
        for zeile in csv.DictReader(fh):
            zeilen[zeile["emote"]] = {
                "emote": zeile["emote"],
                "bow": float(zeile["bow"]),
                "braue_innen": float(zeile["braue_innen"]),
                "braue_aussen": float(zeile["braue_aussen"]),
                "lid": int(zeile["lid"]),
                "pupille_x": float(zeile["pupille_x"]),
                "pupille_y": float(zeile["pupille_y"]),
                "mund_offen": int(zeile["mund_offen"]),
                "augen_gross": float(zeile["augen_gross"]),
                "bogen_daempfung": float(zeile["bogen_daempfung"]),
            }
    return zeilen


EMOTES = lade_emotes()


def schreibe_svg(p, pfad):
    with open(pfad, "w") as fh:
        fh.write(p.svg(W, H))
    return len(p.paths)


def zeichne_ansichten(name, fn, seed):
    """Die drei bestehenden Blickrichtungen -- unveraendert im Verhalten."""
    for suffix, turn, versatz in ANSICHTEN:
        p = Pen(seed + versatz)
        fn(p, turn)
        pfad = os.path.normpath(os.path.join(OUT, name + suffix + ".svg"))
        n = schreibe_svg(p, pfad)
        print("geschrieben:", os.path.basename(pfad), f"({n} Pfade)")


def zeichne_emotes(name, fn, seed, kurz):
    """Alle 14 Emote-Canvases einer Figur, alle mit demselben Zufallsstartwert.

    Nur das Gesicht (Brauen, Augen, Mund) unterscheidet sich zwischen den
    Dateien -- Haare und Silhouette werden vor dem Gesicht gezeichnet und
    verbrauchen den Zufallsstrom deshalb identisch, unabhaengig vom Emote."""
    zielverzeichnis = os.path.join(EMOTE_OUT, kurz)
    os.makedirs(zielverzeichnis, exist_ok=True)
    manifest_zeilen = []

    for emote in EMOTE_NAMEN:
        row = EMOTES[emote]

        p = Pen(seed)
        fn(p, 0.0, row=row, blink=False)
        pfad = os.path.join(zielverzeichnis, f"{emote}.svg")
        n = schreibe_svg(p, pfad)
        print("geschrieben:", os.path.relpath(pfad, ROOT), f"({n} Pfade)")
        manifest_zeilen.append(
            (os.path.relpath(pfad, ROOT).replace(os.sep, "/"),
             f"figuren/{kurz}/{emote}.gif", "480", "624", "1"))

        offen_row = dict(row)
        offen_row["mund_offen"] = 1
        p = Pen(seed)
        fn(p, 0.0, row=offen_row, blink=False)
        pfad = os.path.join(zielverzeichnis, f"{emote}_open.svg")
        n = schreibe_svg(p, pfad)
        print("geschrieben:", os.path.relpath(pfad, ROOT), f"({n} Pfade)")
        manifest_zeilen.append(
            (os.path.relpath(pfad, ROOT).replace(os.sep, "/"),
             f"figuren/{kurz}/{emote}_open.gif", "480", "624", "1"))

    for emote in BLINK_EMOTES:
        row = EMOTES[emote]
        p = Pen(seed)
        fn(p, 0.0, row=row, blink=True)
        pfad = os.path.join(zielverzeichnis, f"{emote}_blink.svg")
        n = schreibe_svg(p, pfad)
        print("geschrieben:", os.path.relpath(pfad, ROOT), f"({n} Pfade)")
        manifest_zeilen.append(
            (os.path.relpath(pfad, ROOT).replace(os.sep, "/"),
             f"figuren/{kurz}/{emote}_blink.gif", "480", "624", "1"))

    return manifest_zeilen


def schreibe_manifest(neue_zeilen, bearbeitete_kurznamen):
    """Schreibt game/data/art.csv neu.

    Zeilen, die nicht mit doc/img/emotes/ beginnen, bleiben unangetastet
    (spaetere Hintergruende und aehnliches). Von den Emote-Zeilen werden nur
    die der gerade bearbeiteten Figuren ersetzt -- ein Aufruf mit nur einem
    Figurennamen darf die Zeilen der anderen Figuren nicht loeschen."""
    behalten = []
    if os.path.isfile(MANIFEST):
        with open(MANIFEST, newline="", encoding="utf-8") as fh:
            leser = csv.reader(fh)
            next(leser, None)
            for zeile in leser:
                if not zeile:
                    continue
                pfad = zeile[0]
                if not pfad.startswith("doc/img/emotes/"):
                    behalten.append(zeile)
                    continue
                betroffen = any(pfad.startswith(f"doc/img/emotes/{k}/")
                                 for k in bearbeitete_kurznamen)
                if not betroffen:
                    behalten.append(zeile)

    with open(MANIFEST, "w", newline="", encoding="utf-8") as fh:
        schreiber = csv.writer(fh)
        schreiber.writerow(["svg", "gif", "breite", "hoehe", "transparent"])
        for zeile in behalten:
            schreiber.writerow(zeile)
        for zeile in neue_zeilen:
            schreiber.writerow(zeile)

    print(f"Manifest geschrieben: {os.path.relpath(MANIFEST, ROOT)} "
          f"({len(behalten) + len(neue_zeilen)} Zeilen)")


def main(argv):
    names = argv or list(FIGUREN)
    alle_manifest_zeilen = []
    for name in names:
        fn, seed = FIGUREN[name]
        kurz = PUPPEN[name]
        zeichne_ansichten(name, fn, seed)
        alle_manifest_zeilen += zeichne_emotes(name, fn, seed, kurz)

    bearbeitete_kurznamen = [PUPPEN[n] for n in names]
    schreibe_manifest(alle_manifest_zeilen, bearbeitete_kurznamen)


if __name__ == "__main__":
    main(sys.argv[1:])
