#!/usr/bin/env python3
"""Erzeugt aus den AsciiDoc-Kapiteln der Novelle "Das Netzwerk" ein Twee-3/Ply-
Gerüst für Decker.

Quelle (nur lesend):  ../Novelle_Zukunft-der-DW/src/02-teil-1 .. 06-epilog
Ziel:                 game/data/szenen_geruest.twee

WICHTIG: Dieses Skript schreibt ausschließlich szenen_geruest.twee, niemals
szenen.twee. Das Gerüst ist ein einmaliger Startpunkt zum Weiterschreiben von
Hand (siehe plans/graphic-novel-plan.md, Abschnitt 5.3) -- kein wiederholbarer
Build-Schritt für die eigentliche Szenendatei.

Aufruf:
  python3 tools/kapitel_zu_twee.py            # alle 30 Kapitel
  python3 tools/kapitel_zu_twee.py 01 15      # nur diese Kapitel (das Gerüst
                                               # enthält dann auch nur diese)
"""

import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Pfade
# ---------------------------------------------------------------------------

TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
SRC_ROOT = (REPO_ROOT / ".." / "Novelle_Zukunft-der-DW" / "src").resolve()
OUT_PATH = REPO_ROOT / "game" / "data" / "szenen_geruest.twee"

# Reihenfolge der Quellordner und ihr teil-Tag (siehe Aufgabenstellung: der
# teil-Tag kommt aus dem Ordnernamen, nicht aus dem :part:-Attribut, weil
# mehrere Kapitel dieses Attribut gar nicht im Kopf tragen).
TEIL_DIRS = [
    ("02-teil-1", "teil-1"),
    ("03-teil-2", "teil-2"),
    ("04-teil-3", "teil-3"),
    ("05-teil-4", "teil-4"),
    ("06-epilog", "epilog"),
]

# ---------------------------------------------------------------------------
# Die vier Kapitel ohne strukturierte Kopf-Attribute (01, 07, 08, 30)
# ---------------------------------------------------------------------------

FALLBACK = {
    1: {"pov": "sarah", "monat": "Januar", "jahr": 2026, "stadt": "Bonn", "bg": "sarah-buero"},
    7: {"pov": "sarah", "monat": "März", "jahr": 2027, "stadt": "Bonn", "bg": "konferenzraum"},
    8: {"pov": "michael", "monat": "Juni", "jahr": 2027, "stadt": "Bonn", "bg": "konferenzraum"},
    30: {"pov": "alle", "monat": "März", "jahr": 2030, "stadt": "Bonn", "bg": "bad-godesberg"},
}

MONATE = {
    "Januar": 1, "Februar": 2, "März": 3, "April": 4, "Mai": 5, "Juni": 6,
    "Juli": 7, "August": 8, "September": 9, "Oktober": 10, "November": 11,
    "Dezember": 12,
}

# POV-Erkennung: die sechs Hauptfiguren plus "Alle". Reihenfolge ist egal,
# weil alle Formen (Katharina, Kat, "Kat") auf denselben Tag abgebildet werden.
POV_NAMEN = [
    ("Alle", "alle"),
    ("Sarah", "sarah"),
    ("Jamal", "jamal"),
    ("Michael", "michael"),
    ("Katharina", "kat"),
    ("Kat", "kat"),
    ("Lena", "lena"),
    ("Tom", "tom"),
]

# Ort-Feld (oder ersatzweise :location:) -> Hintergrund. Reihenfolge ist eine
# Priorität: speziellere Stichworte zuerst, damit z.B. "Görlitz, Elternhaus
# der Familie Müller" nicht fälschlich als Toms Elternhaus erkannt wird.
ORT_ZU_BG = [
    ("sarahs-wohnung", ["Sarahs Wohnung"]),
    ("jamals-wohnung", ["Jamals Wohnung"]),
    ("sarah-buero", ["Sarahs Büro", "BRI-Hochhaus"]),
    ("michael-buero", ["Michaels Büro", "Research & Cooperations", "Research and Cooperations"]),
    ("lena-buero", ["Lenas Büro", "BRI-Redaktion"]),
    ("bri-akademie", ["BRI Akademie"]),
    ("innovation-lab", ["BRI Innovation Lab", "Innovation Lab"]),
    ("cafe-bonn", ["Café"]),
    ("ccc-halle", ["37C3", "Chaos Communication Congress", "Hamburg"]),
    ("goerlitz-kinderzimmer", ["Görlitz"]),
    ("toms-elternhaus", ["Toms Elternhaus"]),
    ("toms-wg", ["Toms WG"]),
    ("nairobi-hub", ["Nairobi"]),
    ("landgericht", ["Landgericht"]),
    ("bad-godesberg", ["Bad Godesberg"]),
    ("konferenzraum", ["Konferenzraum"]),
]

