"""Rendert die Strichgrafiken aus game/data/art.csv zu .gif.

Grund: Decker/lilt kann nur .gif lesen, keine .png/.svg (siehe
plans/graphic-novel-plan.md, Abschnitt 2, Befund 5). Dieses Werkzeug fuehrt
die dort verifizierte Kette rsvg-convert -> magick fuer jede Zeile des
Manifests aus.

Aufruf:
  python3 tools/render_art.py                 # alle Zeilen des Manifests
  python3 tools/render_art.py figuren/sarah    # nur Zeilen mit diesem gif-Praefix
  python3 tools/render_art.py --pruefen        # zusaetzlich das Pixel-Histogramm pruefen
"""

import csv
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
MANIFEST = os.path.join(ROOT, "game", "data", "art.csv")
ART_DIR = os.path.join(ROOT, "game", "data", "art")


def lies_manifest(praefix=None):
    """Liest art.csv und liefert die Zeilen, optional gefiltert nach gif-Praefix."""
    if not os.path.isfile(MANIFEST):
        sys.exit(f"Fehler: Manifest nicht gefunden: {MANIFEST}")
    zeilen = []
    with open(MANIFEST, newline="", encoding="utf-8") as fh:
        for zeile in csv.DictReader(fh):
            if praefix and not zeile["gif"].startswith(praefix):
                continue
            zeilen.append(zeile)
    return zeilen


def pruefe_werkzeuge():
    """Bricht fruehzeitig mit klarer Meldung ab, wenn ein Kommandozeilenwerkzeug fehlt."""
    for werkzeug in ("rsvg-convert", "magick"):
        if shutil.which(werkzeug) is None:
            sys.exit(f"Fehler: Werkzeug '{werkzeug}' nicht gefunden. Bitte installieren.")


def rendere_zeile(zeile, tempdir):
    """Wandelt eine Manifest-Zeile in eine .gif-Datei um. Bricht bei Fehlern ab."""
    svg_pfad = os.path.normpath(os.path.join(ROOT, zeile["svg"]))
    gif_pfad = os.path.normpath(os.path.join(ART_DIR, zeile["gif"]))
    breite = zeile["breite"]
    hoehe = zeile["hoehe"]
    transparent = zeile["transparent"].strip() == "1"

    if not os.path.isfile(svg_pfad):
        sys.exit(f"Fehler: Quelldatei fehlt: {svg_pfad}")

    os.makedirs(os.path.dirname(gif_pfad), exist_ok=True)

    png_pfad = os.path.join(tempdir, os.path.basename(gif_pfad) + ".png")

    lauf = subprocess.run(
        ["rsvg-convert", "-w", breite, "-h", hoehe, svg_pfad, "-o", png_pfad],
        capture_output=True, text=True,
    )
    if lauf.returncode != 0:
        sys.exit(f"Fehler bei rsvg-convert fuer {svg_pfad}:\n{lauf.stderr}")

    # Verifizierte Kette aus plans/graphic-novel-plan.md, Abschnitt 2, Befund 5:
    # erst weiss unterlegen und schwellwerten, dann weiss transparent schalten.
    # Der naheliegende Weg ueber -background none erzeugt Anti-Aliasing-Farben
    # und macht ausgerechnet Schwarz transparent -- deshalb NICHT aendern.
    sw_pfad = os.path.join(tempdir, os.path.basename(gif_pfad) + ".sw.png")
    lauf = subprocess.run(
        ["magick", png_pfad, "-background", "white", "-alpha", "remove",
         "-alpha", "off", "-threshold", "60%", sw_pfad],
        capture_output=True, text=True,
    )
    if lauf.returncode != 0:
        sys.exit(f"Fehler bei magick fuer {svg_pfad}:\n{lauf.stderr}")

    if transparent:
        silhouette(sw_pfad, gif_pfad, breite, hoehe, tempdir, png_pfad)
    else:
        lauf = subprocess.run(["magick", sw_pfad, f"GIF:{gif_pfad}"],
                              capture_output=True, text=True)
        if lauf.returncode != 0:
            sys.exit(f"Fehler bei magick fuer {svg_pfad}:\n{lauf.stderr}")

    gif_rel = os.path.relpath(gif_pfad, ART_DIR)
    print(f"geschrieben: {gif_rel} ({breite}x{hoehe})")
    return gif_pfad, transparent


