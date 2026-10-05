# bierspot.de

Ehrliche Biertests, die dir erklären, was zu deinem Essen passt und warum.

Die Seite wird mit [Hugo](https://gohugo.io) gebaut und über GitHub Pages veröffentlicht. Sie braucht kein externes Theme, alles liegt in diesem Repository.

## Aufbau

| Ordner / Datei | Inhalt |
| --- | --- |
| `content/biertests/` | Ein Biertest pro Datei |
| `content/posts/` | Beiträge |
| `content/food-pairing.md` | Seite für den Food-Pairing-Finder |
| `content/so-bewerte-ich.md` | Erklärung der Profil-Skala |
| `data/profil.yaml` | Die fünf Merkmale des Geschmacksprofils und ihre Stufen |
| `data/stile.yaml` | Bierstile mit Beschreibung und typischem Profil |
| `data/pairing.yaml` | Gerichte und passende Bierstile für den Finder |
| `layouts/` | Vorlagen, darunter das Spinnennetz in `layouts/_partials/spinnennetz.html` |
| `assets/` | CSS und JavaScript |
| `scripts/untappd_import.py` | Übernimmt Untappd-Check-ins als „Kurz notiert" |
| `data/untappd_stile.yaml` | Übersetzt Untappd-Stile auf die eigene Stil-Liste |
| `.github/workflows/hugo.yml` | Baut und veröffentlicht die Seite automatisch |

Hugo erzeugt daraus automatisch:

- eine Seite pro Bierstil unter `/stile/…`, sobald ein Test diesen Stil hat
- „Ähnliche Biere" unter jedem Test, berechnet aus Stil und passenden Gerichten
- die Datei `/biere.json` mit allen Tests, als Grundlage für weitere Tools

## Einen neuen Biertest anlegen

```bash
hugo new content biertests/name-des-biers.md
```

Die Vorlage enthält alle Felder. Wichtig:

- **stile:** genau so geschrieben wie in `data/stile.yaml`, zum Beispiel `"Pale Ale"`
- **profil:** fünf Werte von 1 bis 5, Bedeutung siehe `/so-bewerte-ich/`
- **passt_zu:** Gerichte genau so geschrieben wie in `data/pairing.yaml`
- **draft: true** entfernen oder auf `false` setzen, sonst erscheint der Test nicht

Ohne Hugo geht es auch: Eine bestehende Datei in `content/biertests/` kopieren und anpassen.

## Untappd-Check-ins übernehmen („Kurz notiert")

Biere aus Untappd erscheinen als **Kurz notiert**: mit Brauerei, Stil, Alkohol, deiner Notiz und deiner Bewertung, aber ohne eigenes Geschmacksprofil. Stattdessen zeigt das Netz gestrichelt das typische Profil des Stils. Diese Seiten sind für Suchmaschinen auf „nicht indexieren" gestellt und stehen nicht in der Sitemap.

1. Bei Untappd (mit Insiders-Abo, im Browser) unter **Drink History** den Export als **JSON** anfordern. Er kommt per E-Mail.
2. Im Hauptordner des Projekts ausführen:

   ```bash
   python3 scripts/untappd_import.py pfad/zur/datei.json --probelauf   # erst nur anschauen
   python3 scripts/untappd_import.py pfad/zur/datei.json               # dann wirklich anlegen
   ```

3. Das Skript zeigt am Ende Untappd-Stile ohne Zuordnung. Diese in `data/untappd_stile.yaml` ergänzen und dann übernehmen:

   ```bash
   python3 scripts/untappd_import.py --stile-nachtragen
   ```

Später einfach einen neuen Export holen und Schritt 2 wiederholen. Vorhandene Dateien werden nie überschrieben, nur neue Biere kommen dazu.

**Doppelte vermeiden:** Wenn ein Bier schon als ausführlicher Test existiert, aber bei Untappd anders heißt, trag im Test die Zeile `untappd_id: 12345` ein. Die Nummer steht in der Untappd-Adresse des Biers. Dann überspringt das Skript dieses Bier.

**Aus „Kurz notiert" einen Test machen:** In der Datei die Zeile `stufe: kurz` und den Block `sitemap: disable: true` löschen, dann `profil`, `passt_zu`, `fazit` und den Text ergänzen. Den Rest erledigt die Seite automatisch.

Die eigene Untappd-Bewertung lässt sich in `hugo.toml` mit `zeigeUntappdBewertung = false` ausblenden.

## Lokal ansehen

```bash
hugo server
```

Dann im Browser `http://localhost:1313` öffnen. Getestet mit Hugo 0.167.0 (Extended).

## Erstmals auf GitHub bringen

1. Auf GitHub ein neues Repository anlegen, zum Beispiel `bierspot`. Öffentlich oder privat ist egal, GitHub Pages geht bei privaten Repositories aber nur mit einem bezahlten Konto.
2. Den Inhalt dieses Ordners hochladen. Am einfachsten mit **GitHub Desktop**: Ordner als Repository hinzufügen, „Publish repository".
   - Beim Hochladen über die Website per Drag-and-drop wird der versteckte Ordner `.github` oft nicht mit übertragen. Dann die Datei `.github/workflows/hugo.yml` danach über „Add file" → „Create new file" anlegen und den Inhalt einfügen.
3. Im Repository unter **Settings → Pages** bei „Source" **GitHub Actions** auswählen.
4. Unter **Actions** prüfen, ob der Lauf „Seite bauen und veröffentlichen" grün ist. Die Seite ist dann unter `https://torsten107.github.io/bierspot/` erreichbar.

Die alte Seite auf bierspot.de bleibt so lange unverändert online.

## bierspot.de umstellen (IONOS)

Erst umstellen, wenn die neue Seite unter der GitHub-Adresse fertig ist.

1. **Domain bei GitHub bestätigen (empfohlen):** Auf GitHub unter Profil → **Settings → Pages → Verified domains** `bierspot.de` hinzufügen. GitHub zeigt einen TXT-Eintrag an, den du bei IONOS anlegst. Das schützt die Domain davor, dass jemand anderes sie auf GitHub nutzt.
2. **Bei IONOS die DNS-Einträge setzen:** Domains & SSL → bierspot.de → DNS.
   - Vorhandene **A**- und **AAAA**-Einträge für `@` (Hostname leer) und für `www` löschen bzw. ersetzen.
   - **MX-Einträge nicht anfassen**, sonst kommt keine E-Mail an torsten@bierspot.de mehr an.
   - Neu anlegen:

| Typ | Hostname | Wert |
| --- | --- | --- |
| A | @ | 185.199.108.153 |
| A | @ | 185.199.109.153 |
| A | @ | 185.199.110.153 |
| A | @ | 185.199.111.153 |
| AAAA | @ | 2606:50c0:8000::153 |
| AAAA | @ | 2606:50c0:8001::153 |
| AAAA | @ | 2606:50c0:8002::153 |
| AAAA | @ | 2606:50c0:8003::153 |
| CNAME | www | torsten107.github.io |

   Falls IONOS die Domain noch mit einem eigenen Webspace verknüpft hat, die Verknüpfung vorher lösen, sonst lässt IONOS die A-Einträge nicht ändern.

3. **Im Repository:** Settings → Pages → **Custom domain** `bierspot.de` eintragen und speichern. Sobald der Haken bei der DNS-Prüfung grün ist, **Enforce HTTPS** aktivieren. Das Zertifikat kann bis zu einer Stunde dauern.

Bis die Umstellung überall angekommen ist, können ein paar Minuten bis Stunden vergehen.

## Offen

- Die übrigen alten Beiträge aus dem bisherigen Hugo-Projekt nach `content/posts/` kopieren. Dateinamen beibehalten, dann bleiben die Adressen gleich.
- Profilwerte, „passt zu" und Fazit der zwei übernommenen Tests sind Vorschläge und sollten geprüft werden.
- Impressum und Datenschutz sind Entwürfe und sollten rechtlich geprüft werden.
