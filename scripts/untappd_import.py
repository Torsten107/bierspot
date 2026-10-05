#!/usr/bin/env python3
"""
Untappd-Export in bierspot.de einspielen.

Aufruf (im Hauptordner des Projekts):
    python3 scripts/untappd_import.py pfad/zum/untappd-export.json
    python3 scripts/untappd_import.py pfad/zum/untappd-export.csv
    python3 scripts/untappd_import.py export.json --probelauf      # zeigt nur an, schreibt nichts
    python3 scripts/untappd_import.py --stile-nachtragen           # nach Ergänzen der Stil-Zuordnung

Was das Skript macht:
- Fasst alle Check-ins desselben Biers zu einem Eintrag zusammen.
- Legt pro Bier eine Datei in content/biertests/ an, markiert als "Kurz notiert" (stufe: kurz).
- Übersetzt den Untappd-Stil über data/untappd_stile.yaml auf die eigene Stil-Liste.
- Überschreibt NIE eine vorhandene Datei. Ausführliche Tests und bereits importierte Biere bleiben unangetastet.
- Listet am Ende alle Untappd-Stile auf, für die es noch keine Zuordnung gibt.

Braucht nur Python 3, keine Zusatzpakete.
"""

import csv
import json
import re
import sys
import unicodedata
from collections import Counter, OrderedDict
from datetime import datetime
from pathlib import Path

PROJEKT = Path(__file__).resolve().parent.parent
ZIEL = PROJEKT / "content" / "biertests"
ZUORDNUNG = PROJEKT / "data" / "untappd_stile.yaml"


# ---------- Hilfsfunktionen ----------

def lies_zuordnung():
    """Liest die Einträge '- { beginnt: "...", stil: "..." }' aus data/untappd_stile.yaml."""
    regeln = []
    muster = re.compile(r'beginnt:\s*"([^"]+)"\s*,\s*stil:\s*"([^"]+)"')
    for zeile in ZUORDNUNG.read_text(encoding="utf-8").splitlines():
        zeile = zeile.strip()
        if zeile.startswith("#"):
            continue
        m = muster.search(zeile)
        if m:
            regeln.append((m.group(1).lower(), m.group(2)))
    return regeln


def ordne_stil_zu(untappd_stil, regeln):
    s = (untappd_stil or "").strip().lower()
    for anfang, stil in regeln:
        if s.startswith(anfang):
            return stil
    return None


def slug(text):
    text = text.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss"), ("ø", "oe"), ("æ", "ae"),
                 ("å", "aa"), ("œ", "oe"), ("ł", "l"), ("đ", "d"), ("&", " und ")):
        text = text.replace(a, b)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return re.sub(r"-{2,}", "-", text)[:80].strip("-") or "bier"


LAENDER = {
    "Germany": "Deutschland", "Austria": "Österreich", "Switzerland": "Schweiz",
    "Belgium": "Belgien", "Netherlands": "Niederlande", "Czech Republic": "Tschechien",
    "Czechia": "Tschechien", "Denmark": "Dänemark", "Ireland": "Irland", "Scotland": "Schottland",
    "England": "England", "United Kingdom": "Großbritannien", "United States": "USA",
    "France": "Frankreich", "Italy": "Italien", "Poland": "Polen", "Sweden": "Schweden",
    "Norway": "Norwegen", "Spain": "Spanien", "Mexico": "Mexiko", "Japan": "Japan",
}


def dateiname_fuer(brauerei, name):
    """Brauerei nur voranstellen, wenn sie nicht schon im Biernamen steckt."""
    erstes_wort = re.split(r"[\s\-]+", brauerei.strip())[0].lower() if brauerei else ""
    if not brauerei or (len(erstes_wort) > 3 and erstes_wort in name.lower()):
        return slug(name)
    return slug(f"{brauerei} {name}")


def zahl(wert):
    try:
        if wert in (None, ""):
            return None
        return float(str(wert).replace(",", "."))
    except ValueError:
        return None


def datum(wert):
    """Untappd liefert z. B. '2023-05-01 18:22:11'."""
    if not wert:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(wert)[:19], fmt)
        except ValueError:
            continue
    return None


def q(text):
    """Text sicher für YAML schreiben (JSON-Strings sind gültiges YAML)."""
    return json.dumps(text, ensure_ascii=False)


