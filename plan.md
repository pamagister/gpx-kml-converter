# Plan: UX/UI- und Workflow-Verbesserungen für gpx-kml-converter

## 1. Objective and desired outcome

Das Ziel ist es, das Nutzererlebnis der GUI-Anwendung `gpx-kml-converter` zu verbessern und den
Verarbeitungs-Workflow transparenter, fehlerresistenter und intuitiver zu gestalten. Die Kern-Logik
(GPX/KML-Verarbeitung, CLI, Kartendarstellung) bleibt unverändert. Schwerpunkt sind die GUI,
das Prozess-Feedback, die Selektionslogik, visuelle Hierarchie und Onboarding.

Erwartetes Ergebnis:
- Ein neuer Nutzer kann ohne Dokumentation eine Datei öffnen, verarbeiten und das Ergebnis finden.
- Während der Verarbeitung ist immer sichtbar: Status, aktuelle Datei, Fortschritt.
- Nach Abschluss ist ohne separates Log-Fenster klar, was verarbeitet wurde und wo die Ergebnisse liegen.
- Versehentliche Massenverarbeitung ohne explizite Bestätigung wird verhindert.

## 2. Scope, constraints and explicit non-goals

### In Scope
- GUI-Hauptfenster (`src/gpx_kml_converter/gui/gui.py` und `gui/artifacts.py`)
- Log-Anzeige und Fortschritts-Feedback
- Datei-Auswahl, Selektion, Verarbeitungs-Buttons, Kontextmenüs
- Leer-Zustände, About-Dialog, Tooltips
- README / `docs/index.md` Ergänzungen für GUI-Erste-Schritte
- Tests für neue GUI-Verhalten

### Out of Scope (explicit non-goals)
- Änderungen an der Verarbeitungs-Logik (`application/processing.py`, `core/*.py`)
- Änderungen am CLI (`cli/cli.py`)
- Neue Dateiformate oder neue Verarbeitungs-Modi
- Änderungen am Build-/Verpackungs-Setup (PyInstaller, pyproject, Makefile)
- SRTM-Höhenmodul oder Kartendarstellung außerhalb der bestehenden `GPXPlotter`-Nutzung

### Constraints
- Python 3.11+, tkinter + ttkbootstrap (bestehender Tech-Stack bleibt)
- `config-cli-gui`-Settings-Dialog bleibt bestehen
- Nicht-destruktiver Workspace-Prinzip (Originaldateien nie verändern) bleibt erhalten
- Bestehende pytest-Tests müssen weiterlaufen

## 3. Architecture and decisions

| Entscheidung | Begründung |
|---|---|
| Log-Panel in Hauptfenster integrieren (docked, unten), statt separates Toplevel | Nutzer sehen Fortschritt und Fehler kontextbezogen, ohne Fenster suchen zu müssen |
| Deterministischer Fortschrittsbalken mit Datei-Label statt nur `indeterminate` | Transparenz bei langen Vorgängen |
| Abschluss-Zusammenfassung nach Verarbeitung im Hauptfenster | Klare Abschluss-Rückmeldung ohne Log-Fenster |
| Bestätigungsdialog bei "Clear Workspace" und bei Verarbeitung ohne Selektion ("Alle X verarbeiten?") | Verhindert versehentliche Datenverarbeitung / Löschung |
| Drag & Drop für GPX/KML/ZIP in den Workspace | Erwarteter Desktop-Standard, reduziert Klicks |
| Layout-Anpassung: Workspace prominenter, Karte dauerhaft sichtbar | Karte bleibt Teil des Standardlayouts; Workspace bekommt mehr Gewicht |
| Icons + konsistentes Button-Styling für die drei Modi | Schnellere visuelle Erkennung |
| About-Dialog mit echter Version aus `_version.py`, korrektem Autor | Professioneller Eindruck |
| Änderungen in kleinen, eigenständigen Phasen umarbeiten, jede Phase separat commitbar | Ermöglicht Review und Rücksetzen bei Problemen |

## 4. Phases containing coherent work packages

### Phase 1: Process-Feedback und Logging [x]

#### 1.1 Log-Panel ins Hauptfenster integrieren [x]
- Log-Text-Widget fest im Hauptfenster platzieren (unten, docked), statt nur im separaten Toplevel.
- Separates Toplevel-Fenster kann über Menü weiterhin geöffnet werden, aber das Hauptfenster-Panel ist standardmäßig sichtbar.
- Log-Level-Selektor und Clear-Button ebenfalls im Hauptfenster verfügbar.

Acceptance criteria:
- Beim Start ist ein Log-Panel im Hauptfenster sichtbar und empfängt Log-Einträge.
- Klicken auf "View → Show Log" öffnet weiterhin das separate Fenster (funktioniert wie bisher).
- Bestehende Tests für Logging-Interface laufen weiter.