# Jeder Hintergrund hat eine kanonische Stadt (für !zeit). Quelle: das
# jeweilige *Ort:*-Feld selbst bzw. Abschnitt 8 des Plans. bad-godesberg
# folgt der Vorgabe aus der Fallback-Tabelle der Aufgabe (Kapitel 30: Bonn).
BG_ZU_STADT = {
    "sarah-buero": "Bonn",
    "innovation-lab": "Bonn",
    "michael-buero": "Bonn",
    "bri-akademie": "Bonn",
    "cafe-bonn": "Bonn",
    "lena-buero": "Bonn",
    "ccc-halle": "Hamburg",
    "toms-elternhaus": "München",
    "konferenzraum": "Bonn",
    "sarahs-wohnung": "Bonn",
    "jamals-wohnung": "Berlin",
    "goerlitz-kinderzimmer": "Görlitz",
    "toms-wg": "Berlin",
    "nairobi-hub": "Nairobi",
    "pressekonferenz": "Berlin",
    "landgericht": "Berlin",
    "bad-godesberg": "Bonn",
}

# Wenn kein !bg gefunden wird, versuchen wir wenigstens eine Stadt aus dem
# Rohtext des Ort-Feldes zu lesen, damit !zeit nicht ganz leer bleibt.
STADT_STICHWORTE = [
    "Nairobi", "Görlitz", "Bad Godesberg", "Hamburg", "München",
    "Berlin", "Bonn", "Köln",
]

# ---------------------------------------------------------------------------
# Sprecher-Erkennung für die konservative Dialogumwandlung
# ---------------------------------------------------------------------------

# Die sechs Hauptfiguren (Kat/Katharina auf denselben Anzeigenamen) sowie
# Nebenfiguren, die im Text als Sprecher mit "Verb Name" auftreten (siehe
# plans/graphic-novel-plan.md Abschnitt 5.1: Nebenfiguren ohne Portrait
# sprechen ebenfalls per Präfix).
SPRECHER_NAMEN = {
    "Sarah": "Sarah", "Jamal": "Jamal", "Michael": "Michael",
    "Kat": "Kat", "Katharina": "Kat", "Lena": "Lena", "Tom": "Tom",
    "Martina": "Martina", "Hartmann": "Hartmann", "Brandt": "Brandt",
    "Sandra": "Sandra", "Claudia": "Claudia", "Lisa": "Lisa",
    "Alex": "Alex", "Aisha": "Aisha", "Weidmann": "Weidmann",
    "Joseph": "Joseph", "Markus": "Markus", "Rajesh": "Rajesh",
    "Nadia": "Nadia",
}

REDEVERBEN = [
    "sagte", "fragte", "flüsterte", "murmelte", "erwiderte", "rief",
    "wiederholte", "antwortete", "meinte", "betonte", "korrigierte",
    "unterbrach", "schrie", "seufzte", "vollendete", "erklärte",
    "bestätigte", "begann", "entgegnete",
]

_NAMEN_ALT = "|".join(re.escape(n) for n in SPRECHER_NAMEN)
_VERBEN_ALT = "|".join(REDEVERBEN)

# "sagte Sarah" (häufigster Fall) und als Rückfallmuster "Sarah sagte".
ATTRIB_VERB_NAME = re.compile(rf"\b(?:{_VERBEN_ALT})\s+({_NAMEN_ALT})\b")
ATTRIB_NAME_VERB = re.compile(rf"\b({_NAMEN_ALT})\s+(?:{_VERBEN_ALT})\b")

# 'Sarah: "Ja."' oder '**Sarah:** "Ja."' (kommt nur in Kapitel 30 vor, ist
# aber ein eindeutiges Muster: der Sprecher steht schon als Präfix da, die
# Anführungszeichen sind nur noch AsciiDoc-Zierde).
SPRECHER_PRAEFIX_ZITAT = re.compile(
    rf'^\*{{0,2}}({_NAMEN_ALT})\*{{0,2}}:\*{{0,2}}\s*"([^"]+)"\s*$'
)

# ---------------------------------------------------------------------------
# ASCII-Transliteration für Bezeichner (Passagennamen bleiben ASCII)
# ---------------------------------------------------------------------------

