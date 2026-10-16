# Datenprobleme und Lösungsansätze

Sammlung der bei Beschaffung und Aufbereitung aufgetretenen Probleme.
Grundlage für den Methodikteil der Abschlussarbeit.

**Erhebungszeitraum:** 14.09.2026 – laufend
**Zuletzt ergänzt:** 16.10.2026

---

## A. Grenzen der Datenquellen

### A1 — Ticketmaster hat keine Historie

Die Discovery API indexiert nur laufende und kommende Veranstaltungen. Vergangenes
fällt nach kurzer Zeit aus dem Index und ist nicht rückwirkend beschaffbar.

**Auswirkung:** Für den Trainingszeitraum ab 2024 stehen keine Ticketmaster-Daten zur
Verfügung. Jeder Tag ohne laufenden Abruf ist unwiederbringlich verloren.

**Lösung:** Täglicher Snapshot per systemd-Timer ab 14.09.2026, dadurch selbst
aufgebaute Historie. Für die Vergangenheit Ersatzquellen (setlist.fm, Retrosheet).

### A2 — setlist.fm ist das Spiegelbild dazu

Archiv für gespielte Setlists, also ausschließlich Vergangenheit und ausschließlich
Musik. Keine kommenden Termine, keine Uhrzeiten, keine Kapazitäten, keine
Besucherzahlen. Sport und Theater fehlen vollständig.

**Auswirkung:** Zwei Quellen mit komplementärer Abdeckung erforderlich. Die
Überlappungsphase ab 09/2026 ist die einzige Möglichkeit, ein Zeitprofil für die
Historie zu lernen.

### A3 — Venue-Koordinaten bei setlist.fm sind Stadtmittelpunkte

Das `coords`-Objekt gehört zur Stadt, nicht zur Spielstätte. Jedes Venue in Manhattan
trägt dieselben Werte (40.71427 / -74.00597).

**Auswirkung:** Für eine Analyse auf Stationsebene unbrauchbar.

**Lösung:** Handkuratierte Venue-Tabelle (`config/venues_nyc.csv`) mit echten
Koordinaten, Kapazität und Stationszuordnung.

### A4 — Busdaten haben keine Haltestellenebene

`kv7t-n8in` und `gxb3-akrn` enthalten nur `bus_route`, keine Haltestelle und keine
Koordinaten.

**Auswirkung:** Für Busse nur Linienbezug statt Haltestellenbezug möglich.

**Lösung:** Zuordnung Linie ↔ Arena über die Haltestellen-Referenz `2ucp-7wg5`
(3.190.138 Zeilen, Linien-Haltestellen-Kombinationen mit Gültigkeitszeiträumen).

### A5 — U-Bahn-Daten kennen nur Einstiege

Die drehkreuzbasierte Erhebung erfasst keine Ausstiege.

**Auswirkung:** Die Anfahrt zu einem Event ist nur indirekt messbar; gut messbar ist
die Abfahrt danach.

---

## B. Technische Probleme der Schnittstellen

### B1 — Paging-Grenze der Ticketmaster API

Die Abfrage meldete 50 Seiten (rund 10.000 Treffer), lieferte aber nur die ersten
1.000 aus.

**Auswirkung:** 90 % der Events hätten unbemerkt gefehlt.

**Lösung:** Zerlegung in Wochenscheiben mit rekursiver Halbierung, sobald eine Scheibe
über 1.000 Treffer meldet. Ergebnis: 31.584 statt 1.000 Events.

### B2 — Der Filter `city=New York` schließt vier Stadtbezirke aus

Barclays Center, Citi Field, Yankee Stadium und Forest Hills Stadium fehlten
vollständig, da Ticketmaster Venues unter ihrem tatsächlichen Stadtteil führt
(Brooklyn, Queens, Bronx).

**Auswirkung:** Genau die für das Projekt zentralen Arenen wären nicht erfasst worden.

**Lösung:** Geografische Radiussuche (`latlong` + 20 Meilen) statt Stadtnamensfilter.
Gegenprobe nach der Umstellung: Barclays Center 217, Yankee Stadium 293,
MSG 239 Einträge.

### B3 — Abbruch des CSV-Bulk-Exports ohne Wiederaufnahme

Der Export der U-Bahn-Stundendaten (17,9 GB) brach nach 2:53 h bei 9,5 GB ab
(`curl: (56) Recv failure`). Eine Wiederaufnahme war nicht möglich, da Socrata den
Export dynamisch erzeugt und keine Byte-Ranges unterstützt
(`curl: (33) HTTP server doesn't seem to support byte ranges`).

**Auswirkung:** Knapp drei Stunden Übertragung verloren; ein erneuter Versuch wäre an
derselben Stelle gescheitert.

**Lösung:** Umstellung auf 60 Monatsscheiben über die API. Jede Scheibe ist einzeln
abgeschlossen, wiederholbar und bei erneutem Lauf überspringbar. Gesamtdauer rund
2 Stunden. Gegenprüfung ergab exakt 120.855.567 Zeilen.

