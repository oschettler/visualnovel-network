# Plan: Graphic Novel "Das Netzwerk"

Umsetzung der Novelle [Novelle_Zukunft-der-DW](../../Novelle_Zukunft-der-DW)
als spielbare Visual Novel in [Decker](../extern/decker), mit den Modulen
`dd` (Dialogizer), `pt` (Puppeteer) und `twee` (Ply).

Leitprinzip:
**Die Geschichte ist eine Datei, kein Programm.** Wer eine Szene ändert, eine
Figur auftreten lässt, einen Hintergrund wechselt oder eine Entscheidung
einbaut, editiert `game/data/szenen.twee` und baut neu. Kein Lil-Code nötig.

---

## 1. Ziel und Abgrenzung

Ziel ist eine **lineare, bebilderte Erzählung mit Entscheidungspunkten**, kein
Adventure und kein Tilemap-Spiel. Der Spieler klickt
sich durch Dialogboxen, sieht die sechs Figuren als Tuschezeichnungs-Puppen auf
einer Bühne und trifft an definierten Stellen Entscheidungen, die Textvarianten
und den Epilog beeinflussen.

Nicht Teil dieses Plans: Bewegung, Karten, Inventar, Minispiele.

Umfang der Vorlage: 30 Kapitel, 19.445 Wörter, vier Teile plus Epilog,
Januar 2026 bis März 2030.

---

## 2. Warum dieser Stack (und was davon bereits verifiziert ist)

Die drei Module decken je eine Schicht ab:

| Modul | Schicht | Liefert |
|---|---|---|
| `twee` / Ply | Struktur | Passagen, Links, Variablen, eingebettete Lil-Fragmente |
| `dd` (Dialogizer) | Präsentation | Modale Dialogbox, Klick-durch, Auswahlknöpfe, Textanimation |
| `pt` (Puppeteer) | Darstellung | Figuren auf der Bühne, Emotes, Blinzeln, Sprechanimation, Bewegung |

Die Module sind nicht dafür gebaut, zusammen zu laufen, passen aber genau
ineinander. Das wurde **headless mit `lilt` geprüft**, bevor dieser Plan
geschrieben wurde. Die Befunde:

**Befund 1: `twee.render[]` liefert genau die Struktur, die die Engine braucht.**

```lil
d:read["extern/decker/examples/decks/twee.deck"]
twee:d.modules.twee.value
r:twee.render[story "k01-buero" vars]
```

`r.value` ist eine rtext-Tabelle mit den Spalten `text`, `font`, `arg`, `pat`.
Für eine Passage mit zwei Links kam heraus:

```
| text                                     | font | arg       | pat |
| "!show sarah sorge centerleft\n!talk ... | ""   | ""        | 1   |
| "Konzept schreiben."                     | ""   | "Konzept" | 1   |
| "\n"                                     | ""   | ""        | 1   |
| "Fenster schließen."                     | ""   | "Fenster" | 1   |
```

Daraus folgt die zentrale Trennung der Engine: **Zeilen mit leerem `arg` sind
Prosa (gehen an `dd.say[]`), Zeilen mit gefülltem `arg` sind Auswahlmöglichkeiten
(gehen an `dd.ask[]`, `arg` ist das Sprungziel).**

**Befund 2: Regieanweisungen überleben das Ply-Rendering unverändert.**
Eine Zeile `!show sarah sorge centerleft` ist für Ply gewöhnlicher Fließtext
und landet unverändert in der rtext-Prosa. Dialogizer wiederum behandelt jede
Zeile in Rich Text, die mit `!` beginnt und durch Leerzeilen abgetrennt ist, als
Kommando und schickt sie als `command`-Ereignis an die aktuelle Karte, von wo
`pt.command[deck x]` sie übernimmt. Regie ist damit **Text in der twee-Datei**.

**Befund 3: `{lil}`-Fragmente laufen und verändern die Variablen.**
`{mut:mut+1}` im Passagentext ergab `r.vars` mit `{"mut":1}`. Bedingte Links
(`{if mut>3 rtext.make[...] end}`) funktionieren damit ebenfalls.

**Befund 4: Das Deck lässt sich headless zusammenbauen, Module inklusive.**

```lil
nd:newdeck[]
nd.add[read["...twee.deck"].modules.twee]
nd.add[read["...dialog.deck"].modules.dd]
nd.add[read["...puppeteer.deck"].modules.pt]
```

ergab ein Deck mit `{"twee":<module>,"dd":<module>,"pt":<module>}`. Karten und
Canvas-Widgets lassen sich mit `nd.add["card" name]` bzw. `c.add["canvas" name]`
anlegen und mit `write[pfad nd]` schreiben.

**Befund 5: Die Tuschezeichnungen kommen sauber als transparente Strichgrafik an.**
Verifizierte Kette:

```sh
rsvg-convert -w 154 -h 200 doc/img/sarah-hoffmann.svg -o sarah.png
magick sarah.png -background white -alpha remove -alpha off \
       -threshold 60% -transparent white GIF:sarah.gif
```

Das ergibt in Decker exakt zwei Werte: Pattern 0 (transparent, 26.712 Pixel) und
Pattern 1 (schwarz, 4.088 Pixel). Kein Graustufen-Matsch, keine Farbverirrung wie
beim Escanor7x-Terrain in zelda-network. Wichtig ist die Reihenfolge: erst weiß
unterlegen und schwellwerten, dann weiß transparent schalten. Der direkte Weg
(`-background none`) erzeugt Anti-Aliasing-Farben (Pattern 32, 44, 45, 46) und
macht ausgerechnet Schwarz transparent.

`lilt` liest `.gif`, aber **kein** `.png`/`.svg` (siehe zelda-network README) --
die Konvertierung ist deshalb Pflicht, kein Komfort.

---

## 3. Architektur

```nomnoml
#direction: down
#spacing: 50
#padding: 12

[<frame>Quellen|
  [Novelle .adoc|30 Kapitel|:pov: :date: *Ort:*]
  [doc/personen.md|6 Charakterprofile]
  [doc/stil-tuschezeichnung.md]
]

[<frame>Daten (game/data)|
  [szenen.twee|Passagen, Dialog, Regie, Auswahl]
  [figuren.csv|Puppe, Emote, Ansicht]
  [orte.csv|Hintergrund, Kapitelzuordnung]
  [art/*.gif|generierte Strichgrafik]
]

[<frame>Werkzeuge (tools)|
  [portraits.py|+ Emote-Tabelle]
  [szenen.py|Hintergründe im Tuschestil]
  [render_art.py|SVG nach GIF, 1-bit + transparent]
  [kapitel_zu_twee.py|Gerüst aus .adoc]
]

[<frame>Build (game/build)|
  [build_vn.lil|headless, lilt]
]

[<frame>Deck (game/build/netzwerk.deck)|
  [Module|twee, dd, pt]
  [Karte buehne|Hintergrund-Canvas + Engine-Skript]
  [Karten figurenblatt|je Figur, Emote-Canvases]
  [Karte hintergruende|alle Orte als Canvases]
  [Karte daten|Spielstand, szenen.twee]
]

[<frame>Quellen] -> [<frame>Daten (game/data)]
[<frame>Werkzeuge (tools)] -> [<frame>Daten (game/data)]
[<frame>Daten (game/data)] -> [<frame>Build (game/build)]
[<frame>Build (game/build)] -> [<frame>Deck (game/build/netzwerk.deck)]
```

Laufzeit-Datenfluss einer Passage:

```nomnoml
#direction: right
#spacing: 40

[Engine|liest Passagennamen]
[twee.render|Ply: Markup, Variablen, Links]
[rtext-Tabelle]
[Prosa (arg leer)]
[Auswahl (arg gesetzt)]
[dd.say|modale Box, splittet an Leerzeilen]
[on command|Karte buehne]
[pt.command|Puppen zeigen, bewegen, sprechen]
[eigene Kommandos|!bg !hell !dunkel !ton]
[dd.ask|Knöpfe, gibt Index zurück]
[nächste Passage]

[Engine] -> [twee.render]
[twee.render] -> [rtext-Tabelle]
[rtext-Tabelle] -> [Prosa (arg leer)]
[rtext-Tabelle] -> [Auswahl (arg gesetzt)]
[Prosa (arg leer)] -> [dd.say]
[dd.say] -> [on command]
[on command] -> [pt.command]
[on command] -> [eigene Kommandos]
[Auswahl (arg gesetzt)] -> [dd.ask]
[dd.ask] -> [nächste Passage]
[nächste Passage] -> [Engine]
```

---

## 4. Was ist Daten, was ist Code

**Daten (in `game/data/`, ohne Lil-Kenntnisse editierbar):**
Der komplette Erzähltext, die Sprecherzuordnung, jede Regieanweisung (welche
Figur wo mit welchem Emote steht, wer spricht, wann die Kamera wackelt), jeder
Hintergrundwechsel, jede Auswahlmöglichkeit samt Sprungziel, jede
Variablenänderung und jede bedingte Textvariante. Dazu die Zuordnung
Emote-Name zu Bilddatei und Ort-Name zu Hintergrundbild.