def silhouette(sw_pfad, gif_pfad, breite, hoehe, tempdir, png_pfad):
    """Setzt die Puppe aus Tusche und deckender Silhouette zusammen.

    Die Silhouette kommt aus der Zeichnung selbst (umriss() in
    tools/portraits.py) und liegt im SVG als weisse Flaeche vor. Im
    gerenderten PNG ist damit alles undurchsichtig, was zur Figur gehoert,
    und alles daneben durchsichtig. Genau dieser Alphakanal wird hier zur
    Maske: die Farben werden auf Schwarz und Weiss geschwellt, die
    Durchsichtigkeit bleibt erhalten.
    """
    basis = os.path.basename(gif_pfad)
    maske = os.path.join(tempdir, basis + ".maske.png")

    schritte = [
        # Alphakanal des gerenderten SVG als Maske: weiss, wo die Figur ist.
        ["magick", png_pfad, "-alpha", "extract", "-threshold", "40%", maske],
        ["magick", sw_pfad, maske, "-alpha", "off",
         "-compose", "CopyOpacity", "-composite", f"GIF:{gif_pfad}"],
    ]
    for kommando in schritte:
        lauf = subprocess.run(kommando, capture_output=True, text=True)
        if lauf.returncode != 0:
            sys.exit(f"Fehler in der Silhouetten-Kette fuer {gif_pfad}:\n{lauf.stderr}")


def pruefe_gif(gif_pfad, transparent):
    """Ruft lilt fuer eine erzeugte Datei auf und prueft das Muster-Histogramm.

    Erwartung bei transparent=1: nur die Muster 0 und 1.
    Erwartung bei transparent=0: kein Muster 0.
    Gibt bei Abweichung eine Warnung aus und liefert False zurueck.
    """
    # Decker liefert das Histogramm eines Bildes fertig als "hist". Eine
    # eigene Schleife ueber alle Pixel waere dasselbe Ergebnis, dauert bei
    # 480x624 aber fast 300.000 Lil-Schritte je Datei und macht den
    # Pruefschritt um Groessenordnungen langsamer als die Umwandlung selbst.
    lilt_ausdruck = 'i:read["%s"] show[i.size] show[i.hist]' % gif_pfad
    lauf = subprocess.run(["lilt", "-e", lilt_ausdruck], capture_output=True, text=True)
    if lauf.returncode != 0:
        print(f"WARNUNG: lilt-Aufruf fuer {gif_pfad} fehlgeschlagen:\n{lauf.stderr}")
        return False

    ausgabe = lauf.stdout
    gif_rel = os.path.relpath(gif_pfad, ART_DIR)

    # lilt gibt zwei Zeilen aus: zuerst die Bildgroesse (show[i.size]), dann
    # das Histogramm (show[d]). Nur die letzte, nichtleere Zeile auswerten.
    zeilen = [z for z in ausgabe.splitlines() if z.strip()]
    if not zeilen:
        print(f"WARNUNG: {gif_rel} lieferte keine lilt-Ausgabe.")
        return False
    histogramm = zeilen[-1]

    # image.hist liefert die Muster als Zahlen: {0:285047,1:14473}
    muster = set()
    for teil in histogramm.replace("{", "").replace("}", "").split(","):
        teil = teil.strip()
        if not teil:
            continue
        schluessel = teil.split(":")[0].strip().strip('"')
        if schluessel.lstrip("-").isdigit():
            muster.add(int(schluessel))

    if not muster:
        print(f"WARNUNG: {gif_rel} lieferte kein lesbares Histogramm: {histogramm.strip()}")
        return False

    if transparent:
        # 0 transparent, 1 Tusche, 32 das deckende Weiss der Silhouette.
        unerwartet = sorted(muster - {0, 1, 32})
        if unerwartet:
            print(f"WARNUNG: {gif_rel} hat unerwartete Muster {unerwartet} (erwartet nur 0 und 1): {histogramm.strip()}")
            return False
    else:
        if 0 in muster:
            print(f"WARNUNG: {gif_rel} enthaelt Muster 0, obwohl transparent=0: {histogramm.strip()}")
            return False

    return True


def main(argv):
    pruefen = "--pruefen" in argv
    praefixe = [a for a in argv if a != "--pruefen"]
    praefix = praefixe[0] if praefixe else None

    pruefe_werkzeuge()
    zeilen = lies_manifest(praefix)
    if not zeilen:
        sys.exit(f"Fehler: keine Manifest-Zeilen fuer Praefix '{praefix}' gefunden.")

    erzeugt = []
    with tempfile.TemporaryDirectory() as tempdir:
        for zeile in zeilen:
            erzeugt.append(rendere_zeile(zeile, tempdir))

    print(f"\n{len(erzeugt)} Datei(en) erzeugt.")

    if pruefen:
        alle_sauber = True
        for gif_pfad, transparent in erzeugt:
            if not pruefe_gif(gif_pfad, transparent):
                alle_sauber = False
        if alle_sauber:
            print(f"Pruefung sauber: alle {len(erzeugt)} Datei(en) entsprechen der Erwartung.")
        else:
            print("Pruefung fehlgeschlagen: siehe Warnungen oben.")
            sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