### B4 — `$limit` schneidet stillschweigend ab

Die Haltestellen-Referenz wurde mit `$limit=200000` geholt und lieferte exakt
200.001 Zeilen. Tatsächlich enthält der Datensatz 3.190.138 Zeilen.

**Auswirkung:** Die Datei wirkte vollständig und plausibel; die daraus abgeleiteten
16.805 Haltestellen lagen sogar in einer glaubwürdigen Größenordnung. Ohne
Gegenprüfung wäre mit einem Sechzehntel der Daten weitergearbeitet worden.

**Lösung:** Grundsätzlich jede Abfrage gegen `$select=count(*)` prüfen.

### B5 — HTTP 200 belegt keine gültige Authentifizierung

Öffentliche Socrata-Datasets antworten auch ohne gültigen Token mit Status 200.

**Lösung:** Differenztest mit absichtlich ungültigem Token; erst der Unterschied
zwischen beiden Antworten ist aussagekräftig.

### B6 — Zwei verwechselbare Zugangsarten bei Socrata

| | App Token | API Key |
|---|---|---|
| Form | ein String | Key ID + Key Secret |
| Übergabe | Header `X-App-Token` | HTTP Basic Auth |
| Zweck | hebt das Ratenlimit an | authentifiziert als Person |

Für den gemeinsamen Betrieb ist nur der App Token geeignet, da ein API Key die Rechte
einer konkreten Person trägt und das Ratenlimit nicht anhebt.

### B7 — Ratenlimit bei setlist.fm

1.440 Requests pro Tag, gezählt pro Schlüssel und nicht pro Person. Bei einem
gemeinsam genutzten Schlüssel teilen sich alle Projektmitglieder dieses Kontingent.
Die Freigabe erfolgt manuell mit erheblicher Wartezeit; inaktive Schlüssel werden nach
einem Jahr automatisch deaktiviert.

**Lösung:** Backfill einmalig und kontrolliert über den Dienstnutzer; Entwicklung
gegen die zwischengespeicherten Rohantworten statt gegen die API.

---
## C. Datenqualität und Formate

### C1 — Inhaltlicher Austausch eines Datensatzes im laufenden Betrieb

Der gravierendste Vorfall. Der Datensatz *MTA Bus Stop Level Ridership* (`fvdm-uavx`)
enthielt am 14.10.2026 tagesgenaue Zählungen:

| | 14.10.2026 | 16.10.2026 |
|---|---|---|
| Spalten | date, hour, route_id, direction, stop_id, stop_sequence, boardings, alightings, trips | month, weekday, day_type, hour, route_id, trip_type, stop_id, direction_id, stop_sequence, estimated_ridership |
| Zeilen | 169.862.731 | 102.173.328 |
| Zeitraum | 30.09.2024 – 31.08.2026 | 01.01.2024 – 01.09.2026 |
| Zeitbezug | Kalendertag | Monatsdurchschnitt je Wochentag |

Die Metadaten weisen für alle Zeilen `created_at = 2026-10-15T17:21:07Z` aus, der
Bestand wurde also vollständig ersetzt. Die Beschreibungsseite des Portals zeigte zu
diesem Zeitpunkt noch die alte Spaltenliste; der Widerspruch fiel erst durch einen
HTTP 400 mit der Meldung `No such column: date` auf.

**Auswirkung:** Die ursprünglich als primäre Busquelle vorgesehenen haltestellengenauen
Tagesdaten existierten rund 24 Stunden lang und sind nicht mehr beschaffbar. Durch die
Mittelung über alle gleichartigen Wochentage ist gerade die Abweichung vom Normalfall,
also der zu messende Effekt, im neuen Bestand nicht mehr enthalten.

**Lösung:** Wechsel auf die linienbasierten Datensätze mit echter Zeitachse. Die neuen
Mittelwerte bleiben als Verteilungsschlüssel nutzbar, um Linienzahlen näherungsweise
auf einzelne Haltestellen herunterzubrechen.

**Konsequenz für das Vorgehen:** Manifest-Datei je Quelle mit Abrufzeitpunkt,
Dataset-ID, Zeilenzahl und Kopfzeile, damit derartige Änderungen sofort auffallen.

### C2 — Uneinheitliche Datumsformate

| Quelle | Format |
|---|---|
| MTA CSV-Bulk-Export | `MM/DD/YYYY` |
| MTA API | ISO 8601 |
| setlist.fm | `dd-MM-yyyy` |
| Stop Level (alt), Feld `hour` | Text, 12-Stunden-Format mit AM/PM |

Bemerkenswert ist, dass derselbe Datensatz je nach Zugriffsweg unterschiedliche
Formate liefert.

**Auswirkung:** Automatische Typerkennung führt zu stillen Fehlinterpretationen, etwa
05.06. statt 06.05.

### C3 — Zahlen als Zeichenketten

