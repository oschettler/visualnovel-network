# Handbuch "Das Netzwerk"

Dieses Verzeichnis enthält das Handbuch zur Visual Novel als
AsciiDoc-Quelltext und die Docker-basierte Build-Pipeline, die daraus
EPUB, PDF und HTML erzeugt.

## Verzeichnisstruktur

```
handbuch/
├── src/                      # Die Kapitel, in AsciiDoc
│   ├── 00-master.adoc        # Master-Datei (bindet alle Kapitel ein)
│   ├── 01-einleitung.adoc
│   ├── ...
│   ├── bilder/                # Beispielbilder (Szenen, Emote- und Figurenuebersichten)
│   └── diagrams/              # Generierte SVG-Diagramme (nicht von Hand bearbeiten)
├── diagrams/                 # Diagramm-Quellen im nomnoml-Format
│   ├── 01-architektur.nomnoml
│   └── ...
├── build/                    # Build-Pipeline
│   ├── Makefile
│   ├── Dockerfile
│   ├── metadata.yaml
│   ├── theme.yml             # PDF-Layout
│   └── generate-diagrams.sh
└── output/                   # Generierte Dateien (entsteht beim Bauen)
    ├── das-netzwerk-handbuch.epub
    ├── das-netzwerk-handbuch.pdf
    └── das-netzwerk-handbuch.html
```

## Voraussetzungen

- Docker Desktop, gestartet
- [nomnoml](https://github.com/skanaar/nomnoml) für die Diagramme:
  `npm install -g nomnoml`

Es ist keine lokale Ruby- oder Asciidoctor-Installation nötig, alles läuft
im Docker-Container `asciidoctor/docker-asciidoctor`.

## Verwendung

Alle Befehle werden aus `handbuch/build/` heraus aufgerufen:

```bash
cd handbuch/build

make diagrams   # SVG-Diagramme aus den nomnoml-Quellen erzeugen
make html       # HTML erstellen (am einfachsten zum Nachschauen)
make epub       # EPUB erstellen
make pdf        # PDF erstellen
make all        # EPUB und PDF erstellen
make clean      # output/ löschen
make help       # Übersicht aller Targets
```

Die fertigen Dateien landen in `handbuch/output/`.

## Ein Kapitel ändern

1. Die passende Datei in `handbuch/src/` bearbeiten.
2. `make html` aufrufen und `handbuch/output/das-netzwerk-handbuch.html`
   im Browser öffnen, um das Ergebnis zu prüfen.
3. Wenn alles passt, auch `make epub` und `make pdf` laufen lassen.

## Ein Diagramm ändern

1. Die passende `.nomnoml`-Datei in `handbuch/diagrams/` bearbeiten. Die
   Syntax ist in den bestehenden Dateien zu sehen, ausführlicher auf der
   [nomnoml-Seite](https://www.nomnoml.com/).
2. `make diagrams` aufrufen, das schreibt die SVG-Dateien nach
   `handbuch/src/diagrams/` neu.
3. Neu bauen (`make html` o.ä.), um das Ergebnis zu prüfen.

Jedes `.nomnoml` sollte `#background: white` enthalten, sonst haben die
Diagramme im PDF einen schwarzen statt einem weißen Hintergrund
(Asciidoctor-PDF interpretiert einen transparenten SVG-Hintergrund anders
als ein Browser).

## Ein Beispielbild ändern oder ergänzen

Beispielszenen liegen unter `handbuch/src/bilder/` und lassen sich mit dem
Werkzeug aus dem Hauptprojekt neu erzeugen:

```bash
python3 tools/szenenbild.py --ziel handbuch/src/bilder/<name>.png <hintergrund> <figur>:<emote>:<links|mitte|rechts> ...
```

Übersichten mehrerer Bilder nebeneinander (Emote-Reihe einer Figur, alle
sechs Figuren) entstehen mit `magick montage` direkt aus
`game/data/art/figuren/`.

## Ein neues Kapitel hinzufügen

1. Neue Datei `handbuch/src/NN-name.adoc` anlegen, mit einem eindeutigen
   Anker am Anfang, zum Beispiel `[[mein-kapitel]]`.
2. In `handbuch/src/00-master.adoc` eine passende `include::`-Zeile
   ergänzen.
3. Neu bauen.

## Fehlerbehebung

**"include file not found"** — meist ein Tippfehler im Dateinamen der
`include::`-Zeile in `00-master.adoc`, oder eine fehlende Datei in `src/`.

**PDF-Fehler "comparison of Float with String"** — ein Wert in
`build/theme.yml` benutzt eine Einheit (z. B. `em`), die diese
Asciidoctor-PDF-Version an dieser Stelle nicht akzeptiert. Zahl ohne
Einheit angeben.

**Kaputte Bilder im EPUB** — meist ein Widerspruch zwischen dem Pfad, unter
dem ein Bild im `.adoc` referenziert wird, und dem tatsächlichen
Speicherort. Am zuverlässigsten funktionieren Bildpfade, die *innerhalb*
von `src/` bleiben (siehe `src/diagrams/` und `src/bilder/`), nicht `../`
nach oben verlassen. Dieses Handbuch setzt deshalb kein globales
`:imagesdir:`, sondern schreibt jeden Bildpfad vollständig aus
(`image::diagrams/foo.svg[...]`, `image::bilder/foo.png[...]`).