_TRANSLIT = str.maketrans({
    "ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
    "Ä": "Ae", "Ö": "Oe", "Ü": "Ue",
})


def ascii_bezeichner(text):
    text = text.translate(_TRANSLIT)
    text = re.sub(r"[^A-Za-z0-9-]", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text.lower()


# ---------------------------------------------------------------------------
# Kapitel einsammeln
# ---------------------------------------------------------------------------

class Kapitel:
    def __init__(self, nummer, pfad, teil_tag):
        self.nummer = nummer
        self.pfad = pfad
        self.teil_tag = teil_tag
        stem = pfad.stem  # z.B. "01-sarah-vision"
        rest = re.sub(r"^\d+-", "", stem)
        self.passage_name = f"k{nummer:02d}-{ascii_bezeichner(rest)}"
        self.titel = self.titel_lesen()

    def titel_lesen(self):
        """Kapitelueberschrift "= Kapitel 1: Sarah - Die Vision" als Titel.

        Der Titel wandert als Twee-Metadatum in die Passage. Die Engine
        baut daraus den Kapitelindex, und Twine behaelt die Angabe beim
        Bearbeiten bei."""
        for zeile in self.pfad.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^=[^=]\s*(.+?)\s*$", zeile)
            if m:
                return m.group(1)
        return f"Kapitel {self.nummer}"


def kapitel_einsammeln():
    kapitel = []
    for ordner, teil_tag in TEIL_DIRS:
        for pfad in sorted((SRC_ROOT / ordner).glob("*.adoc")):
            m = re.match(r"^(\d+)-", pfad.stem)
            if not m:
                continue
            kapitel.append(Kapitel(int(m.group(1)), pfad, teil_tag))
    kapitel.sort(key=lambda k: k.nummer)
    return kapitel


# ---------------------------------------------------------------------------
# AsciiDoc-Kopf auslesen (:pov:, :date:, *Ort:*, :location:)
# ---------------------------------------------------------------------------

def kopf_lesen(text):
    pov = None
    date = None
    location = None
    ort = None
    for zeile in text.splitlines():
        m = re.match(r"^:pov:\s*(.+)$", zeile)
        if m:
            pov = m.group(1).strip()
        m = re.match(r"^:date:\s*(.+)$", zeile)
        if m:
            date = m.group(1).strip()
        m = re.match(r"^:location:\s*(.+)$", zeile)
        if m:
            location = m.group(1).strip()
        m = re.match(r"^\*Ort:\*\s*(.+?)\s*\+?\s*$", zeile)
        if m and ort is None:
            ort = m.group(1).strip()
    return pov, date, location, ort


def pov_tag_ermitteln(pov_text):
    for stichwort, tag in POV_NAMEN:
        if stichwort in pov_text:
            return tag
    return None


def datum_ermitteln(date_text):
    """'März 2026' -> (3, 2026)."""
    m = re.match(r"^(\S+)\s+(\d{4})$", date_text.strip())
    if not m:
        return None
    monat = MONATE.get(m.group(1))
    if monat is None:
        return None
    return monat, int(m.group(2))


# Kapitel, deren Ortsangabe zu unscharf ist ("BRI Bonn", "Köln und Bonn").
# Die Auflösung steht in plans/graphic-novel-plan.md, Abschnitt 9.4, und ist
# dort aus dem Kapiteltext entschieden worden, nicht geraten.
KAPITEL_ZU_BG = {
    4: "bri-akademie",
    5: "lena-buero",
    20: "lena-buero",
    22: "sarah-buero",
    23: "michael-buero",
    26: "nairobi-hub",
}


def bg_ermitteln(ort_text, nummer):
    if nummer in KAPITEL_ZU_BG:
        return KAPITEL_ZU_BG[nummer]
    if not ort_text:
        return None
    for bg, stichworte in ORT_ZU_BG:
        for stichwort in stichworte:
            if stichwort in ort_text:
                return bg
    if nummer == 27 and "Berlin" in ort_text:
        return "pressekonferenz"
    return None


def stadt_aus_rohtext(ort_text):
    if not ort_text:
        return None
    for stadt in STADT_STICHWORTE:
        if stadt in ort_text:
            return stadt
    return None


# ---------------------------------------------------------------------------
# AsciiDoc-Aufbereitung des Fließtextes
# ---------------------------------------------------------------------------

# Diese drei Blöcke verschwinden komplett samt Inhalt: [.metadata] und
# [.chapter-info] sind Kopf-Synopsen, die in Tags und !zeit schon stecken;
# [.author-note] ist das Nachwort des Autors am Ende von Kapitel 30, also
# kein Teil der Spielhandlung.
BLOECKE_GANZ_ENTFERNEN = {".metadata", ".chapter-info", ".author-note"}


def zitat_zeile_umwandeln(zeile, stats):
    """Wandelt genau das eindeutige Muster "Zitat, Sprecherangabe" um.

    Rückgabe: (neue_zeile, ist_zitatzeile). stats["umgewandelt"] bzw.
    stats["offen"] werden dabei entsprechend hochgezählt.
    """
    # Muster 1: 'Sarah: "Ja."' -- der Sprecher steht schon als Präfix da.
    m = SPRECHER_PRAEFIX_ZITAT.match(zeile)
    if m:
        sprecher = SPRECHER_NAMEN[m.group(1)]
        text = m.group(2).strip()
        if text and text[-1] not in ".!?…":
            text += "."
        stats["umgewandelt"] += 1
        return f"{sprecher}: {text}", True

    if not zeile.startswith('"'):
        return zeile, False

    ende = zeile.find('"', 1)
    if ende == -1 or zeile.count('"') != 2:
        # Kein eindeutiges Einzel-Zitat auf dieser Zeile (mehrere
        # Anführungszeichen oder keins zum Schließen) -- unverändert lassen.
        stats["offen"] += 1
        return zeile, True

    zitat = zeile[1:ende]
    rest = zeile[ende + 1:].strip()
    if rest.startswith(","):
        rest = rest[1:].strip()

    if not rest:
        # Zeile ist nur das Zitat, keine Sprecherangabe -- nicht raten.
        stats["offen"] += 1
        return zeile, True

    treffer = ATTRIB_VERB_NAME.search(rest) or ATTRIB_NAME_VERB.search(rest)
    if not treffer:
        stats["offen"] += 1
        return zeile, True

    sprecher = SPRECHER_NAMEN[treffer.group(1)]
    text = zitat.strip()
    if text and text[-1] not in ".!?…":
        text += "."
    stats["umgewandelt"] += 1
    return f"{sprecher}: {text}", True


def zeile_aufbereiten(zeile, stats):
    # AsciiDoc-typografische Anführungszeichen "`...`" -> "..."
    zeile = zeile.replace('"`', '"').replace('`"', '"')
    # Zeilenumbruch-Marker " +" am Ende entfernt
    zeile = re.sub(r" \+$", "", zeile)
    # Kursiv _text_ -> text (Auszeichnung entfällt)
    zeile = re.sub(r"_([^_\n]+)_", r"\1", zeile)
    # Doppelsternchen-Fett **text** -> *text* (Ply-Fettschrift-Syntax)
    zeile = re.sub(r"\*\*([^*\n]+)\*\*", r"*\1*", zeile)
    # konservative Dialogumwandlung
    zeile, _ = zitat_zeile_umwandeln(zeile, stats)
    return zeile


def ist_delimiter_zeile(zeile):
    # ____ und **** sind AsciiDoc-Blockbegrenzer (Zitat/Metadaten), ---- ist
    # der Begrenzer von [source]-Blöcken, ``` der von Codezäunen, ''' und ---
    # werden im Quelltext beide als Szenentrenner benutzt.
    return zeile.strip() in ("____", "****", "----", "'''", "---", "```")


def fliesstext_erzeugen(quelltext, stats):
    zeilen = quelltext.splitlines()
    ergebnis_bloecke = []
    aktueller_block = []
    i = 0
    n = len(zeilen)

    def block_abschliessen():
        if aktueller_block:
            ergebnis_bloecke.append("\n".join(aktueller_block))
            aktueller_block.clear()

    while i < n:
        zeile = zeilen[i]
        nackt = zeile.strip()

        # Kapitelüberschrift (Level 1, "= Kapitel N: ...") komplett entfernen.
        if re.match(r"^=[^=]", nackt) or nackt == "=":
            i += 1
            continue

        # AsciiDoc-Kopfattribute (:pov:, :date:, :chapter:, :part:, :location:)
        if re.match(r"^:[A-Za-z_-]+:.*$", nackt):
            i += 1
            continue

        # Zwischenüberschriften (Level 2 und tiefer) -> eigene Zeile in
        # Sternchen, das ist Ply-Markup für die Menü-Schrift.
        m = re.match(r"^(=={1,})\s+(.*)$", nackt)
        if m:
            block_abschliessen()
            ergebnis_bloecke.append(f"*{m.group(2).strip()}*")
            i += 1
            continue

        # Blöcke, die komplett verschwinden: [.metadata], [.chapter-info],
        # [.author-note] samt Begrenzern und Inhalt.
        m = re.match(r"^\[([^\]]+)\]$", nackt)
        if m and m.group(1) in BLOECKE_GANZ_ENTFERNEN:
            i += 1
            # Begrenzerzeile (**** oder ____) überspringen und bis zur
            # schließenden Begrenzerzeile alles verwerfen.
            if i < n and ist_delimiter_zeile(zeilen[i]):
                delim = zeilen[i].strip()
                i += 1
                while i < n and zeilen[i].strip() != delim:
                    i += 1
                if i < n:
                    i += 1  # schließende Begrenzerzeile überspringen
            continue

        # Andere Blockattribute in eckigen Klammern ([quote], [.email],
        # [.document-title], [source], [.scene-break], [.whiteboard], ...):
        # nur die Attributzeile entfällt, der Inhalt bleibt erhalten.
        if m:
            i += 1
            continue

        # Reine Begrenzerzeilen (____, ****, ----, ''', ---, ```) entfallen,
        # der Inhalt dazwischen bleibt erhalten.
        if ist_delimiter_zeile(zeile):
            i += 1
            continue

        # Leerzeile trennt Absätze.
        if nackt == "":
            block_abschliessen()
            i += 1
            continue

        aktueller_block.append(zeile_aufbereiten(zeile, stats))
        i += 1

    block_abschliessen()
    absaetze = [b for b in ergebnis_bloecke if b.strip()]
    return "\n\n".join(absaetze), len(absaetze)


# ---------------------------------------------------------------------------
# Eine Kapitel-Datei zu einer Passage verarbeiten
# ---------------------------------------------------------------------------

class Ergebnis:
    pass


def kapitel_verarbeiten(kapitel):
    text = kapitel.pfad.read_text(encoding="utf-8")
    pov_text, date_text, location_text, ort_text = kopf_lesen(text)

    r = Ergebnis()
    r.kapitel = kapitel

    if kapitel.nummer in FALLBACK:
        fb = FALLBACK[kapitel.nummer]
        r.pov_tag = fb["pov"]
        r.monat, r.jahr = MONATE[fb["monat"]], fb["jahr"]
        r.monat_name = fb["monat"]
        r.bg = fb["bg"]
        r.stadt = fb["stadt"]
        r.bg_ist_todo = False
    else:
        r.pov_tag = pov_tag_ermitteln(pov_text or "") or "unbekannt"
        md = datum_ermitteln(date_text or "")
        if md:
            r.monat, r.jahr = md
            r.monat_name = [k for k, v in MONATE.items() if v == r.monat][0]
        else:
            r.monat, r.jahr, r.monat_name = None, None, "?"

        ort_quelle = ort_text or location_text or ""
        bg = bg_ermitteln(ort_quelle, kapitel.nummer)
        if bg:
            r.bg = bg
            r.stadt = BG_ZU_STADT.get(bg) or stadt_aus_rohtext(ort_quelle) or "TODO"
            r.bg_ist_todo = False
        else:
            r.bg = "TODO"
            r.stadt = stadt_aus_rohtext(ort_quelle) or "TODO"
            r.bg_ist_todo = True
        r._ort_quelle = ort_quelle

    stats = {"umgewandelt": 0, "offen": 0}
    r.fliesstext, r.absaetze = fliesstext_erzeugen(text, stats)
    r.stats = stats
    return r


# ---------------------------------------------------------------------------
# Twee-Passage bauen
# ---------------------------------------------------------------------------

def passage_bauen(r, naechste_passage):
    k = r.kapitel
    if r.jahr:
        datum_tag = f"datum-{r.jahr:04d}-{r.monat:02d}"
        tags = f"kapitel-{k.nummer:02d} {k.teil_tag} pov-{r.pov_tag} {datum_tag}"
        zeit = f"{r.monat_name} {r.jahr}, {r.stadt}"
    else:
        tags = f"kapitel-{k.nummer:02d} {k.teil_tag} pov-{r.pov_tag}"
        zeit = f"?, {r.stadt}"

    meta = json.dumps({"titel": k.titel}, ensure_ascii=False)
    zeilen = [f":: {k.passage_name} [{tags}] {meta}"]
    zeilen.append(f"!bg {r.bg}")
    zeilen.append(f"!zeit {zeit}")
    zeilen.append("")
    zeilen.append(r.fliesstext)
    if naechste_passage:
        zeilen.append("")
        zeilen.append(f"[[Weiter.->{naechste_passage}]]")
    return "\n".join(zeilen)


# ---------------------------------------------------------------------------
# Validierung: zeigen alle Links auf existierende Passagen?
# ---------------------------------------------------------------------------

LINK_RE = re.compile(r"\[\[[^\]|]*->([^\]]+)\]\]")


def links_pruefen(twee_text):
    namen = set(m.group(1) for m in re.finditer(r"^:: (\S+)", twee_text, re.MULTILINE))
    kaputt = []
    for m in LINK_RE.finditer(twee_text):
        ziel = m.group(1).strip()
        if ziel not in namen:
            kaputt.append(ziel)
    return kaputt


# ---------------------------------------------------------------------------
# Hauptprogramm
# ---------------------------------------------------------------------------

def main():
    angefragt = None
    if len(sys.argv) > 1:
        angefragt = {int(a) for a in sys.argv[1:]}

    alle_kapitel = kapitel_einsammeln()
    if len(alle_kapitel) != 30:
        print(f"Warnung: {len(alle_kapitel)} Kapitel gefunden, erwartet waren 30.")

    verarbeitet = [k for k in alle_kapitel if angefragt is None or k.nummer in angefragt]
    if not verarbeitet:
        print("Keine passenden Kapitel gefunden.")
        return 1

    nummer_zu_passage = {k.nummer: k.passage_name for k in verarbeitet}

    ergebnisse = [kapitel_verarbeiten(k) for k in verarbeitet]

    # Startpassage ist die des niedrigsten in diesem Lauf verarbeiteten
    # Kapitels -- bei einem Teillauf ohne Kapitel 1 also nicht zwangsläufig
    # k01-sarah-vision.
    start_passage = nummer_zu_passage[min(nummer_zu_passage)]

    teile = [
        ":: StoryData\n"
        '{"format": "Ply", "format-version": "1.0.0", '
        f'"start": "{start_passage}"}}',
        ":: StoryTitle\nDas Netzwerk",
    ]
    for r in ergebnisse:
        naechste = nummer_zu_passage.get(r.kapitel.nummer + 1)
        teile.append(passage_bauen(r, naechste))

    twee_text = "\n\n".join(teile) + "\n"

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(twee_text, encoding="utf-8")

    # -- Bericht ------------------------------------------------------------
    todo_faelle = []
    kopfzeile = (
        f"{'K':>2}  {'Passage':<32} {'Hintergrund':<20} {'Absätze':>8} "
        f"{'umgewandelt':>11} {'offen':>6}"
    )
    zeilen = [kopfzeile, "-" * len(kopfzeile)]
    for r in ergebnisse:
        k = r.kapitel
        zeilen.append(
            f"{k.nummer:02d}  {k.passage_name:<32} {r.bg:<20} {r.absaetze:>8} "
            f"{r.stats['umgewandelt']:>11} {r.stats['offen']:>6}"
        )
        if r.bg_ist_todo:
            todo_faelle.append((k.nummer, k.passage_name, getattr(r, "_ort_quelle", "")))

    print(f"Geschrieben: {OUT_PATH}")
    print(f"Passagen insgesamt: {len(ergebnisse) + 2} "
          f"({len(ergebnisse)} Kapitel plus StoryData plus StoryTitle)")
    print()
    print("\n".join(zeilen))

    gesamt_um = sum(r.stats["umgewandelt"] for r in ergebnisse)
    gesamt_offen = sum(r.stats["offen"] for r in ergebnisse)
    print()
    print(f"Zitatzeilen umgewandelt: {gesamt_um}, unverändert gelassen: {gesamt_offen}")

    if todo_faelle:
        print()
        print("Kapitel ohne eindeutige Hintergrund-Zuordnung (!bg TODO):")
        for nummer, passage, ort in todo_faelle:
            print(f"  Kapitel {nummer:02d} ({passage}): Ort-Text = {ort!r}")
    else:
        print()
        print("Alle Kapitel haben einen Hintergrund gefunden.")

    kaputt = links_pruefen(twee_text)
    print()
    if kaputt:
        print("Kaputte Links gefunden (Ziel existiert nicht):")
        for ziel in kaputt:
            print(f"  -> {ziel}")
        return 1
    print("Alle Links zeigen auf existierende Passagen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
