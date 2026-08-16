# Stilvorlage: Tuschezeichnung (Urmel-Bücher, Franz Josef Tripp)

Verbindliche Beschreibung des Zielstils für alle Grafiken in [img/](img/).

**Leitreferenz:** [`in/u2/000008.jpg`](../in/u2/000008.jpg) – sitzender bärtiger Mann im Anzug, Hand am Kinn.
**Ergänzend:** [`in/u1/.../000075.png`](../in/u1/OEBPS/Images/000075.png) (Kinderporträt, Aufbau eines Gesichts), [`in/u2/000013.jpg`](../in/u2/000013.jpg) (Fell, Schraffur), [`in/u1/.../000060.png`](../in/u1/OEBPS/Images/000060.png) (Figur mit Bart und Mantel).

## 1. Werkzeug und Duktus

Spitzfeder bzw. Pinsel mit Tusche auf rauem Papier. Jeder Strich ist eine einmalige, schnelle Handbewegung – ohne Vorzeichnung, ohne Korrektur, ohne Nachziehen. Das Bild wirkt in einem Zug hingeworfen, nicht konstruiert.

## 2. Strichstärke – das zentrale Merkmal

- **Innerhalb eines einzigen Strichs** schwankt die Breite um den Faktor 3 bis 8. Der Strich setzt haarfein an, schwillt dort an, wo Druck auf der Feder liegt, und läuft spitz aus, wenn die Feder abhebt.
- Es gibt zwei deutlich getrennte Strichfamilien:
  - **Konturstriche** – fein (bei 400 px Bildbreite ca. 1,5–3 px), beschreiben Silhouetten und Gesichtszüge.
  - **Akzentstriche** – fett und stark keilförmig (ca. 6–14 px an der dicksten Stelle, spitz auslaufend). Sie sitzen an Falten, Schattenkanten und Überschneidungen und tragen die ganze Zeichnung. Ohne sie wirkt das Bild leer.
- Der Kontrast zwischen diesen beiden Familien ist das, was den Stil ausmacht.
- **Niemals** gleichmäßig breite Linien.

## 3. Konturen sind offen

- Silhouetten sind nicht geschlossen. Linien brechen ab und setzen leicht versetzt wieder an; Lücken von 5–20 % der Linienlänge sind normal.
- Linien **schießen über** Kreuzungspunkte hinaus (3–10 px Überstand). Ecken werden nicht sauber geschlossen.
- Das Auge ergänzt die Form – gerade das erzeugt die Lebendigkeit.

## 4. Keine Symmetrie, keine Geometrie

Kein Kreis ist rund, keine Körperhälfte gleicht der anderen. Brillengläser sind schiefe Ovale, Augen unterschiedlich groß, der Kopf ist leicht gekippt.

## 5. Haare und Bart

- Nie als geschlossene, flächig gefüllte Silhouette.
- Stattdessen: ein Bündel einzelner, vom Kopf bzw. Kinn **nach außen strahlender** Striche – dick am Ansatz, spitz auslaufend, unterschiedlich lang, unterschiedlich gekrümmt, einander überkreuzend.
- Dazwischen einzelne massive schwarze Klumpen mit gezackten Rändern und kleinen Spitzen.
- Der Rand der Frisur ist immer zerfranst, nie glatt.

## 6. Schwarzflächen

Sparsam, klein, als Akzent – nicht als Füllung. Immer unregelmäßig geformt, mit ausfransenden Spitzen an mindestens einer Seite. Typische Orte: Schatten unter dem Kinn, Nasenloch, Mundwinkel, Kleidungsfalte, Achselhöhle.

## 7. Tuschespritzer

15–40 zufällige Punkte, Kommas und unregelmäßige Kleckse (1–6 px) rund um die Figur. Ungleichmäßig verteilt (Cluster statt Raster), teils dicht am Motiv, teils weit weg. Sie gehören zum Stil und sind keine Verschmutzung.

## 8. Gesichtszüge – extrem sparsam

- **Augen:** winziges Mandel- oder Strichzeichen mit Punktpupille. *Kein* weißes Augapfel-Oval mit Kreis darin.
- **Nase:** ein einziger hakenförmiger Strich.
- **Mund:** ein dünner Strich; die Mundwinkel häufig durch je einen kleinen runden Punkt betont.
- **Ohr:** ein kleiner „c"-Haken.
- **Augenbrauen:** je ein keilförmiger Strich, asymmetrisch gesetzt.
- Der Ausdruck entsteht aus sechs bis acht Strichen, nicht aus Modellierung.

## 9. Schraffur

Selten und locker: kurze, leicht divergierende Parallelstriche unterschiedlicher Länge. Nie ein sauberes Kreuzschraffur-Raster.

## 10. Ausdrücklich nicht vorkommend

Gleichmäßige Strichstärke · geschlossene saubere Pfade · Spiegelsymmetrie · geometrische Kreise und Ellipsen · große glatte Schwarzflächen · weiße Glanzlichter im Auge · Graustufen, Transparenz oder Farbverläufe.

## 11. Technische Konsequenz für SVG

Striche dürfen **nicht** als `stroke` mit `stroke-width` gezeichnet werden – das erzeugt zwangsläufig gleichmäßig breite Linien und damit den Vektor-Clipart-Look. Jeder Strich muss als **gefüllter Umriss** (`fill="#000"`, kein `stroke`) erzeugt werden, dessen Breite entlang der Mittellinie variiert.

Die Grafiken werden deshalb aus [`tools/ink.py`](../tools/ink.py) heraus generiert; die Bildinhalte stehen in [`tools/portraits.py`](../tools/portraits.py).