**Bewusst Code:**

- Die Engine-Schleife (Abschnitt 6) -- rund 80 Zeilen, danach unverändert.
- Der Zeichencode der Figuren in `tools/portraits.py` und der Hintergründe in
  `tools/szenen.py`. Ein Gesicht lässt sich nicht als Tabellenzeile ausdrücken.
  Die **Emote-Varianten** dagegen schon: sie sind Abweichungen von Mundbogen,
  Brauenwinkel und Lidstellung und gehören in eine Tabelle (Abschnitt 7).
- Widget-Layout (Größe und Position von Bühne, Dialogbox, Titelkarte).
- Der Dialogizer-Stil (Farben, Schriften, Rahmen, Textgeschwindigkeit) als
  Konfigurationsdictionary im Deck-Skript, mit umschaltbaren Varianten pro
  Kommando (`!hell`, `!dunkel`, `!rueckblende`).

**Bewusst nicht als Datei gepflegt, weil es sich berechnet:**
Der Kapitelindex und die Fortschrittsanzeige. Beide entstehen zur Laufzeit aus
den Tags der Passagen (`kapitel-07`, `teil-1`, `pov-sarah`) gegen den
gespeicherten Fortschritt.

---

## 5. Das Datenformat: `game/data/szenen.twee`

Echtes Twee 3, mit dem Story-Format **Ply**. Damit ist die Datei in Twine
bearbeitbar (Story Format über `https://beyondloom.com/decker/ply/format.js`
hinzufügen) und gleichzeitig von `twee.read[]` lesbar.

### 5.1 Konventionen

**Eine Passage ist eine Szene an einem Ort.** Kapitel mit Ortswechsel werden auf
mehrere Passagen aufgeteilt, Kapitel ohne auf eine. Erwartung: rund 45 bis 55
Passagen für 30 Kapitel.

**Passagenname:** `k<NN>-<kurzname>`, zum Beispiel `k01-buero`, `k15-abstimmung`,
`k15-abstimmung-nein`. Der Name ist der Sprungziel-Bezeichner, er wird nie
angezeigt.

**Kapitelanfänge tragen ihren Titel als Metadatum:**

```
:: k01-buero [kapitel-01 teil-1 pov-sarah] {"titel":"Kapitel 1: Die Vision"}
```

Daraus baut die Engine den Kapitelindex. Twee 3 erlaubt beliebige Schlüssel in
diesem Objekt, und `twee.write[]` gibt sie unverändert zurück, Twine behält die
Angabe beim Bearbeiten also bei.