#### 1.2 Deterministischer Fortschritt und Datei-Label [x]
- Fortschrittsbalken von `indeterminate` auf deterministisch umstellen, soweit die Verarbeitungs-Logik Fortschritt liefert.
- Aktuelle Datei ("Verarbeite X von Y — datei.gpx") daneben anzeigen.
- Fortschritt zurücksetzen bei Start neuer Verarbeitung.

Acceptance criteria:
- Während einer Verarbeitung zeigt der Balken einen deterministischen Wert (nicht nur Animation).
- Ein Label zeigt die aktuell verarbeitete Datei und den Zähler (X von Y).

#### 1.3 Abschluss-Zusammenfassung [x]
- Nach erfolgreichem Abschluss: Hinweis im Hauptfenster (Status-Label oder nicht-blockierender Info-Bereich) mit Anzahl verarbeiteter Dateien, Modus und Ausgabepfad als klickbarer Link.
- Bei Fehler: nicht-blockierende Anzeige im Log-Panel statt nur `messagebox`.

Acceptance criteria:
- Nach Verarbeitung ist im Hauptfenster ersichtlich, wie viele Dateien verarbeitet wurden und wo die Ergebnisse liegen.
- Ein Klick auf den Ausgabepfad öffnet den Ordner im Dateisystem.

### Phase 2: Selektionssicherheit und Workflow [ ]

#### 2.1 Bestätigung bei "Clear Workspace" [x]
- Vor dem Leeren des gesamten Workspaces einen Bestätigungsdialog anzeigen.

Acceptance criteria:
- "Clear Workspace" löscht den Workspace nur nach expliziter Nutzerbestätigung.
- Abbruch lässt den Workspace unverändert.

#### 2.2 Warnung bei Verarbeitung ohne Selektion [x]
- Wenn keine Datei selektiert ist und "Alle X Dateien" verarbeitet würden, Hinweis-Dialog anzeigen ("Alle X Dateien verarbeiten?").
- Auswahl kann bestätigt oder abgebrochen werden.

Acceptance criteria:
- Starke Nutzeraktion (Verarbeitung) bei leerer Selektion wird vorab explizit bestätigt.
- Batch-Status bleibt sichtbar und eindeutig ("Batch: all X input files").

#### 2.3 Drag & Drop für Dateien [ ]
- Dateien per Drag & Drop in den Workspace ziehen können (GPX, KML, ZIP).
- Gleiches Verhalten wie beim "Open Files"-Dialog.

Acceptance criteria:
- Ziehen einer GPX/KML/ZIP-Datei in den Workspace lädt die Datei.
- Ungültige Dateien werden ignoriert und im Log gewarnt.

#### 2.4 Undo für Workspace-Entfernung (optional, geringer Aufwand) [ ]
- "Letzte Änderung rückgängig" für Artefakt-Entfernung im Workspace (In-Memory-Kopie vor der Änderung).

Acceptance criteria:
- Entfernte Artefakte oder Dateien können einmalig wiederhergestellt werden.
- Originaldatei auf Disk wird nie verändert.

### Phase 3: Visuelles Design und Informationsarchitektur [ ]

#### 3.1 Layout-Anpassung [ ]
- Workspace-Bereich prominenter gestalten (größeres Gewicht).
- Karte bleibt dauerhaft sichtbar (nicht einklappbar/ausblendbar), Paned-Window-Gewichte zugunsten des Workspaces überdenken.

Acceptance criteria:
- Workspace nimmt im Standardlayout mehr Raum ein als die Karte.
- Karte ist dauerhaft sichtbar und Teil des Standardlayouts.

#### 3.2 Icons und konsistentes Button-Styling [ ]
- Drei Verarbeitungs-Buttons mit Icons und einheitlichem Styling versehen.
- Modus-Namen präzisieren: "Process Files" → "Compress Files", "Merge Files", "Extract POIs from Tracks".
- Tooltips für alle Buttons und Menüeinträge.

Acceptance criteria:
- Jeder Verarbeitungs-Button hat ein zugehöriges Icon und ein aussagekräftiges Label ("Compress Files", "Merge Files", "Extract POIs from Tracks").
- Tooltips erscheinen beim Hovern über Buttons und Menüeinträgen.

#### 3.3 Leer-Zustände und Onboarding [ ]
- Beim Start ohne Dateien: einladender Leer-Zustand mit Call-to-Action ("Erste Datei öffnen").
- Kurze Hinweise im Leer-Zustand, keine generische Meldung nur.

Acceptance criteria:
- Der Erststart zeigt einen klaren Einstiegspunkt ohne Notwendigkeit, die Dokumentation zu lesen.

#### 3.4 About-Dialog korrigieren [ ]
- Echte Version aus `src/gpx_kml_converter/_version.py` auslesen.
- Projekt-Name und Autor korrekt setzen (keine Platzhalter wie "Your Name/Organization").

Acceptance criteria:
- About-Dialog zeigt die installierte Version und keine Platzhaltertexte.

### Phase 4: Daten-Vorschau und Kontrolle [ ]

