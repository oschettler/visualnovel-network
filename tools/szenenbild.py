#!/usr/bin/env python3
"""Setzt eine Beispielszene aus Hintergrund und Puppen zusammen.

Die Puppen sind transparente Strichgrafik, der Hintergrund scheint also
durch sie hindurch. Genau deshalb gibt es dieses Werkzeug: wie eine Szene
wirklich aussieht, laesst sich nur am zusammengesetzten Bild beurteilen,
nicht an den Einzeldateien.

Aufruf (von der Repo-Wurzel):
  python3 tools/szenenbild.py sarah-buero sarah:ent:links michael:sorge:rechts
  python3 tools/szenenbild.py --ziel doc/img/szenen/probe.png konferenzraum tom:freude:mitte
"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "game", "data", "art")
BREITE, HOEHE = 1024, 684
PUPPE_B, PUPPE_H = 480, 624

# Bildmitte der drei Buehnenspalten, wie Puppeteer sie berechnet.
SPALTEN = {
    "links": 0,
    "mitte": (BREITE - PUPPE_B) // 2,
    "rechts": BREITE - PUPPE_B,
}
# Blickrichtung folgt der Spalte, genau wie in der Engine.
RICHTUNG = {"links": "_r", "mitte": "", "rechts": "_l"}


def puppenpfad(figur, emote, spalte):
    ordner = figur + RICHTUNG[spalte]
    return os.path.join(ART, "figuren", ordner, f"{emote}.gif")


def bauen(hintergrund, puppen, ziel):
    hg = os.path.join(ART, "hintergruende", f"{hintergrund}.gif")
    if not os.path.exists(hg):
        print(f"Hintergrund fehlt: {hg}")
        return False

    befehl = ["magick", hg]
    for figur, emote, spalte in puppen:
        p = puppenpfad(figur, emote, spalte)
        if not os.path.exists(p):
            print(f"Puppe fehlt: {p}")
            return False
        x = SPALTEN[spalte]
        y = (HOEHE - PUPPE_H) // 2
        # Die Puppen-GIFs tragen ihre Transparenz bereits (siehe
        # silhouette() in tools/render_art.py). Weiss hier nochmals
        # transparent zu schalten wuerde genau die deckende Flaeche
        # zerstoeren, die die Figur vom Hintergrund trennt.
        befehl += [p, "-geometry", f"+{x}+{y}", "-composite"]
    befehl.append(ziel)
    subprocess.run(befehl, check=True)
    print("geschrieben:", os.path.relpath(ziel, ROOT))
    return True


def main(argv):
    ziel = os.path.join(ROOT, "doc", "img", "szenen", "probe.png")
    if argv and argv[0] == "--ziel":
        ziel = os.path.join(ROOT, argv[1])
        argv = argv[2:]
    if not argv:
        print(__doc__)
        return 1
    hintergrund = argv[0]
    puppen = []
    for teil in argv[1:]:
        figur, emote, spalte = teil.split(":")
        puppen.append((figur, emote, spalte))
    os.makedirs(os.path.dirname(ziel), exist_ok=True)
    return 0 if bauen(hintergrund, puppen, ziel) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