**Bezeichner bleiben ohne Umlaute.** Passagennamen, Kommandonamen, Puppen- und
Emote-Namen, Hintergrund-Namen, Variablen- und Spaltennamen sind ASCII
(`k01-buero`, `!rueckblende`, `goerlitz-kinderzimmer`, `braue_l`). Das gilt nur
für Bezeichner. Jeder Text, den ein Spieler zu sehen bekommt, hat selbst-
verständlich Umlaute, und `lilt`, `twee.read[]` und `twee.render[]` reichen sie
verlustfrei durch (geprüft mit "Sarah öffnete das Fenster. Größe, Straße,
Müller.").

**Tags** tragen Metadaten für Werkzeuge und Index, nicht für die Darstellung:
`kapitel-01`, `teil-1`, `pov-sarah`, `datum-2026-01`. Die Darstellung steuern
Kommandos, weil die dann im Fließtext an genau der richtigen Stelle stehen und
nicht nur passagenweit gelten.

**Kommandos** (jeweils eigener Absatz, durch Leerzeilen abgetrennt; mehrere
Kommandos dürfen mit einfachem Zeilenumbruch gruppiert werden):

| Kommando | Wirkung | Herkunft |
|---|---|---|
| `!bg sarah-buero` | Hintergrundbild wechseln | eigenes Kommando |
| `!hell` / `!dunkel` / `!rueckblende` | Dialogizer-Stil umschalten | eigenes Kommando |
| `!zeit Januar 2026, Bonn` | Ort- und Zeitmarke einblenden | eigenes Kommando |
| `!schnell` / `!langsam` / `!tempo 3` | Textgeschwindigkeit | eigenes Kommando |
| `!show sarah sorge centerleft` | Puppe zeigen, Emote, Position | `pt` |
| `!move sarah centerright 45` | Puppe bewegen | `pt` |
| `!anim michael bob` | Leerlaufanimation | `pt` |
| `!hide tom` / `!clear` | Puppe(n) entfernen | `pt` |
| `!shake 5 5 15` | Bildschirm wackeln (Betonung) | `pt` |
| `!play klopfen` | Ton abspielen | `pt` |
| `!wait 30` | warten, Animation laufen lassen | `pt` |
| `!lil ...` | einmalige Sonderlogik | `pt` |

**Sprecher** stehen als Präfix im Text (`Sarah: Ich habe eine Idee.`), so wie in
den Puppeteer-Beispielen. Erzähltext bekommt kein Präfix. Nebenfiguren ohne
Portrait (Dr. Hartmann, Frau Brandt, Claudia, Lisa, Alex, Aisha) sprechen
ebenfalls per Präfix, ohne Puppe -- das ist bewusst so und braucht keine
Sonderbehandlung.

**Das Präfix ist die einzige Quelle dafür, wer spricht.** Die Engine liest es
ab und leitet daraus alles Weitere her, deshalb gibt es keine `!talk`-Kommandos
mehr in der Szenendatei:

- Die Puppe mit dem kleingeschriebenen Vornamen bewegt den Mund
  (`Sarah:` steuert die Puppe `sarah`). Gibt es keine solche Puppe, spricht
  eine Nebenfigur, und keine Puppe bewegt sich.
- **Erzähltext bewegt keine Münder.** Ein Absatz ohne Sprecherpräfix schaltet
  die Sprechanimation ab.
- Erzähltext und Rede sehen verschieden aus: die Rede behält die Stimmung der
  Szene, der Erzähltext dreht sie um. Damit bleiben beide in jeder Stimmung
  auseinanderzuhalten. Beide sind linksbündig. Der Erzähltext stand zunächst
  zentriert, was sich beim Lesen als schlecht erwies: bei mehrzeiligem
  Fließtext springt der Zeilenanfang, und das Auge verliert die Spur.
- **Zwei Sprecher unterscheiden sich über die Ausrichtung der Dialogbox**, und
  zwar automatisch: Puppeteer legt pro Puppe ein Canvas-Widget mit genau ihrem
  Namen auf der Karte an, also liest die Engine die Bühnenseite des Sprechers
  direkt ab. Wer links steht, spricht linksbündig, wer rechts steht,
  rechtsbündig. Das braucht keine Tabelle und stimmt immer, auch wenn Figuren
  während der Szene die Seite wechseln.
- Der Name selbst erscheint in der Menü-Schrift, der Rest im Fließtext.

Erkannt wird ein Sprecher an einem kurzen Vorspann vor dem Doppelpunkt, der
wie ein Name aussieht: höchstens drei Wörter, höchstens 24 Zeichen, jedes Wort
großgeschrieben. So bleibt `Dr. Hartmann: ...` ein Sprecher, während
`Sie las: der Bescheid war da.` Erzähltext bleibt, weil "las" klein anfängt.

**Auswahl** über Ply-Links am Ende der Passage:
`[[Den Antrag stellen.->k01-antrag]]`. Eine Prosazeile, die mit `?` beginnt, ist
die Frage über den Knöpfen; fehlt sie, nimmt die Engine "Was tust du?".

**Genau ein Link ist keine Auswahl, sondern eine Fortsetzung.** Die Engine
zeigt dann die Beschriftung als letzte Textbox und springt weiter, statt einen
Knopf mit nur einer Möglichkeit anzubieten. Schreibe deshalb sprechende
Beschriftungen (`[[Es klopft.->k01-michael]]`), keine Platzhalter wie
"Weiter.". Erst ab zwei Links erscheint die Frage mit Knöpfen.

**Variablen** über `{lil}`-Fragmente. Sie bleiben über Passagen hinweg erhalten
(`r.vars` wird zurückgereicht) und werden nach jeder Passage gespeichert.

### 5.2 Beispielpassage (Kapitel 1, gekürzt)

```
:: StoryData
{
  "format": "Ply",
  "format-version": "1.0.0",
  "start": "k01-buero"
}

:: k01-buero [kapitel-01 teil-1 pov-sarah datum-2026-01]
!bg sarah-buero
!zeit Januar 2026, Bonn
!dunkel

Der Schnee fiel leise auf die Dächer der Bonner Innenstadt, als Sarah
Hoffmann das Fenster ihres Büros im siebten Stock öffnete.

!show sarah schock center
!talk sarah

USAGM workforce reduced by 85 percent. Voice of America effectively silenced.

Sarah: Fünfundachtzig Prozent. In sechs Monaten. Das war keine
Umstrukturierung. Das war eine Hinrichtung.

!show sarah denk
!play klopfen
!move sarah centerleft 30
!show michael sorge offcenterright
!move michael centerright 45
!wait
!talk michael

Michael: Fünfundachtzig Prozent. Das könnte uns auch passieren.

!talk sarah

Sarah: Ich weiß.

? Was antwortest du Michael?

[[Ich habe eine Idee.->k01-idee]]
[[Noch nicht. Erst nachdenken.->k01-zoegern]]

:: k01-idee [kapitel-01 teil-1 pov-sarah]
{entschlossenheit:entschlossenheit+1 ""}
!show sarah ent

Sarah: Ich habe eine Idee.

Sie drehte ihren Monitor zu ihm. Michael las schweigend.

!show michael denk
!talk michael

Michael: Föderiert. Wie E-Mail.

[[Weiter.->k01-email]]
```

Ein `{...}`-Fragment, das nur eine Variable setzen soll, endet mit `""`, sonst
erscheint sein Wert im Text.

### 5.3 Gerüst aus den Kapiteln erzeugen

26 der 30 Kapitel tragen bereits strukturierte Metadaten (`:pov:`, `:date:`,
`*Ort:*`). `tools/kapitel_zu_twee.py` liest die `.adoc`-Dateien und erzeugt für
jedes Kapitel eine Passage mit korrekten Tags, `!bg`- und `!zeit`-Kommando und
dem Rohtext als Prosa. Das ist ein **einmaliger Startpunkt zum Weiterschreiben**,
kein wiederholbarer Build-Schritt: die Adaption (Kürzen, Prosa in Dialog
auflösen, Regie setzen) ist Schreibarbeit und passiert danach von Hand in der
twee-Datei.

Realistische Erwartung: aus 19.445 Wörtern Prosa werden etwa 8.000 bis 10.000
Wörter Dialog und Erzähltext. Eine Visual Novel verträgt keine
Absatzbeschreibungen, die das Bild ohnehin zeigt.

---

## 6. Die Engine (`game/lil/vn.lil`, plus Skripte im Deck)

Die Engine ist eine einzige blockierende Schleife. Das ist möglich, weil
`dd.say[]` und `dd.ask[]` synchron sind: ein kompletter Spieldurchlauf läuft in
**einem** Skriptaufruf ab. Während Dialogizer wartet, schickt es `animate`- und
`command`-Ereignisse an die aktuelle Karte, sodass Puppen weiter blinzeln und
Regieanweisungen greifen.

Die tatsächliche Fassung steht in `game/lil/vn.lil` und wird von
`build_vn.lil` als Deck-Skript eingesetzt. Der Kern:

```lil
on spiele start do
  s:lade_stand[]
  if start~"neu" s:frischer_stand[] end
  dd.open[deck stil.dunkel]
  while 1
    r:twee.render[STORY s.passage s.vars]
    s.vars:r.vars
    zeilen:r.value
    prosa:select where arg="" from zeilen
    wahl:select where !arg="" from zeilen
    frage:vn_prosa[prosa]
    labels:extract text from wahl
    ziele:extract arg from wahl
    if 0~count wahl
      laeuft:0
    elseif 1~count wahl
      dd.say[first labels]
      s.passage:first ziele
      vn_speichern[s]
    else
      i:dd.ask[frage labels]
      s.passage:ziele[i]
      vn_speichern[s]
    end
  end
  dd.close[]
  pt.clear[]
end
```

**`where !arg=""` ist hier die einzige richtige Form.** Der naheliegende
Ausdruck `where 0<count arg` filtert überhaupt nicht: `count` aggregiert die
ganze Spalte zu einer Zahl statt zeilenweise zu zählen, die Bedingung ist damit
konstant wahr. In der Engine führte das zu einer Endlosschleife, weil als
Sprungziel ein leerer Passagenname herauskam. Gefunden hat es der Test, nicht
das Lesen. Seitdem prüft die Schleife zusätzlich, ob es die Zielpassage
überhaupt gibt, und bricht sonst mit einer sichtbaren Meldung ab, statt zu
hängen.

Dazu im Deck-Skript die von Puppeteer geforderte Weiterleitung, erweitert um die
eigenen Kommandos (Muster aus der Karte "custom commands" der `puppeteer.deck`):

```lil
on animate do
  pt.animate[deck]
end

on command x do
  each z in "\n" split x
    vn_kommando[z]
  end
end
```

**Der Handler muss zuerst in Zeilen zerlegen.** Dialogizer schickt einen
ganzen Absatz als ein Kommando, und mehrere Regieanweisungen dürfen darin mit
einfachem Zeilenumbruch gruppiert sein (so beschreibt es die Puppeteer-Doku,
und `pt` zerlegt intern genauso). Ohne das Zerlegen schluckt das erste
Kommando den ganzen Block als Argument: aus

```
!zeit Januar 2026, Bonn, 18 Uhr
!show sarah neutral centerleft
!move michael centerright 45
```

wurde eine Ortsmarke mit drei Zeilen Text, und `!show` und `!move` liefen nie.
Auch das hat der Test gefunden.

**Zustand und Speichern.** Der Spielstand ist ein Dictionary
(`passage`, `vars`, `gesehen`) und wird nach jeder Passage als LOVE-String in ein
unsichtbares Feld auf der Karte `daten` geschrieben. Verifiziert:

```lil
s:"%J" format zustand      # -> {"mut":3,"tom_fehler":1}
zustand:"%J" parse s       # -> dict, verlustfrei zurück
```

Damit funktioniert "Weiterspielen" auch nach dem Schließen des Decks, obwohl
die Schleife selbst nie unterbrochen wird.

**Hintergründe zur Laufzeit.** Alle Orte liegen als Canvases auf einer
unsichtbaren Karte `hintergruende` (genau wie Puppeteers Figurenblätter).
`hintergrund[name]` kopiert das passende Bild in das Bühnen-Canvas
(`buehne.paste[hintergruende.widgets[name].copy[] (0,0)]`). Kein Kartenwechsel,
kein Nachladen von der Platte (die interaktive Decker-App darf das nicht).

**Achtung bei der Umsetzung** (siehe zelda-network README, "Sechs
Lil-Fallstricke"): in `where`-Klauseln gehört `=` hin, nicht `~`; Funktionsaufrufe
vor einem Komma in einer Liste immer klammern; `each` gibt zuerst den **Wert**,
dann den Schlüssel; Verkettung ist `"" fuse (a,b,c)`, nicht `"praefix" fuse (a,b)`.

---

## 7. Figuren: Puppen und Emotes

### 7.1 Was Puppeteer erwartet

Ein Figurenblatt ist eine Karte, deren **Name der Puppenname** ist. Jedes Emote
ist ein Canvas auf dieser Karte. Zusatzkonventionen:

- `<emote>_blink` -- wird automatisch periodisch eingeblendet.
- `<emote>_open`, `<emote>_open2` -- Sprechanimation, zyklisch durchlaufen,
  sobald `!talk <name>` gesetzt und `dd`s `.speed` ungleich 0 ist.

Puppen werden transparent gezeichnet (Pattern 0), was die Pipeline aus Abschnitt
2, Befund 5 liefert.

### 7.2 Emote-Katalog

Sechs Emotes je Figur, abgeleitet aus den Charakterprofilen. Weniger wäre zu
arm, mehr lässt sich im Tuschestil aus sechs bis acht Strichen im Gesicht nicht
mehr unterscheiden.

| Emote | Ausdruck | Trägt vor allem |
|---|---|---|
| `neutral` | ruhig, wach | Erzählfluss |
| `denk` | Blick abgewandt, Braue gehoben | Michael, Jamal |
| `sorge` | Brauen zusammen, Mund schmal | Jamal, Kat, Michael |
| `ent` | Kinn leicht angehoben, fester Mund | Sarah, Lena |
| `freude` | Mundwinkel hoch, Lidbogen | Tom, Kat |
| `schock` | Augen groß, Mund offen, Braue hoch | Wendepunkte |

Pro Figur ergibt das 6 Basis-Canvases, 6 `_open`-Canvases und 2 `_blink`
(für `neutral` und `ent`, wo Figuren am längsten stehen): **14 Canvases je
Figur, 84 insgesamt**, alle generiert.

### 7.3 Erweiterung von `tools/portraits.py`

Die Zeichenfunktionen sind heute `sarah(p, turn=0.0)` und rufen `auge()`,
`mund()` und die Brauenstriche mit fest verdrahteten Koordinaten auf. Der Umbau:

1. Jede Figur deklariert ihre Gesichtsgeometrie als Dictionary (Augenposition und
   -radius, Brauenpunkte, Mundpunkte) statt sie inline zu zeichnen.
2. Eine gemeinsame Funktion `gesicht(p, geo, emote)` zeichnet daraus, moduliert
   über eine **Emote-Tabelle**: Mundbogen (`bow`), Brauenneigung, Lidstellung,
   Pupillenversatz, Mundöffnung.
3. Haare, Kleidung, Tuschespritzer und Silhouette bleiben unverändert
   figurenspezifischer Code.

Die Emote-Tabelle ist damit Daten und in `game/data/emotes.csv` pflegbar:
`emote,bow,braue_innen,braue_aussen,lid,pupille_x,pupille_y,mund_offen,augen_gross`.

`_blink` ist keine eigene Tabellenzeile, sondern ein Schalter: Auge als
einzelner Bogen statt Mandel plus Pupille. `_open` ist die Emote-Zeile mit
`mund_offen=1`.

**Der Mundbogen gehört halb der Figur, halb dem Emote.** Eine Tabelle für alle
sechs Figuren hatte zunächst einen Nebeneffekt, der beim Vergleich mit den
alten Zeichnungen auffiel: Kats warmes Lächeln (Grundbogen 15) und Toms
Dauergrinsen (21) verschwanden, weil `neutral` für alle denselben Wert 3 setzt.
Damit sahen drei Figuren im am häufigsten gezeigten Ausdruck deutlich
neutraler aus als vorher. Die Lösung steht in `GEO`: jede Figur hat eine eigene
Grundkrümmung (Michael 4, Sarah 3, Jamal 2, Kat 15, Lena 5,5, Tom 21). Bei
`neutral` gilt sie voll, sonst nur anteilig.

Wie stark sie nachwirkt, ist selbst eine Spalte der Emote-Tabelle
(`bogen_daempfung`), keine Konstante im Code. Ein erster Versuch mit einem
festen Wert von 0,4 für alle Emotes zeigte im Bild, warum das nicht reicht:
Toms `ent` blieb dabei ein Lächeln, obwohl der ganze Sinn des Ausdrucks ein
fester gerader Mund ist. Ausdrucksstarke Emotes müssen die Grundkrümmung fast
verdrängen dürfen (`ent` 0,15, `sorge` 0,2, `schock` 0,3), weiche behalten sie
(`denk` und `freude` 0,6). So bleibt Tom auch besorgt freundlicher als Lena,
ohne dass `sorge` bei ihm zum Lächeln wird.

### 7.4 Blickrichtung

Jede Figur liegt in **drei Blickrichtungen** vor: frontal, `_r` (turn +0.30,
Gesicht nach rechts, steht also links) und `_l` (turn -0.30, steht rechts).
Sprechen zwei Figuren miteinander, wenden sie sich dadurch einander zu.

`!flip` wird **nicht** benutzt: eine gespiegelte Tuschezeichnung sieht falsch
aus (Nasenhaken zeigt in die falsche Richtung, das verdeckte Ohr taucht auf).
Der Generator zeichnet die Drehung stattdessen richtig, als Zylinderprojektion
um die Hochachse.

Technisch sind das drei Puppen, weil Puppeteer eine Puppe über den Namen ihrer
Karte anspricht. **In der Szenendatei steht trotzdem nur `sarah`.** Die Engine
leitet die Variante aus der Bühnenposition ab: eine Position, die "left"
enthält, ergibt `sarah_r`, eine mit "right" ergibt `sarah_l`, alles andere
bleibt frontal. Ohne Positionsangabe (etwa bei einem reinen Emotewechsel) gilt
die Variante, die schon auf der Bühne steht; die Engine liest das an den
vorhandenen Widgets ab und braucht dafür keinen mitgeführten Zustand. Wechselt
eine Figur die Seite, räumt die Engine die alte Variante selbst ab.

`!move` behält die Blickrichtung bei, weil ein Wechsel mitten in der Bewegung
ein anderes Widget wäre. Wer die Richtung ändern will, nimmt `!show` mit neuer
Position.

**Welche Variante gerade gilt, entscheidet die Sichtbarkeit, nicht die
Existenz.** Puppeteers `!hide` entfernt das Widget nicht, es setzt nur
`show` auf `"none"`. Wer nur fragt, ob ein Widget existiert, findet deshalb
auch längst versteckte Varianten und versteckt beim nächsten `!hide` die
falsche, während die sichtbare neben der nächsten Figur stehen bleibt. Genau
so entstand nach dem Einbau der Blickrichtungen wieder eine Überlagerung, die
die Bauprüfung nicht sehen konnte, weil sie mit den schlichten Figurennamen
rechnet.

Kosten: 6 Figuren mal 14 Bilder mal 3 Richtungen sind 252 Zeichnungen. Der
Generator braucht dafür 10 Sekunden, die Umwandlung nach GIF weitere 40, und
das Deck wächst von 768 KB auf gut 2 MB.

### 7.5 Größen

Die Karte ist 512x342 (Decker-Standard), die Portraits sind 400x520. Die
Puppengröße ist **240x312**, also `rsvg-convert -w 240 -h 312`.

Ursprünglich standen hier 150x195, und das war falsch. Bei dieser Größe bricht
der Stil zusammen, was erst der Blick auf das fertige Bild zeigte: die
Einzelsträhnen der Frisur laufen zu einer geschlossenen schwarzen Fläche
zusammen (genau die "Haarkappe", die `doc/stil-tuschezeichnung.md` als
auffälligsten Stilbruch benennt), die feinen Konturstriche von 1,5 bis 3 px
schrumpfen unter einen Pixel und fallen beim Schwellwerten ganz weg, und
`neutral`, `denk` und `ent` sind nicht mehr unterscheidbar. Eine höhere
Schwelle (75 statt 60 Prozent) hilft nicht, sie macht die Haare nur noch
massiver. Entscheidend ist die Größe: bei 240x312 bleiben Strähnen, Brauen und
Mundlinie erhalten.

Ein 240 Pixel breiter Kopf ist auf einer 512 Pixel breiten Karte viel, aber
genau richtig: zwei Figuren nebeneinander belegen 480 Pixel, und die unteren
rund 110 Pixel verschwindet ohnehin hinter der Dialogbox. Sichtbar bleibt die
Büste über der Box, also der übliche Aufbau einer Visual Novel. Großaufnahmen
sind damit vorerst überflüssig.

**Lehre daraus:** Bildgrößen in diesem Stil nicht ausrechnen, sondern
ansehen. Ein fertiges GIF lässt sich mit
`magick datei.gif -scale 300% probe.png` jederzeit prüfen.

### 7.6 Die Karte ist 1024x684, nicht 512x342

Auch bei 240x312 blieb die Darstellung sichtbar grob, und zwar aus einem
Grund, der nichts mit der Zeichnung zu tun hat: Decker rechnet die ganze
Karte im Fenstermodus nachbarschaftlich hoch (es gibt dafür sogar den
Startschalter `--no-scale`). Die Zeichnungen liegen 1:1 vor, die Grenze ist
die Kartengröße.

Das Deck läuft deshalb mit **1024x684** und Puppen in **480x624**. Der
direkte Vergleich derselben Zeichnung bei 240 und bei 480 Pixeln Breite
zeigt den Unterschied deutlich: erst bei 480 trennen sich die Haarsträhnen
wieder, werden Brillengläser rund statt eckig, und die Strichstärke variiert
sichtbar, also genau das, was `doc/stil-tuschezeichnung.md` als Kern des
Stils benennt.

Die Kartengröße steht nur im Dateikopf (`size:[1024,684]`) und ist über die
Deck-Schnittstelle nicht erreichbar. Das Format erlaubt ausdrücklich, sie
von Hand zu ändern ("this permits hand-altering the size of a deck without
mangling its contents", `format.md`), deshalb schreibt `build_vn.lil` das
Deck, tauscht die Zeile im kodierten Text und liest es mit `newdeck[]`
wieder ein.

**Schriften mussten mitwachsen.** Deckers eingebaute Schriften sind Bitmaps
mit fester Pixelhöhe, bei doppelter Karte wären sie physisch halb so groß.
`extern/decker/examples/decks/fonts.deck` liefert passenden Ersatz:

| Schrift | Höhe | Verwendung |
|---|---|---|
| `olympiad` | 20 | Rede, Titel, Knöpfe |
| `olympiad_italic` | 20 | Erzähltext |
| `ahmPicnic` | 20 | Sprechername, Ortsmarke |

Beim Hinzufügen muss der Name mitgegeben werden (`deck.add[schrift name]`),
sonst landet die Schrift namenlos im Deck und ist nicht ansprechbar.

### 7.7 Wie Erzähltext aussieht und wo er steht

Nach mehreren Durchläufen in Decker steht die Trennung so fest:

- **Rede** folgt der Stimmung der Szene (`!hell`, `!dunkel`), steht aufrecht
  in `olympiad` und richtet sich nach der Bühnenseite der sprechenden Figur.
  Die Box sitzt an der Standardstelle unten.
- **Erzähltext** ist immer schwarz auf weiß, unabhängig von der Stimmung, und
  steht kursiv in `olympiad_italic`. Zwei Unterscheidungsmerkmale statt einem,
  weil eines allein im Spiel zu schwach war: erst gab es nur die umgedrehte
  Stimmung, dann nur die Kursive.
- Der Erzähltext steht standardmäßig **oben in der Mitte**, in einer 760 Pixel
  breiten Box. Dialogizer zentriert die Box auf einem benannten Widget der
  aktuellen Karte, deshalb liegt auf der Bühne ein unsichtbarer Platzhalter
  `erzaehlplatz` bei (132,80) mit der Größe (760,140). Die Rechnung dahinter
  ist `box.pos = widget.pos + 0.5*(widget.size - box.size)`, das Widget
  beschreibt also das Rechteck, in dem die Box zentriert wird.
- Umschaltbar per `!erzaehler oben` und `!erzaehler unten`, gespeichert im
  Feld `erzaehlerpos` auf der Bühne. Die Rede setzt `pos` und `size` bei jedem
  Absatz ausdrücklich zurück, sonst bliebe sie am Erzählerplatz kleben.
- **Auch die Frage über den Auswahlknöpfen braucht einen eigenen Stil.**
  `dd.ask[]` erbt sonst den zuletzt gesetzten, also meist den des
  Erzähltextes, und eine Auswahlliste mit sieben Möglichkeiten läuft dann am
  oberen Bildrand aus dem Bild. `vn_stil_frage` setzt deshalb wieder
  Standardposition und volle Breite.

**Die Ortsmarke steht oben links, die Erzählbox darunter.** Beide oben zu
platzieren geht nur, wenn der Mittelpunkt des Platzhalters tief genug liegt:
die Box wächst von ihrem Mittelpunkt aus nach oben und unten, ein langer
Erzählabsatz würde sonst die Ortsmarke überdecken.

---

## 8. Hintergründe

18 Orte decken alle 30 Kapitel ab:

| Hintergrund | Kapitel |
|---|---|
| `sarah-buero` (BRI-Hochhaus, 7. Stock, Bonn) | 1, 7, 16, 22 |
| `innovation-lab` (Bonn) | 2, 17, 21, 25 |
| `michael-buero` (Research & Cooperations) | 3, 12, 19, 23 |
| `bri-akademie` (Bonn) | 4 |
| `kats-wg` (Köln-Ehrenfeld) | 4 |
| `uebersicht` (neutrale Fläche für die Teil II-Übersicht) | Teil II |
| `cafe-bonn` | 5, 13 |
| `lena-buero` (BRI-Redaktion) | 5, 20 |
| `ccc-halle` (37C3, Hamburg) | 6 |
| `konferenzraum` (BRI Bonn) | 7, 8 |
| `sarahs-wohnung` (Bonn-Südstadt) | 9, 15, 24 |
| `jamals-wohnung` | 10 |
| `goerlitz-kinderzimmer` | 11, 15 |
| `toms-wg` (Berlin-Kreuzberg) | 14, 15 |
| `videokonferenz` (Kachelraster, hybrides Treffen) | 15 |
| `nairobi-hub` | 18, 26 |
| `pressekonferenz` (Berlin) | 27 |
| `landgericht` (Berlin) | 28 |
| `bad-godesberg` (Michaels Wohnung) | 29, 30 |

Erzeugt werden sie in `tools/szenen.py` mit derselben `ink.Pen`-Technik wie die
Portraits: sparsame Strichzeichnung, offene Konturen, wenige Akzentstriche,
Tuschespritzer. Im Urmel-Stil ist ein Hintergrund ohnehin eher Andeutung als
Bühnenbild -- Fensterkreuz und Schneeflocken, ein Schreibtisch mit zwei
Monitoren, eine Serverschrankreihe. Fünf bis fünfzehn Züge je Bild.

Die 512x342-Bilder laufen durch dieselbe SVG-nach-GIF-Kette, nur ohne
Transparenz (`-alpha remove` ohne `-transparent`), weil ein Hintergrund deckend
sein soll.

Ein achtzehnter Ort stand hier zunächst mit drin, `toms-elternhaus` in
München. Er stammte aus `plans/orte.md` der Novelle, das eine ältere Fassung
von Kapitel 6 beschreibt. Im heutigen Kapiteltext kommt die Szene nicht vor
(`:location:` nennt nur Bonn und Hamburg), und auch sonst spielt kein Kapitel
dort. Aufgefallen ist das erst beim Adaptieren, nicht beim Planen.

### Wie die Hintergründe aussehen

Drei Dinge machen die Vorlagen als Szene aus:

1. Es gibt keinen Horizont und keine Wände. Die Gegenstände stehen auf
   weissem Papier.
2. Der Boden ist nur angedeutet: lockere waagerechte Schraffur, ein paar
   Steinchen, Tuschespritzer, dazu ein schwerer Zug, der die Linie trägt.
   Nie eine gefüllte Fläche.
3. Geräte und Möbel sind offene, leicht schiefe Umrisse mit wenigen Details:
   Knöpfe als Kreise, Nieten und Tasten als Punktreihen, Holzlatten als drei
   parallele Striche.

`tools/szenen.py` baut daraus einen Formenschatz (Kasten, Tisch, Stuhl,
Fenster, Regal, Serverschrank, Apparat, Kolben, Pflanze, Papierstapel,
Mikrofon, Sofa) und setzt die 18 Orte daraus zusammen. Zwei Fallen dabei:

- **Bricht ein Kasten an allen vier Kanten symmetrisch in der Mitte auf,
  entstehen vier Eckwinkel statt einer Form.** Nur eine Kante darf brechen,
  und die Linien müssen über die Ecken hinausschiessen.
- **Waagerechte Striche übereinander sind kein Papierstapel, sondern
  Schraffur.** Erst die seitlichen Kanten und ein schwerer Zug oben machen
  daraus einen Stapel. Dasselbe gilt für Schatten: wenige kurze Striche dicht
  unter dem Gegenstand, nie ein Block daneben.

### Die Figuren müssen den Hintergrund verdecken

Eine reine Strichzeichnung besteht aus Tusche und Transparenz. Ohne
Gegenmassnahme scheint der Hintergrund also mitten durch die Gesichter, und
bei zwei Figuren auf der Bühne wird das Bild unlesbar: Fensterkreuz im Auge,
Bodenschraffur quer über den Mund. In den Vorlagen ist die Figur dagegen
weisses Papier und verdeckt, was hinter ihr liegt.

**Die Silhouette gehört in die Zeichnung, nicht in eine Nachbearbeitung.**
`umriss()` in `tools/portraits.py` zeichnet vor allem anderen eine
geschlossene Fläche über Haar, Kopf, Hals und Schultern, und `Pen.flaeche()`
gibt sie im SVG als weissen Pfad unter der Tusche aus. Je Figur sind das
sechs Zahlen (Scheitelpunkt, halbe Breite oben und auf Ohrhöhe, Ende der
Haarpartie), die Schulterlinie ist für alle dieselbe und stammt aus
`hals_schultern()`.

Dazu darf `Pen.svg()` das weisse Rechteck über die ganze Fläche weglassen
(`grund=False`). Für die Puppen ist damit genau die Figur undurchsichtig und
alles daneben durchsichtig. `render_art.py` nimmt anschliessend einfach den
Alphakanal des gerenderten SVG als Maske.

Der Umweg über eine nachträgliche Bildbearbeitung (Tusche schliessen, von den
Rändern fluten, das Nichterreichte als Inneres nehmen) wurde verworfen: er
versiegelte den Kopf, nicht aber den Rumpf, denn der endet am unteren Bildrand
und ist dort offen. Aus der Zeichnung heraus ist es einfacher und vollständig.

**Reihenfolge-Empfehlung:** In M1 bis M5 ersetzt die `!zeit`-Ortsmarke
(eingeblendeter Text auf leerer Bühne) den Hintergrund. Erst in M7 werden die
Bilder gezeichnet. So blockiert die größte künstlerische Arbeit nicht die
Erzählung, und die Bühne ist jederzeit spielbar.

---

## 9. Story-Struktur und Verzweigung

### 9.1 Grundsatz

**Die Novelle bleibt kanonisch.** Der Spieler kann den Verlauf nicht kippen: das
Team stimmt zu, das Netzwerk entsteht, die Kürzung kommt, das Netzwerk hält.
Alles andere wäre eine zweite Novelle, keine Adaption.

Was der Spieler stattdessen tut: **er entscheidet, mit welcher Haltung die
Figuren durch die Geschichte gehen.** Das ist der eigentliche Stoff der Vorlage: 
Argumente dafür, dagegen, persönliche Kosten) und passt zu einem Medium, das aus Dialogboxen
besteht.

### 9.2 Drei Arten von Auswahl

**1. Haltungswahl (häufig, über die ganze Geschichte).**
Zwei bis drei Antwortmöglichkeiten in einer Szene. Sie führen nach ein bis
zwei Passagen wieder zusammen, verändern aber Variablen und damit späteren
Text.

**2. Die Abstimmung (Kapitel 15, einmalig, echte Verzweigung).**
Der Spieler stimmt für eine Figur seiner Wahl ab. Kanonisch stimmen alle sechs
zu. Stimmt der Spieler mit Nein, läuft eine eigene Passagenkette: die anderen
fünf machen weiter, die Figur des Spielers steigt aus, und die Geschichte kehrt
mit gesetzter Variable `ausgestiegen` in die Hauptlinie zurück. Betroffen sind
danach mehrere Szenen in Teil III und der Epilog.

**3. Perspektivwahl, aber nur in Teil II.**
Ursprünglich war sie auch für Teil III vorgesehen, unter der Annahme, dessen
Kapitel liefen parallel. Das stimmt nicht: die Kapitel 16 bis 29 sind streng
chronologisch, in Teil III eines alle drei Monate, in Teil IV monatlich. Eine
frei wählbare Reihenfolge würde dort die Kausalität zerstören, etwa Toms Fehler
im Januar 2029 nach dessen Entdeckung im Juni. Teil III und IV sind deshalb
linear; die freie Reihenfolge gibt es nur in Teil II, wo die sechs Kapitel
tatsächlich denselben Abend zeigen.

```nomnoml
#direction: down
#spacing: 45

[<start>Titel]
[Teil I|K1 bis K8|Haltungswahl je Kapitel]
[<choice>K15 Die Abstimmung|Wahl der Figur|Ja oder Nein]
[Teil III kanonisch|K16 bis K23|Reihenfolge wählbar]
[Teil III ausgestiegen|Varianten der gleichen Kapitel|Variable ausgestiegen=1]
[Teil IV|K24 bis K29|Aktivierung, Oeffentlichkeit, Prozess]
[<choice>Epilog|Variante nach Variablen]
[<end>März 2030]

[<start>Titel] -> [Teil I|K1 bis K8|Haltungswahl je Kapitel]
[Teil I|K1 bis K8|Haltungswahl je Kapitel] -> [<choice>K15 Die Abstimmung|Wahl der Figur|Ja oder Nein]
[<choice>K15 Die Abstimmung|Wahl der Figur|Ja oder Nein] -> [Teil III kanonisch|K16 bis K23|Reihenfolge wählbar]
[<choice>K15 Die Abstimmung|Wahl der Figur|Ja oder Nein] -> [Teil III ausgestiegen|Varianten der gleichen Kapitel|Variable ausgestiegen=1]
[Teil III kanonisch|K16 bis K23|Reihenfolge wählbar] -> [Teil IV|K24 bis K29|Aktivierung, Oeffentlichkeit, Prozess]
[Teil III ausgestiegen|Varianten der gleichen Kapitel|Variable ausgestiegen=1] -> [Teil IV|K24 bis K29|Aktivierung, Oeffentlichkeit, Prozess]
[Teil IV|K24 bis K29|Aktivierung, Oeffentlichkeit, Prozess] -> [<choice>Epilog|Variante nach Variablen]
[<choice>Epilog|Variante nach Variablen] -> [<end>März 2030]
```

### 9.3 Variablen

Klein halten, sonst explodiert die Kombinatorik:

| Variable | Bereich | Gesetzt durch | Wirkt auf |
|---|---|---|---|
| `entschlossenheit` | 0 bis 8 | Haltungswahl Sarah, Lena | Tonfall in K22, K24, Epilog |
| `vorsicht` | 0 bis 8 | Haltungswahl Jamal, Michael | Schwere von K21 (Toms Fehler), K23 |
| `zusammenhalt` | 0 bis 8 | Haltungswahl Kat, Tom | Epilog, Schlussbild |
| `figur` | Name | K15 | Wessen Abstimmung der Spieler spricht |
| `ausgestiegen` | 0 oder 1 | K15 | Varianten in Teil III und IV |
| `tom_gestanden` | 0 oder 1 | K21 | K23, K28 (Prozess) |

Textvarianten entstehen im twee direkt:
`{if entschlossenheit>5 "Sie zögerte keine Sekunde." else "Sie zögerte." end}`

### 9.4 Kapitel-zu-Passagen-Landkarte

Aus den Kapitelmetadaten (POV, Datum, Ort):

| K | POV | Zeit | Ort / Hintergrund | Rolle im Spiel |
|---|---|---|---|---|
| 1 | Sarah | Jan 2026 | `sarah-buero` | Einstieg, erste Haltungswahl |
| 2 | Jamal | Mrz 2026 | `innovation-lab` | Figureneinführung |
| 3 | Michael | Apr 2026 | `michael-buero` | Figureneinführung |
| 4 | Kat | Jun 2026 | `kats-wg`, `bri-akademie` | Figureneinführung |
| 5 | Lena | Sep 2026 | `lena-buero`, `cafe-bonn` | zwei Passagen (Ortswechsel) |
| 6 | Tom | Dez 2026 | `innovation-lab`, `ccc-halle`, `konferenzraum` | drei Passagen |
| 7 | Sarah | Mrz 2027 | `konferenzraum` | Projektablehnung, Wendepunkt |
| 8 | Michael | Jun 2027 | `konferenzraum` | Uebergang zu Teil II |
| 9 bis 14 | je Figur | Sep 2027 | Wohnungen, Büros, Görlitz | sechs Vorbereitungsszenen, Reihenfolge wählbar |
| 15 | Alle | 16.09.2027 | `sarahs-wohnung` + `videokonferenz` | **Die Abstimmung**, echte Verzweigung |
| 16 | Sarah | Okt 2027 | `sarah-buero` | erste gefälschte Unterschrift |
| 17 | Jamal | Jan 2028 | `innovation-lab` | Architektur |
| 18 | Kat | Apr 2028 | `nairobi-hub` | Hub-Aufbau |
| 19 | Michael | Jul 2028 | `michael-buero` | Zweifel |
| 20 | Lena | Okt 2028 | `lena-buero` | Beinahe-Entdeckung |
| 21 | Tom | Jan 2029 | `innovation-lab` | **Toms Fehler**, Wahl: gestehen oder schweigen |
| 22 | Sarah | Apr 2029 | `sarah-buero` | Konfrontation |
| 23 | Michael | Jun 2029 | `michael-buero` | Entdeckung durch Dr. Hartmann |
| 24 | Sarah | Jul 2029 | `sarahs-wohnung` | Aktivierung, Höhepunkt |
| 25 | Jamal | Aug 2029 | `innovation-lab` | Das Netzwerk lebt |
| 26 | Kat | Sep 2029 | `nairobi-hub` | Hubs senden |
| 27 | Lena | Okt 2029 | `pressekonferenz` | Oeffentlichkeit |
| 28 | Tom | Nov 2029 | `landgericht` | Konsequenzen |
| 29 | Michael | Dez 2029 | `bad-godesberg` | Vermächtnis |
| 30 | Alle | Mrz 2030 | `bad-godesberg`, BRI | Epilog, Variante nach Variablen |

---

## 10. Verzeichnisse, Build und Test

```
game/
  lil/      vn.lil (Engine) + vn_test.lil
  data/     szenen.twee, emotes.csv, orte.csv, art/*.gif
  build/    build_vn.lil + erzeugte Artefakte
tools/      portraits.py, ink.py (vorhanden), szenen.py, render_art.py,
            kapitel_zu_twee.py
plans/      dieser Plan
```

```sh
uv run tools/render_art.py        # SVG nach GIF, alle Figuren und Orte
lilt game/build/build_vn.lil      # von der Repo-Wurzel aus
make watch                        # Neubau bei jeder Datenänderung (entr)
```

Erzeugt `game/build/netzwerk.deck` (in Decker öffnen) und `netzwerk.html`
(eigenständig im Browser). Wie in zelda-network gilt: die interaktive
Decker-App kann Dateien nicht selbst nachladen, das Deck muss nach jedem Bau neu
geöffnet werden.

### Tests

Was sich headless prüfen lässt, ist genau das, was in einer datengetriebenen
Geschichte kaputtgeht:

1. **Graphprüfung.** Jedes `[[...->ziel]]` zeigt auf eine existierende Passage,
   jede Passage ist von `start` aus erreichbar, keine Sackgasse ohne Links außer
   den markierten Enden.
2. **Kommandoprüfung.** Jedes `!show <puppe> <emote> <pos>` nennt eine Puppe mit
   Figurenblatt, ein dort vorhandenes Emote-Canvas und eine gültige Position
   (die 9 Bühnenfelder, die `off*`-Felder oder ein Widget der Bühnenkarte).
   Jedes `!bg <name>` nennt ein vorhandenes Hintergrund-Canvas.
3. **Renderprüfung.** `twee.render[]` über **alle** Passagen mit einem
   Standard-Variablensatz, damit ein Tippfehler in einem `{lil}`-Fragment beim
   Bauen auffällt und nicht erst im Spiel.
4. **Skript-Gegenlesen.** Wie in zelda-network: den erzeugten Skripttext per
   `print[widget.script]` gegenlesen, nicht nur "stürzt nicht ab" prüfen.

**Grenze:** `dd.say[]` und `dd.ask[]` warten auf echte Eingaben und lassen sich
mit `lilt` nicht fälschen. Der eigentliche Durchlauf bleibt manueller Test in
Decker. Deshalb ist Punkt 3 wichtig -- er fängt den Großteil dessen ab, was
sonst erst dort auffiele.

---

## 11. Meilensteine

| M | Ergebnis | Enthält |
|---|---|---|
| M0 | **erledigt** | Spikes: `twee.render`-Struktur, Kommando-Durchreichung, Modulkopie, SVG-nach-GIF mit Pattern 0/1, `%J`-Rundlauf |
| M1 | **erledigt** | `game/lil/vn.lil` (Engine als Deck-Skript), `game/build/build_vn.lil` (Bau samt Datenprüfung), `game/lil/vn_test.lil` (kopfloser Durchlauf), `game/data/szenen.twee` (Kapitel 1 mit zwei Entscheidungen), Titel-, Hinweis-, Bühnen-, Daten- und sechs Figurenkarten, `Makefile`. Erzeugt `netzwerk.deck` und `netzwerk.html`. Offen: der Sichttest in Decker selbst |
| M2 | **erledigt** | `game/data/emotes.csv`, `tools/portraits.py` umgebaut (Gesichtsgeometrie in `GEO`, Emote-Werte aus der Tabelle), `tools/render_art.py`, 84 Zeichnungen in 240x312, sechs Figurenblätter im Deck, Blinzel- und Sprechbilder vorhanden. Offen: Blinzeln und Sprechanimation in Decker in Bewegung sehen |
| M3 | **erledigt** | Kapitelindex aus den Passagen-Metadaten, Titelkarte mit Fortschritt, Weiterspielen (springt bei fehlendem oder beendetem Stand auf Anfang), Sprecherableitung aus dem Text, eigener Erzählerstil ohne Mundbewegung, Stimmung und Tempo als Kommandos. 12 Testgruppen, alle grün |
| M4 | **erledigt** | Kapitel 1 bis 8 als `szenen.twee`, 43 Passagen, acht Haltungswahlen (je eine pro Kapitel), Kapitelindex, Ortsmarken statt Hintergrundbildern |
| M5 | **erledigt** | Teil II vollständig: Übersichtskarte `t2-runde` mit frei wählbarer Reihenfolge, Kapitel 9 bis 14 als sechs innere Kapitel, Kapitel 15 mit Figurenwahl und Ja/Nein-Verzweigung. 90 Passagen, 6.400 Wörter Spieltext |
| M6 | **erledigt** | Kapitel 16 bis 30 als lineare Kette, Toms folgenreiche Entscheidung in Kapitel 21, sieben `ausgestiegen`- und fünf `tom_gestanden`-Varianten, Epilog nach Haltungszählern. Gesamt: 166 Passagen, 32 Entscheidungspunkte, 12.100 Wörter Spieltext |
| M7 | **erledigt** | 18 Hintergründe in `tools/szenen.py` nach den Urmel-Vorlagen, deckende Figurensilhouetten aus dem Generator, `tools/szenenbild.py` für Beispielszenen, Handbuch in `handbuch/` als HTML, EPUB und PDF. Offen: Töne und Übergänge |

M1 bis M3 sind Technik und voneinander abhängig. M4 bis M6 sind Schreibarbeit
und laufen danach parallel zu M7.

### Das Handbuch

`handbuch/` folgt mechanisch der Vorlage aus `zelda-network/handbuch`:
AsciiDoc-Quellen in `src/`, Bau über Docker in `build/`, Ausgabe nach
`output/` als HTML, EPUB und PDF. Zehn Kapitel von der Einleitung über
Architektur, Datenformat, Bilderzeugung und Handlung bis zu Lil und Glossar,
mit Beispielszenen aus `tools/szenenbild.py` und den nomnoml-Diagrammen
dieses Plans.

Eine Abweichung von der Vorlage war nötig: das HTML-Ziel bekommt
`-a data-uri`, sonst verweist asciidoctor relativ auf das Quellverzeichnis
und die fertige Datei in `output/` zeigt keine Bilder mehr, sobald man sie
irgendwohin kopiert.

### Was M1 tatsächlich gebracht hat

Der kopflose Test (`make test`) fährt die Engine mit gefälschter Umgebung: die
Karten werden zu verschachtelten Keystores (die sind veränderbar, anders als
Lils Dictionaries), `dd` und `pt` zu Attrappen. Die Attrappe von `dd.say[]`
bildet die Kommandoerkennung des echten Moduls nach. Damit läuft ein
vollständiger Durchlauf einschließlich Auswahl, Variablen, bedingtem Text und
Speichern, und die drei Wege durch Kapitel 1 werden einzeln geprüft.

Der Bau (`make deck`) prüft die Daten mit und bricht ab bei: fehlendem
Sprungziel, unbekannter Puppe, unbekannter Bühnenposition, unbekanntem
Kommando und Skripten, die nicht parsen. Ein fehlender Hintergrund ist nur eine
Warnung (die Bilder kommen erst in M7), und ein noch nicht gezeichnetes Emote
wird als Platzhalter aus `neutral` erzeugt, damit das Deck vor M2 spielbar
bleibt. Die Skriptprüfung nutzt aus, dass `eval[]` Parserfehler im Feld
`error` meldet statt zu werfen; Decker selbst ignoriert ein kaputtes Skript
stillschweigend, der Knopf tut dann einfach nichts. Gegengeprüft mit einem
absichtlich eingebauten Syntaxfehler.

Die Prüfung der Bühnenpositionen ist kein Luxus: `pt` fällt bei einem
unbekannten Positionsnamen still auf `bottom` zurück (`get_pos` in dessen
Modulquelltext). Ein Tippfehler wäre sonst nur als leicht falsch stehende
Figur sichtbar.

### Was M3 gebracht hat, und was der erste Lauf in Decker zeigte

Drei Rückmeldungen aus dem ersten echten Durchlauf haben mehr geändert als der
geplante Funktionsumfang:

1. **Die Ortsmarke stand unter der Menüleiste.** Decker belegt fest die
   obersten 16 Pixel der Karte (`int menu=16` in `extern/decker/c/dom.h`), und
   in einem gesperrten Deck werden sie wieder sichtbar. Alles, was oben stehen
   soll, beginnt deshalb unterhalb davon.
2. **Die Leerlaufanimation `!anim ... bob` irritiert** und ist wieder raus. Sie
   ist in einer ruhigen, dialoglastigen Erzählung Unruhe ohne Aussage. Wenn
   überhaupt, dann gezielt an einzelnen Stellen, nie als Grundzustand.
3. **Erzähltext wurde mitgesprochen.** Das führte zur Sprecherableitung aus dem
   Text (Abschnitt 5.1) und damit nebenbei zum Wegfall aller `!talk`-Kommandos:
   der Sprecher stand ohnehin schon im Text, jetzt gibt es nur noch diese eine
   Quelle statt zweier, die auseinanderlaufen können.

**Stimmung und Tempo stehen in Feldern auf der Bühne, nicht in Variablen.** Ein
Deck-Skript wird bei *jedem* Ereignis neu ausgeführt, eine Skriptvariable
überlebt also keine einzige Dialogbox. Da der Sprecherstil ohnehin pro Absatz
neu gesetzt wird, hätte ein einmaliges `dd.style` aus `!dunkel` auch nichts
genützt: die Kommandos schreiben deshalb nur den Zustand, und den Stil baut die
Engine bei jedem Absatz frisch aus Stimmung, Tempo und Sprecher zusammen.

---

## 12. Risiken und offene Fragen

**Technisch, geklärt:** Modulkomposition, rtext-Struktur, Variablen, Grafik- und
Speicherpipeline (Abschnitt 2).

**Technisch, in M1 geklärt:**

- Die Frage, ob `dd.say[]` `!`-Zeilen auch aus `twee.render[]`-Rich-Text als
  Kommando erkennt, ist beantwortet, und zwar ohne Decker: der Modulquelltext
  (`deck.modules.dd.script`) zeigt es direkt.

  ```lil
  module.say:on say text do
   text:fmt @ rtext.split["\n\n" text]
   each seg i in text
    t:rtext.string[seg]
    if t[0]~"!"
     host.card.event["command" (1 drop t)]
  ```

  `dd.say[]` splittet jeden Rich Text an Leerzeilen und prüft nur das erste
  Zeichen. Die Herkunft ist egal. Dabei fiel aber eine Falle auf, die die
  Dokumentation nicht erwähnt: geprüft wird **ausschließlich das allererste
  Zeichen** des Absatzes. Ein Lil-Fragment davor, das nichts ausgibt (etwa
  `{vorsicht:vorsicht+1 ""}`), hinterlässt einen Zeilenumbruch, und die
  Regieanweisung dahinter wäre stillschweigend zu Fließtext geworden. Die
  Engine erkennt Kommandos deshalb selbst (`vn_prosa`, mit Abschneiden
  führender Leerräume) und reicht sie an `command[]` weiter, statt sich auf
  `dd` zu verlassen. Das ist zugleich die Ausweichlösung, die hier vorgesehen
  war.
- Die Sprechanimation braucht `dd`s `.speed` ungleich 0, also Wort-für-Wort
  aufgebauten Text. Das ist eine Stilentscheidung: mit Sprechanimation und
  langsamem Text, oder ohne beides. Vorschlag: `speed:2` als Standard, per
  `!schnell` abschaltbar.

**Inhaltlich:**

- Die Adaption ist der größte Posten, nicht die Technik. Prosa in Dialog
  auflösen, ohne die Innensicht zu verlieren, die die Novelle trägt (Kapitel
  sind durchgehend personal erzählt).
- Sechs POV-Figuren und keine Spielerfigur. Die Visual Novel wechselt die
  Perspektive wie die Novelle. Der Spieler entscheidet also mal für Sarah, mal
  für Jamal. Das ist ungewöhnlich, aber die einzige ehrliche Umsetzung dieser
  Vorlage. Alternative wäre eine erfundene siebte Figur als Spielerfigur -- das
  wäre eine andere Geschichte und ist hier nicht vorgeschlagen.
- Jamals Wohnort, **entschieden**: Die Novelle widerspricht sich selbst.
  Kapitel 2 (März 2026) nennt "seiner Wohnung in Bonn-Beuel", Kapitel 10
  (September 2027) "Einzimmerwohnung in Neukölln". Festgelegt ist
  **Bonn-Beuel**, passend zu Jamals Arbeitsplatz im Bonner Innovation Lab.
  Das Personenblatt bleibt damit unverändert richtig. Bei der Adaption von
  Kapitel 10 wird Neukölln zu Bonn-Beuel; die Novelle selbst bleibt
  unangetastet. Es braucht nur einen Hintergrund `jamals-wohnung`.
- Nebenfiguren ohne Portrait (Dr. Hartmann, Frau Brandt, Claudia, Lisa, Alex,
  Aisha, Intendantin Bergmann). Vorschlag: bleiben Stimmen ohne Puppe. Wenn
  Dr. Hartmann als Gegenspieler in K22 und K23 mehr Gewicht braucht, wäre er
  die einzige lohnende siebte Zeichnung.

**Rechtlich:** Die Novelle ist anonymisiert und steht unter CC BY 4.0. Die
Visual Novel erbt beides. Der rechtliche Hinweis aus der Novelle gehört
als eigene Karte hinter die Titelkarte, wortgleich.

---

## 13. Vor der ersten Zeile Lil

Die sechs Lil-Fallstricke gelten hier
unverändert und sind Pflichtlektüre. Die für dieses Projekt gefährlichsten:

- Keine Operator-Priorität: Tupel nur aus fertig berechneten Variablen bauen.
- Funktionsaufrufe vor einem Komma in einer Liste immer klammern, sonst
  verschluckt der Aufruf den Rest der Liste ohne Fehlermeldung.
- `each v k i in dict` liefert zuerst den **Wert**, dann den Schlüssel. Beim
  Durchlaufen von `deck.cards` und `card.widgets` führt die falsche Reihenfolge
  zu leeren Namen und einer stillen Fehlsuche (genau das ist beim Erstellen
  dieses Plans passiert).
- In `where`-Klauseln `=` statt `~`, sonst filtert die Abfrage still nicht.
- Verkettung ist `"" fuse (a,b,c)`. `"praefix" fuse (a,b)` ergibt `a+"praefix"+b`
  und beim Pfadbau einen gültigen, aber falschen String.
- Ein Modul-`.value`, das mit einer nackten Tabelle endet, wird zu einem flachen
  Spalten-Dict gecastet. Tabelle vorher in ein Dict-Feld einbetten.
- **Zuweisungen in einer Funktion sind nicht automatisch lokal.** Ohne
  `local` schreibt `x:...` in den umgebenden Gültigkeitsbereich. Eine
  Prüffunktion mit einer Zeile `namen:()` hat so die globale Liste der
  Passagennamen überschrieben, woraufhin der Bau plötzlich *jedes*
  Sprungziel als fehlend meldete. Das Symptom zeigt dabei nicht im
  Entferntesten auf die Ursache. Hilfsvariablen in Funktionen deshalb immer
  mit `local` deklarieren.

### Ein fehlerhaftes Lil-Fragment verschwindet spurlos

Ply führt `{...}`-Fragmente aus und schluckt Fehler stillschweigend. Ein `if`
ohne `end` rendert einfach zu nichts: die bedingte Textstelle fehlt im Spiel,
ohne Meldung, ohne Lücke, ohne Hinweis. Bei über dreissig Fragmenten in
166 Passagen ist das eine unangenehme Fehlerklasse, und sie ist mir selbst im
Epilog passiert.

`build_vn.lil` schneidet deshalb jedes Fragment mit einem Klammer-Tiefenzähler
heraus und wertet es einzeln mit `eval[]` aus, das Syntaxfehler im Feld
`error` meldet, statt sie zu verschlucken.

### Ein Bindestrich zerstört Ply-Links

Ein Bindestrich in der **Beschriftung** eines Links löscht den Link spurlos:
statt eines Auswahlknopfes erscheint der rohe Text
`[[Die Chaos-Leute verstehen OpSec.->k06-vertrauen]]` im Spiel. Im
**Sprungziel** ist er dagegen harmlos. Nachgemessen mit Minimalbeispielen:

| Passage | Ergebnis |
|---|---|
| `[[Chaosleute->x]]` | 1 Link |
| `[[Chaos-Leute->x]]` | 0 Links |
| `[[Erster->k06-vertrauen]]` | 1 Link |

`build_vn.lil` bricht deshalb ab, wenn eine Link-Beschriftung einen
Bindestrich enthält. Beschriftungen also umformulieren: aus "Wir nennen es ein
Resilienz-Projekt." wird "Wir nennen es ein Projekt für Resilienz."

### Die Abstimmung, und was der Spieler wirklich entscheidet

Teil II hat zwei Strukturen, die es sonst nirgends gibt.

**Die Übersichtskarte `t2-runde`.** Die sechs Vorbereitungskapitel spielen
alle am selben Abend, jede Figur für sich. Der Spieler wählt die Reihenfolge.
Umgesetzt ist das mit bedingten Links: jedes Kapitel setzt beim Verlassen ein
Flag (`g09` bis `g14`) und kehrt zur Übersicht zurück, und die Übersicht zeigt
nur die noch ungesehenen an.

```
{if g09 "" else rtext.make["Sarah schreibt die Einladung." "" "k09-einladung"] end}
{gesamt:g09+g10+g11+g12+g13+g14 if 6~gesamt rtext.make["Der 16. September, 20 Uhr." "" "k15-abstimmung"] else "" end}
```

`rtext.make[text schrift ziel]` erzeugt eine Zeile mit Sprungziel, die die
Engine genau wie einen `[[...]]`-Link behandelt. Erst wenn alle sechs Flags
stehen, erscheint der Weg zur Abstimmung.

**Der Ausstieg statt des Vetos.** Die Novelle verlangt Einstimmigkeit: "Wenn
auch nur einer Nein sagt, ist das Projekt vorbei." Der Spieler wählt erst, für
welche der sechs Figuren er den Zettel schreibt (`figur`), dann Ja oder Nein.

Ein Nein könnte die Geschichte hier beenden, und genau das soll es nicht: die
Novelle bleibt kanonisch. Gelöst ist das nicht durch Ignorieren der Wahl,
sondern indem die Gruppe ihre eigene Regel unter Druck neu verhandelt. Die
Figur des Spielers legt kein Veto gegen das Projekt ein, sondern gegen die
eigene Beteiligung. Fünf machen weiter, einer geht und nimmt alles mit, was er
weiß, was Michael als das größere Risiko benennt. `ausgestiegen` bleibt für
den Rest der Geschichte gesetzt und färbt Schwur, Teil III und den Epilog.

Das ist die einzige Stelle, an der eine Spielerentscheidung den Bestand der
Gruppe ändert, und sie kostet etwas, ohne die Handlung zu brechen.

### Zwei Figuren, mehr passen nicht

Puppeteers Bühnenpositionen fallen auf drei x-Spalten zusammen: `left`,
`centerleft` und `topleft` liegen alle bei x=0, `center`, `top` und `bottom`
bei (B-P)/2, `right`, `centerright` und `topright` bei B-P. Die Varianten
einer Spalte unterscheiden sich nur in der Höhe, und eine Puppe ist mit 624
von 684 Pixeln fast so hoch wie die Karte.

Bei 480 Pixel Puppenbreite auf 1024 Pixel Karte überlappen benachbarte
Spalten um 208 Pixel. Auf die Bühne passen deshalb **genau zwei Figuren, eine
links und eine rechts**. Sechs Figuren in einer Konferenzszene ergeben
übereinanderliegende Köpfe, und zwar ohne jede Fehlermeldung.

Ensemble-Szenen werden deshalb so inszeniert, wie es Visual Novels ohnehin
tun: sichtbar sind der Sprecher und sein Gegenüber, gewechselt wird mit
`!hide` und einem neuen `!show`. Für Runden, in denen jeder einen Satz sagt,
steht jeweils nur eine Figur in der Mitte.

`build_vn.lil` prüft das mit: es simuliert Sichtbarkeit und Position aller
Puppen durch die Passage und meldet jede Überlappung. Geprüft wird nach jedem
Kommando**block**, nicht nach jedem einzelnen Kommando, denn innerhalb eines
Blocks laufen die Anweisungen ohne Pause durch und ein Zwischenzustand ist nie
zu sehen. `!hide` macht dabei nur unsichtbar und merkt sich die Position; ein
späteres `!show` ohne Positionsangabe zeigt die Puppe wieder am selben Ort.