Socrata liefert numerische Felder in JSON durchgängig als Strings
(`{"count": "51575"}`). Typen müssen beim Schreiben nach Parquet explizit gesetzt
werden.

### C4 — Hoher Anteil inhaltsleerer Zeilen

Die Busdaten bilden ein vollständiges Kreuzprodukt aus 425 Linien × 24 Stunden ×
Kalendertag × 12 Fahrkartenarten × 2 Zahlungsarten.

Stichprobe Januar 2024: 6.325.717 von 7.588.800 Zeilen tragen den Wert null,
entsprechend 83 %.

**Lösung:** Filterung auf `ridership > 0 OR transfers > 0` beim Schritt nach `interim`.
Die zweite Bedingung ist notwendig, da Umsteiger ohne neue Zahlung erfasst werden und
für die Auslastung relevant sind.

### C5 — Aufteilung einer Zeitreihe auf mehrere Datensätze

| Modus | bis 2024 | ab 2025 |
|---|---|---|
| U-Bahn stündlich | `wujg-7c2s` | `5wq4-mkjj` |
| Bus stündlich | `kv7t-n8in` | `gxb3-akrn` |

Die Kopfzeilen stimmten jeweils überein, was aber nicht vorausgesetzt werden darf und
geprüft wurde.

### C6 — Unterschiedliche Erhebungsgrundlagen

Die linienbasierten Stundenzahlen beruhen auf Fahrkartendaten, die haltestellenbezogenen
auf Sensorzählungen in den Fahrzeugen (Automatic Passenger Counters). Die Werte sind
nicht summierbar und nur begrenzt vergleichbar.

---

## D. Betrieb und Infrastruktur

### D1 — Gruppenrechte wirken erst bei neuer Anmeldung

Nach `usermod -aG` scheiterte der Zugriff auf `/srv/nycproj/.env` mit
`PermissionError: [Errno 13]`. Ursache: Gruppen werden beim Login in den Prozess
geschrieben. Erschwerend behält der VS-Code-Server auf dem Host seine beim Start
ermittelten Gruppen und überlebt ein Trennen der Verbindung.

**Lösung:** Serverprozess beenden (`Remote-SSH: Kill VS Code Server on Host`) und neu
verbinden. Gegenprobe über `sudo -u <nutzer>`, da dies die Gruppen frisch aufbaut.

### D2 — Git verweigert Arbeit in fremdem Verzeichnis

`/srv/nycproj/app` wurde mit `sudo` angelegt und gehörte root, was zu
`fatal: detected dubious ownership` führte. Die naheliegende Abhilfe über
`git config --global` wirkt nur für den ausführenden Benutzer und löst das Problem für
die übrigen Projektmitglieder nicht.

**Lösung:** Eigentümer korrigieren, Ausnahme systemweit eintragen,
`core.sharedRepository group` setzen, damit neue Git-Objekte gruppenschreibbar bleiben.

### D3 — Masken und Standardrechte bei gemeinsamer Ablage

Das setgid-Bit vererbt nur die Gruppe, nicht die Schreibrechte. Die Standardmaske 022
erzeugt Dateien, die für die Gruppe lediglich lesbar sind.

**Lösung:** Default-ACLs auf dem Datenverzeichnis. Diese gelten für alle schreibenden
Prozesse einschließlich der Dienste und setzen die umask außer Kraft.

**Randbedingung:** `mv` innerhalb desselben Dateisystems überträgt die bestehenden
Rechte; die Default-ACL greift dabei nicht. Temporäre Dateien werden deshalb im
Zielverzeichnis angelegt und dort umbenannt.

### D4 — Übertragungsrate als limitierender Faktor

Der Durchsatz lag bei 400 bis 900 KB/s. Ein Vergleichstest gegen eine statische Datei
über ein Content Delivery Network legt nahe, dass die serverseitige Erzeugung des
Exports die Begrenzung darstellt, nicht die Netzanbindung oder die Entfernung
(Server in Nürnberg, Quelle in den USA).

Die Zerlegung in Monatsscheiben verkürzte den Gesamtvorgang von über 10 Stunden auf
etwa 2 Stunden, da mehrere kleinere Abfragen weniger serverseitige Vorbereitung
erfordern.

---

## Übergreifende Lehren

1. **Jede Abfrage gegen eine unabhängige Sollgröße prüfen.** Weder HTTP 200 noch eine
   plausible Dateigröße noch eine glaubwürdige Zeilenzahl belegen Vollständigkeit.
2. **Rohdaten unverändert archivieren.** Parserfehler lassen sich beheben, verlorene
   Rohdaten nicht.
3. **Große Abrufe in wiederholbare Scheiben zerlegen.** Ein langlaufender Vorgang ohne
   Zwischenstände ist bei jedem Abbruch vollständig verloren.
4. **Datensätze sind nicht stabil.** Weder Inhalt noch Schema noch Dokumentation sind
   über die Projektlaufzeit garantiert (siehe C1).

