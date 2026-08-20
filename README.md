# Visual Novel

Die Merkmale der Figuren stehen in
[doc/stil-tuschezeichnung.md](doc/stil-tuschezeichnung.md).

### Gesichter erzeugen

Die Porträts sind generiert, nicht von Hand gezeichnet – jeder Strich entsteht
als gefüllter Umriss mit variabler Breite, jede Frisur aus Einzelsträhnen:

```bash
python3 tools/portraits.py            # alle 18 Dateien neu nach doc/img/
python3 tools/portraits.py lena-kowalski   # eine Figur, alle Ansichten
```

Pro Figur entstehen drei Ansichten für Dialoge: `name.svg` (frontal),
`name-von-links.svg` (Gesicht nach rechts gewandt) und `name-von-rechts.svg`
(nach links gewandt).

- [tools/ink.py](tools/ink.py) – Strichgenerator (Feder-Duktus, Haare, Kleckse)
- [tools/portraits.py](tools/portraits.py) – Bildinhalt der sechs Figuren

### Personen

Profilseiten mit Gesichtern (siehe [doc/personen.md](doc/personen.md)):

- [Sarah Hoffmann](doc/sarah-hoffmann.md)
- [Jamal Al-Rashid](doc/jamal-al-rashid.md)
- [Michael Weber](doc/michael-weber.md)
- [Katharina "Kat" Müller](doc/katharina-mueller.md)
- [Lena Kowalski](doc/lena-kowalski.md) (investigative Journalistin)
- [Tom Schneider](doc/tom-schneider.md) (junger Entwickler) 


