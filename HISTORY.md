Changelog
=========


(unreleased)
------------
- Add AGENTS.md and harmonize docs generation. [Paul Magister]
- Add AGENTS.md. [Paul Magister]
- Generate user docs. [Paul Magister]
- #AI-Engineering: Implemented the workspace context actions and
  processing updates. Right-click menus now offer Remove from Workspace
  and Open Containing Folder; Delete removes the same eligible
  selection. File removal never deletes disk files. Removing tracks,
  routes, or POIs—including all items under a category—creates an in-
  memory Generated copy and preserves the original. Mixed selection
  types are blocked, and double-clicking an unsaved copy opens its
  source with a warning in the log. Renamed Compress Files to Process
  Files. Processing now uses source-based timestamped filenames, ZIP
  results go into a folder named after the archive stem, and Merge
  writes a timestamped GPX at the output directory’s top level. Explicit
  --output remains an override. Updated the GUI/CLI docs and condensed
  the UX handoff into UX_GUI_TODO.md, UX_GUI_Prompt.md, and
  UX_GUI_DONE.md. [Paul Magister]
- #AI-Engineering: Implemented the three high-priority UX follow-ups:
  the workspace now spans the left side, the inspector and elevation
  profile stack in the center, and the map stays on the right. The log
  starts hidden but remains available from View > Show Log. Files and
  non-empty Tracks/Routes/POIs folders start collapsed; selecting a
  folder inspects its file without changing batch selection. [Paul
  Magister]
- #AI-Engineering: Implemented the artifact-inspector workspace: a left-
  side Inputs/Generated tree, cached file summaries in a context-
  sensitive inspector, and stable file/type/index identities for
  selection and plots. Batch multiselection and result reuse remain
  available; the map highlights the active artifact, and the elevation
  profile follows the selected track. Updated TODO_UX_GUI.md with
  delivered work and design decisions. [Paul Magister]
- #AI-Engineering: Die erste Workflow-Stufe ist umgesetzt: Alle GUI-
  Buttons — einschließlich der Matplotlib-Werkzeuge — verwenden nun Text
  statt Icons. Neu geladene Dateien sind standardmäßig ausgewählt;
  Select All Inputs wählt alle Dateien, und bei leerer Auswahl werden
  alle geladenen Dateien verarbeitet. Ausgewählte Ergebnisse lassen sich
  wieder zu den Eingaben hinzufügen, ohne sie aus der Ergebnisliste zu
  entfernen. [Paul Magister]
- Lilienstein.gpx umbenennen und elevation entfernen (für Tests) [Paul
  Magister]
- #AI-Engineering: core/base.py ist jetzt in fokussierte Module
  aufgeteilt: file_loader.py für GPX/KML/ZIP, geometry.py für
  Punktoptimierung, elevation.py für Höhenzugriff, gpx_serializer.py für
  Ausgabe und processor.py für Verarbeitung. Die bisherige core.base-API
  bleibt als Kompatibilitätsfassade erhalten. CLI und GUI verwenden die
  neuen Module direkt. SRTM bleibt bei aktivierter Elevation der
  Standardversuch. Der Zugriff ist injizierbar; wenn keine Höhe
  verfügbar ist, bleiben Quellhöhe oder 0 erhalten. Automatische
  Netzwerk- und Firewalldiagnose wurde aus der Verarbeitung entfernt.
  Ein echter Offline-Modus ist noch eine offene Produktentscheidung, da
  die SRTM-Bibliothek bei einem Cache-Miss weiterhin Netzwerkzugriffe
  versuchen kann. [Paul Magister]
- #AI-Engineering: Die erste größere Verbesserung ist umgesetzt: CLI und
  GUI nutzen jetzt denselben Verarbeitungsservice für Komprimieren,
  Zusammenführen und POI-Extraktion. Der CLI-Dispatch-Test verwendet
  echte GPX-Dateien statt Mocks; zusätzliche Service-Tests prüfen
  erzeugte GPX-Dateien durch erneutes Einlesen. Die Architekturpunkte
  und Folgearbeiten stehen in TODO.md. [Paul Magister]


1.1.3 (2026-10-07)
------------------
- Docs: Update HISTORY.md for release 1.1.3. [Paul Magister]
- Seit Commit bb514f3 stehen die Doku-Abhängigkeiten in [dependency-
  groups], Read the Docs installierte aber weiterhin das pip-Extra
  .[docs]. Dadurch wurde mkdocs-awesome-nav nicht installiert. Ich habe
  .readthedocs.yaml auf Read the Docs’ uv-Integration mit der Gruppe
  docs umgestellt. Hinweis: uv sync wählt standardmäßig auch die dev-
  Gruppe aus. [Paul Magister]
- Die Windows-Fehlerursache ist behoben: Der CLI-Aufruf schließt jetzt
  seine Log-Handler auch bei Fehlern, und beim erneuten Initialisieren
  werden vorhandene Handler ordnungsgemäß geschlossen. Dadurch bleiben
  keine Logdateien in temporären Testverzeichnissen gesperrt. Eine
  Regressionstest-Abdeckung prüft, dass der Logdatei-Handler nach der
  CLI-Ausführung geschlossen ist. [Paul Magister]