#### 4.1 Vorschau vor der Verarbeitung [ ]
- Vor Start einer Verarbeitung: Punktanzahl, geschätzte Dateigröße, Differenz vorher/nachher (bei Kompression) anzeigen.
- Nutzer kann die Verarbeitung nach der Vorschau bestätigen oder abbrechen.

Acceptance criteria:
- Vor einer Kompression wird die erwartete Änderung an Punktanzahl/Größe angezeigt.
- Bestätigung ist erforderlich, bevor die Verarbeitung startet.

#### 4.2 Speicherort-Dialog pro Vorgang [ ]
- Optional zum globalen Settings-Pfad: bei Verarbeitung Zielverzeichnis wählbar machen.

Acceptance criteria:
- Der Nutzer kann pro Verarbeitungsvorgang einen eigenen Ausgabepfad wählen.

#### 4.3 Zuletzt geöffnete Dateien [ ]
- Datei-Menü listet zuletzt geöffnete Dateien zur schnellen Wiederwahl.

Acceptance criteria:
- Das Datei-Menü enthält einen "Zuletzt geöffnet"-Eintrag mit bis zu 5 Einträgen.

### Phase 5: Dokumentation [ ]

#### 5.1 README / docs/index.md für GUI ergänzen [ ]
- Screenshots der GUI erstellen und in die Dokumentation einbinden (`docs/usage/gui.md` und `docs/index.md`).
- "Erste Schritte mit der GUI"-Abschnitt (Datei öffnen → verarbeiten → Ergebnis finden).
- Hinweise zu Drag & Drop und Leer-Zuständen.

Acceptance criteria:
- `docs/index.md` enthält einen GUI-Erste-Schritte-Block mit aktuellen Screenshots.
- `README.md` wird über `make syncdocs` (oder `make fmt`) daraus generiert.

#### 5.2 Troubleshooting-Abschnitt [ ]
- Häufige Probleme: SRTM nicht verfügbar, KML öffnet sich nicht, Log leer, Ausgabepfad nicht gefunden.

Acceptance criteria:
- `docs/usage/gui.md` oder `docs/index.md` enthält einen Troubleshooting-Block.

## 5. Acceptance criteria and verification expectations

Globale Abnahmekriterien (alle Phasen):
- [ ] `make test` (Ruff + pytest + Coverage) läuft grün.
- [ ] Bestehende GUI-Tests (`tests/test_gui_workflow.py`, `test_gui_artifacts.py`) bleiben grün.
- [ ] Manuelle Prüfung: Eine Datei öffnen, komprimieren, Ergebnis finden — ohne Dokumentation und ohne Hilfestellung.
- [ ] Während der Verarbeitung ist Fortschritt und aktuelle Datei sichtbar.
- [ ] Nach Abschluss sind verarbeitete Dateien und Ausgabepfad im Hauptfenster erkennbar.

Phase-Gates:
- Phase 1 gilt als abgeschlossen, wenn Log-Panel, Fortschritt und Zusammenfassung funktionieren und getestet sind.
- Phase 2 gilt als abgeschlossen, wenn Drag & Drop, Bestätigungen und Selektions-Warnung implementiert sind.
- Phase 3 gilt als abgeschlossen, wenn Layout, Icons, Tooltips und About-Dialog umgesetzt sind.
- Phase 4 gilt als abgeschlossen, wenn Vorschau, Speicherort-Dialog und zuletzt geöffnete Dateien umgesetzt sind.
- Phase 5 begleitet jede Phase (Dokumentation mitwachsen lassen).

## 6. Dependencies, risks and unresolved questions

### Dependencies
- `ttkbootstrap` für thematisiertes Widget-Styling (bereits vorhanden).
- `config-cli-gui` für Settings-Dialog (bereits vorhanden).
- Keine neuen externen Abhängigkeiten geplant für Phase 1–3.

### Risks
- Deterministische Fortschrittsanzeige erfordert ggf. Änderungen an `process_gpx_files`, um Fortschritt zurückzumelden. Falls die Anwendung das nicht liefert, bleibt der Balken indeterminiert mit Datei-Label als Fallback.
- Drag & Drop unter tkinter ist plattformabhängig (Windows/macOS/Linux unterschiedlich). Implementierung muss auf allen Zielplattformen getestet werden.
- Layout-Änderungen können bestehende Screenshots in der Dokumentation ungültig machen.

### Unresolved questions (zur Klärung mit dem Nutzer)
Keine offenen Fragen mehr; alle Punkte wurden mit dem Nutzer abgestimmt:
1. Karte bleibt dauerhaft sichtbar.
2. Bezeichnung lautet "Compress Files".
3. Screenshots werden in die Dokumentation aufgenommen.
4. Phase 4 ist fester Bestandteil des Plans.

### Deferred work
- Barrierefreiheits-Audit (Kontraste, Fokus-Ringe, Screenreader-Label) ist nicht als eigene Phase enthalten, sollte aber bei Gelegenheit nachgeholt werden.