def lies_export(pfad):
    if pfad.suffix.lower() == ".csv":
        with pfad.open(encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    daten = json.loads(pfad.read_text(encoding="utf-8-sig"))
    if isinstance(daten, dict):  # falls der Export in einem Objekt steckt
        for schluessel in ("checkins", "items", "data"):
            if isinstance(daten.get(schluessel), list):
                return daten[schluessel]
        raise SystemExit("Unbekanntes Format: keine Liste von Check-ins gefunden.")
    return daten


def vorhandene_biere():
    """Merkt sich, welche Biere schon im Projekt liegen (per Untappd-ID oder Brauerei + Name)."""
    ids, namen, dateien = set(), set(), set()
    for datei in ZIEL.glob("*.md"):
        dateien.add(datei.stem)
        text = datei.read_text(encoding="utf-8")
        m = re.search(r"^untappd_id:\s*(\d+)", text, re.M)
        if m:
            ids.add(m.group(1))
        t = re.search(r'^title:\s*"?(.+?)"?\s*$', text, re.M)
        b = re.search(r'^brauerei:\s*"?(.+?)"?\s*$', text, re.M)
        if t:
            namen.add(((b.group(1) if b else "").lower(), t.group(1).lower()))
    return ids, namen, dateien


def stile_nachtragen(probelauf):
    """Trägt bei importierten Bieren ohne Stil die Zuordnung nach, z. B. nachdem
    data/untappd_stile.yaml ergänzt wurde."""
    regeln = lies_zuordnung()
    geaendert, offen = 0, Counter()
    for datei in sorted(ZIEL.glob("*.md")):
        text = datei.read_text(encoding="utf-8")
        if "quelle: untappd" not in text or not re.search(r"^stile: \[\]\s*$", text, re.M):
            continue
        m = re.search(r'^untappd_stil:\s*(".*")\s*$', text, re.M)
        if not m:
            continue
        untappd_stil = json.loads(m.group(1))
        stil = ordne_stil_zu(untappd_stil, regeln)
        if not stil:
            offen[untappd_stil] += 1
            continue
        if not probelauf:
            datei.write_text(re.sub(r"^stile: \[\]\s*$", f"stile: [{q(stil)}]", text, count=1, flags=re.M), encoding="utf-8")
        geaendert += 1
    print(f"Stil nachgetragen:       {geaendert}{'  (Probelauf, nichts geschrieben)' if probelauf else ''}")
    if offen:
        print("\nWeiterhin ohne Zuordnung:")
        for stil, anzahl in offen.most_common():
            print(f"  {anzahl:4d} × {stil}")


# ---------- Hauptprogramm ----------

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    probelauf = "--probelauf" in sys.argv
    if "--stile-nachtragen" in sys.argv:
        stile_nachtragen(probelauf)
        return
    if not args:
        print(__doc__)
        sys.exit(1)

    checkins = lies_export(Path(args[0]))
    regeln = lies_zuordnung()

    # Check-ins pro Bier bündeln
    biere = OrderedDict()
    for c in checkins:
        name = (c.get("beer_name") or "").strip()
        brauerei = (c.get("brewery_name") or "").strip()
        if not name:
            continue
        schluessel = str(c.get("bid") or "") or f"{brauerei}|{name}".lower()
        biere.setdefault(schluessel, []).append(c)

    ids, namen, dateien = vorhandene_biere()
    neu, uebersprungen = 0, 0
    ohne_stil = Counter()

    for schluessel, liste in biere.items():
        liste.sort(key=lambda c: datum(c.get("created_at")) or datetime.min)
        erster, letzter = liste[0], liste[-1]
        name = erster["beer_name"].strip()
        brauerei = (erster.get("brewery_name") or "").strip()
        bid = str(erster.get("bid") or "")

        if (bid and bid in ids) or (brauerei.lower(), name.lower()) in namen:
            uebersprungen += 1
            continue

        untappd_stil = (erster.get("beer_type") or "").strip()
        stil = ordne_stil_zu(untappd_stil, regeln)
        if not stil and untappd_stil:
            ohne_stil[untappd_stil] += 1

        bewertungen = [zahl(c.get("rating_score")) for c in liste]
        bewertungen = [b for b in bewertungen if b]
        notizen = [(c.get("comment") or "").strip() for c in liste]
        notizen = [n for n in notizen if n]
        alkohol = zahl(erster.get("beer_abv"))
        ibu = zahl(erster.get("beer_ibu"))
        land = (erster.get("brewery_country") or "").strip()
        ort = ", ".join(x for x in ((erster.get("brewery_city") or "").strip(), LAENDER.get(land, land)) if x)
        d = datum(erster.get("created_at")) or datetime.now()

        dateiname = dateiname_fuer(brauerei, name)
        basis, n = dateiname, 2
        while dateiname in dateien:
            dateiname = f"{basis}-{n}"
            n += 1
        dateien.add(dateiname)

        zeilen = [
            "---",
            f"title: {q(name)}",
            f"date: {d.strftime('%Y-%m-%d')}",
            "stufe: kurz",
            "quelle: untappd",
        ]
        if brauerei:
            zeilen.append(f"brauerei: {q(brauerei)}")
        if ort:
            zeilen.append(f"herkunft: {q(ort)}")
        zeilen.append(f"stile: [{q(stil)}]" if stil else "stile: []")
        if untappd_stil:
            zeilen.append(f"untappd_stil: {q(untappd_stil)}")
        if alkohol:
            zeilen.append(f"alkohol: {alkohol:g}")
        if ibu:
            zeilen.append(f"ibu: {int(ibu)}")
        if bewertungen:
            zeilen.append(f"untappd_bewertung: {bewertungen[-1]:g}")
        zeilen.append(f"untappd_checkins: {len(liste)}")
        if bid:
            zeilen.append(f"untappd_id: {bid}")
        if erster.get("beer_url"):
            zeilen.append(f"untappd_link: {q(erster['beer_url'])}")
        if notizen:
            zeilen.append(f"notiz: {q(notizen[-1])}")
        zeilen += ["sitemap:", "  disable: true", "---", ""]

        if not probelauf:
            ZIEL.mkdir(parents=True, exist_ok=True)
            (ZIEL / f"{dateiname}.md").write_text("\n".join(zeilen), encoding="utf-8")
        neu += 1

    print(f"Check-ins gelesen:       {len(checkins)}")
    print(f"Verschiedene Biere:      {len(biere)}")
    print(f"Neu angelegt:            {neu}{'  (Probelauf, nichts geschrieben)' if probelauf else ''}")
    print(f"Schon vorhanden:         {uebersprungen}")
    if ohne_stil:
        print("\nOhne Zuordnung. In data/untappd_stile.yaml ergänzen, dann mit --stile-nachtragen übernehmen:")
        for stil, anzahl in ohne_stil.most_common():
            print(f"  {anzahl:4d} × {stil}")


if __name__ == "__main__":
    main()