- Remove copy-paste-ini files from makefile. [Paul Magister]


1.1.2 (2026-10-07)
------------------
- Docs: Update HISTORY.md for release 1.1.2. [Paul Magister]
- Beim Merge bleiben jetzt Beschreibungen aus GPX und KML erhalten – bei
  Wegpunkten, Tracks, Routen und Trackpunkten. Trackpunkte mit
  Beschreibung werden außerdem nicht durch die Geometrievereinfachung
  entfernt. Das Bereinigen im Komprimierungsmodus bleibt unverändert.
  [Paul Magister]


1.1.1 (2026-10-07)
------------------
- Docs: Update HISTORY.md for release 1.1.1. [Paul Magister]
- Add tests and example files for merging gpx and kml with only pois
  inside. [Paul Magister]
- Add lxml runtime dependency. [Paul Magister]


1.1.0 (2026-10-07)
------------------
- Docs: Update HISTORY.md for release 1.1.0. [Paul Magister]
- Das bestehende CLI unterstützt jetzt --mode add-poi. gpx-kml-converter
  --mode add-poi --lat 51.0632 --lon 13.7421 \   --name "Historic Cafe"
  --desc "Coffee shop" --sym Coffee --ele 115 input.gpx. [Paul Magister]
- Update cli-config-gui, improve makefile. [Paul Magister]
- Use the new and improved cli generator. [Paul Magister]


1.0.9 (2026-10-02)
------------------
- Docs: Update HISTORY.md for release 1.0.9. [Paul Magister]
- Use config-cli-gui in new version. [Paul Magister]
- Implement douglas-peucker algorithm for track optimization improve
  cli. [Paul Magister]


1.0.8 (2026-10-02)
------------------
- Docs: Update HISTORY.md for release 1.0.8. [Paul Magister]
- Improve install.m instructions. [Paul Magister]
- Bump python to <3.14. [Paul Magister]


1.0.7 (2026-07-07)
------------------
- Docs: Update HISTORY.md for release 1.0.7. [Paul Magister]
- Fix pylint: remove import. [Paul Magister]


1.0.6 (2026-07-07)
------------------
- Docs: Update HISTORY.md for release 1.0.6. [Paul Magister]
- Update config-cli-gui: dark mode and updated gui-config concept. [Paul
  Magister]
- Update config-cli-gui: dark mode and updated gui-config concept. [Paul
  Magister]
- Update config-cli-gui. [Paul Magister]
- Remove unused tool_tip.py. [Paul Magister]


1.0.5 (2025-11-14)
------------------
- Docs: Update HISTORY.md for release 1.0.5. [Paul Magister]
- Makefile: run precommit before release to get proper formatted code.
  [Paul Magister]
- Fix compatibility between cli and gui interface. [Paul Magister]
- Proper configurations. [Paul Magister]
- Switch to new config_cli_gui version: code fixes. [Paul Magister]
- Switch to new config_cli_gui version. [Paul Magister]


1.0.4 (2025-06-27)
------------------
- Feat #6: preserve altitute plot when losing focus. [Paul Magister]
- Feat #6: fix tests. [Paul Magister]
- Feat #6: add functionality for altitute profile. [Paul Magister]
- Feat #6: Optimize waypoints. [Paul Magister]
- Feat #6: Optimize waypoints. [Paul Magister]
- Feat #6: GUI restructuring. [Paul Magister]
- Feat #5: callback/refresh: _update_selected_file_display. [Paul
  Magister]
- Feat #5: performance improvements: Restructuring GPX object handling.
  [Paul Magister]
- Feat #4: refactor classes: move gpx_plotter out. [Paul Magister]
- Feat #4: refactor classes: move gpx_plotter out. [Paul Magister]


1.0.3 (2025-06-24)
------------------
- Feat #4: remove padx and pady. [Paul Magister]
- Feat #4: Add map visualization: make window sizes resizable. [Paul
  Magister]
- Feat #4: Add map visualization and metadata info box #4. [Paul
  Magister]


1.0.2 (2025-06-23)
------------------
- Feat #3: update libs: fix example config.yaml generation. [Paul
  Magister]
- Feat #3: Update makefile with pytree and update_funding.py. [Paul
  Magister]
- Feat #3: update libs. [Paul Magister]
- Switch to use config-cli-gui lib. [Paul Magister]
- Update README.md from docs/index.md. [github-actions]


1.0.1 (2025-06-21)
------------------
- Add gui description, images and a new icon. [Paul Magister]
- Use hard link in doc, remove unnecessary core. [Paul Magister]
- Release history. [Paul Magister]
- Update README.md from docs/index.md. [github-actions]


1.0.0 (2025-06-21)
------------------
- Update and clean docs. [Paul Magister]
- Update HISTORY.md. [Paul Magister]


0.0.1 (2025-06-21)
------------------
- Adjust build macos. [Paul Magister]
- Remove unnecessary files. [Paul Magister]
- ✅ Project renamed from template. [github-actions[bot]]
- Initial commit. [Paul Magister]


