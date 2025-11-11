# CO₂-Bilanzierer - Architekturübersicht

## 1. Schichtenarchitektur

```
┌─────────────────────────────────────────────┐
│         UI Layer (CustomTkinter)            │
│  WelcomeWindow │ MainWindow │ Views         │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│      Core Layer (AppOrchestrator)           │
│  • Zentrale Steuerung                       │
│  • Event-Management (StateStore)            │
│  • API für UI                               │
└──────────────────┬──────────────────────────┘
                   │
      ┌────────────┼────────────┐
      │            │            │
┌─────▼────┐ ┌────▼────┐ ┌─────▼──────┐
│ Services │ │  Data   │ │Persistence │
│ CalcSvc  │ │CSV Repo │ │   JSON     │
└──────────┘ └─────────┘ └────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│           Models Layer                      │
│  Project │ Variant │ MaterialRow │Material  │
└─────────────────────────────────────────────┘
```

## 2. Komponenten-Übersicht

### Models (Datenstrukturen)

**Material** - CSV-Zeile/EPD
- Eigenschaften: id, name, unit, gwp_a1a3, gwp_c3, gwp_c4, gwp_d
- Methoden: to_dict(), from_dict(), has_c_modules(), has_d_module()

**MaterialRow** - Material + Menge in Variante
- Verknüpft Material mit Quantity
- Enthält berechnete Werte (result_a, result_ac, result_acd)

**Variant** - Bauwerksvariante
- Liste von MaterialRows
- Methoden: add_row(), remove_row(), move_row_up/down(), calculate_sums()

**Project** - Hauptcontainer
- Liste von Variants (max. 5)
- CSV-Metadaten, Systemgrenze, UI-Zustand

### Core Layer

**AppOrchestrator** - Zentrale Steuerungseinheit
- Koordiniert alle Services
- Stellt API für UI bereit
- Verwaltet StateStore (Events)
- Implementiert Autosave mit Debounce (800ms)
- **Zentrale Farbverwaltung** (`material_colors` Dictionary):
  - `update_material_colors(variant_indices)`: Aktualisiert Farben basierend auf sichtbaren Varianten
  - `get_material_color(material_name)`: Gibt konsistente Farbe für Material zurück
  - Alphabetische Sortierung für konsistente Farbzuordnung
  - Verwendet `plt.cm.tab20.colors` (20 Farben)

**StateStore** - Event-System
```python
Events:
- project_loaded, csv_loaded
- row_updated, row_deleted, row_moved
- boundary_changed, visibility_changed
- rebuild_charts
- autosave_success, autosave_failed
```

**PersistenceService** - Speichern/Laden
- Verzeichnis: ~/.abc_co2_bilanzierer/
- **Flexible Projektspeicherung:**
  - Interne Projekte: `~/.abc_co2_bilanzierer/projects/<uuid>.json`
  - Externe Projekte: Beliebiger Speicherort (Desktop, Cloud, etc.)
  - UUID-basierte Identifikation (unabhängig vom Dateinamen)
- **Intelligente Pfadverwaltung:**
  - `external_project_paths`: Mapping UUID → Dateipfad
  - Automatische Pfad-Aktualisierung bei Umbenennung/Verschiebung
  - Sucht nach UUID wenn Datei nicht gefunden
- **Recent Projects:**
  - Liste der zuletzt geöffneten Projekte (max. 10)
  - Automatische Säuberung ungültiger Einträge
  - Sortierung nach letzter Nutzung
- Snapshots: Max. 20 pro Projekt
- **config.json**: Favoriten, CSV-Pfad, Theme, externe Pfade, last_open_directory
- Auto-Restore beim Start

**UndoRedoManager** - Änderungsverwaltung
- **Stack-basierte History** mit max. 10 Schritten
- **Deep Copy** von Project-States für sichere Isolation
- **Automatische Redo-Löschung** bei neuen Änderungen
- **Loop-Prevention** beim Anwenden von Undo/Redo
- Integriert mit allen State-ändernden Operationen

### Services

**CalculationService** - CO₂-Berechnungen
```python
calc_gwp(material, quantity, boundary):
    gwp_a = quantity × gwp_a1a3
    gwp_ac = quantity × (gwp_a1a3 + gwp_c3 + gwp_c4)
    gwp_acd = gwp_ac + (quantity × gwp_d)
```

**PDF-Export** (Version 2.0 - Komplett neu implementiert)
- **Modularer Aufbau** (7 separate Module in `services/pdf/`):
  1. `pdf_config.py`: Konfigurationsklassen (`ExportConfig`, `InfoBlock`)
  2. `pdf_styles.py`: Style-Definitionen (`PDFStyles`, `PDFColors`)
  3. `pdf_charts.py`: Diagramm-Erstellung mit **Orchestrator für konsistente Farben**
  4. `pdf_tables.py`: Professionelle Tabellen (graue Header, SUMMEN-Zeile, Grid)
  5. `pdf_header_footer.py`: Header/Footer-Renderer (auf jeder Seite)
  6. `pdf_export_pro.py`: Hauptklasse (`PDFExporterPro`, orchestriert Export)
  7. `export_dialog_pro.py`: Erweiterter GUI-Dialog (in `ui/dialogs/`)
- **Features**:
  - PageTemplate mit Header/Footer auf jeder Seite
  - Gestapelte & horizontale Diagramme (200 DPI)
  - **Konsistente Farben** (Orchestrator wird übergeben)
  - Info-Blöcke (Methodik, Projektbeschreibung, Ergebnisse)
  - Kommentar-Felder pro Variante
  - Logo-Unterstützung (3 Logos inkludiert)
  - Layout im Excel-Tool-Stil (gelbe Section-Headings)

**Excel-Export**
- Erstellt `.xlsx` Dateien mit `openpyxl`
- Dashboard-Sheet + Varianten-Sheets
- Optional: Eingebettete Diagramme
- Professionelle Formatierung (Header, Summen, Grid)

### Data Layer

**MaterialRepository** - CSV-Verwaltung
- Auto-Erkennung: Trennzeichen (`;`, `,`, `\t`) und Dezimalformat
- Suche: Volltext, Datensatztyp, Favoriten, EN 15804+A2 Filter
- **Favoriten-Persistierung**: Speichern/Laden aus config.json
- Favoriten-Mapping bei CSV-Wechsel
- **Custom Materials**: Eigene EPDs laden/speichern/löschen

### UI Layer

**WelcomeWindow** - Startbildschirm
- **Liste der zuletzt geöffneten Projekte** (sortiert nach letzter Nutzung)
- Zeigt interne UND externe Projekte
- Neues Projekt / Projekt öffnen (mit intelligentem Startverzeichnis)
- Merkt sich letztes Öffnen-Verzeichnis in `config.json`

**MainWindow** - Hauptfenster
- Layout: ProjectTree (links) + Tab-Area (rechts)
- Tabs: Dashboard + 5 Varianten
- Menü: CSV laden, Export, **Undo/Redo**, **Info**, Theme-Toggle
- **Info-Dialog**: Programminformationen mit normative Grundlagen, Features und PDF-Opener
  - Öffnet Entwurfstafeln-PDF per Knopfdruck
  - PDF wird in .app Bundle eingebunden
- **Projekt öffnen**: Öffnet ProjectPickerDialog statt einfachem File-Browser
- **Keyboard-Shortcuts**:
  - Mac: Cmd+Z (Undo), Cmd+Shift+Z (Redo)
  - Windows/Linux: Ctrl+Z (Undo), Ctrl+Y / Ctrl+Shift+Z (Redo)

**ProjectPickerDialog** - Projektwechsel im laufenden Programm
- Liste der zuletzt geöffneten Projekte (wie WelcomeWindow)
- "Durchsuchen"-Button mit intelligentem Startverzeichnis
- Zeigt Projektnamen und letzte Änderung
- Modal-Dialog für schnellen Projektwechsel

**DashboardView** - Vergleichsansicht (Tab 1)
- Gestapeltes Balkendiagramm mit **zentral verwalteten Farben**
- **Source of Truth** für Material-Farben (alle sichtbaren Varianten)
- Ruft `orchestrator.update_material_colors(visible_indices)` beim Rendern auf
- **Manuelle Legende** (alphabetisch sortiert, horizontal + vertikal zentriert)
- **Material-Übersichtstabellen** (2x2 Grid, dynamische Höhe)
- Vertikales Scrolling
- Systemgrenze-Dropdown (6 Optionen)
- Varianten-Checkboxen

**VariantView** - Einzelvariante (Tabs 2-6)
- **Einheitliche Diagramme** (8x3.5 Zoll, festes Layout)
- Vertikale Balken mit **manueller Legende** rechts (alphabetisch)
- Nutzt `orchestrator.get_material_color()` für **konsistente Farben**
- Überschreibt KEINE Farben (falls vom Dashboard bereits gesetzt)
- Material-Tabelle (Treeview, 8 Zeilen)
- **Inline-Mengenbearbeitung** (Doppelklick)
- Buttons: Add/Delete, Move Up/Down
- **Intelligente Summen-Anzeige** (Fußzeile):
  - Zeigt Σ A, Σ A+C, Σ A+C+D (wenn D-Werte vorhanden)
  - Automatische Umschaltung zwischen Standard/Bio basierend auf Systemgrenze
  - Bio-Werte in grün angezeigt mit "(bio)" Suffix
  - Keine doppelte Anzeige mehr

**MaterialPickerDialog** - Materialauswahl
- Suchfeld + Filter (Typ, Favoriten, **EN 15804+A2**)
- Tabelle mit Treffern (max. 500)
- **Favoriten-Stern** (★) zum Toggle
- **Custom Materials** mit Rechtsklick-Löschung
- OK / Abbrechen

## 3. Datenfluss - Beispiel

**Material zu Variante hinzufügen:**

```
User klickt "+ Zeile"
    ↓
VariantView.add_row()
    ↓
Orchestrator.add_material_row(idx)
    → Erstellt MaterialRow
    → variant.add_row(row)
    → notify_change() → Autosave (800ms)
    ↓
VariantView öffnet MaterialPickerDialog
    ↓
Dialog: orchestrator.search_materials()
    → MaterialRepository.search()
    → Zeigt Treffer
    ↓
User wählt Material
    ↓
Dialog-Callback: on_select(material)
    ↓
Orchestrator.update_material_row(idx, row_id, material)
    → CalculationService.update_material_row()
        → Kopiert Material-Daten
        → calc_gwp() → Berechnet Werte
    → variant.calculate_sums()
    → notify_change()
    → state.trigger('row_updated')
    ↓
Event-Handler in Views:
    → VariantView: Tabelle + Chart neu laden
    → DashboardView: Vergleichsdiagramm neu laden
    ↓
Autosave (nach Debounce):
    → PersistenceService.save_project()
    → PersistenceService.save_snapshot()
```

## 4. Persistenz-Strategie

**Verzeichnisstruktur:**
```
~/.abc_co2_bilanzierer/
├── config.json              # Einstellungen + Favoriten + Projektverwaltung
├── projects/                # Interne Projekte (optional)
│   └── <uuid>.json         # Projekt-Dateien (intern gespeichert)
├── snapshots/
│   └── <project-id>/
│       └── autosave_*.json # Max. 20
└── logs/
    └── app.log             # Logging

Externe Projekte:
Beliebige Speicherorte möglich (Desktop, Cloud-Ordner, USB, etc.)
- ~/Desktop/MeinProjekt.json
- ~/iCloud/Projekte/Bauwerk_A.json
- /Volumes/USB/projekt_xyz.json
```

**config.json Struktur:**
```json
{
  "last_project_id": "uuid",
  "global_csv_path": "/path/to/OBD.csv",
  "favorites": ["mat-id-1", "mat-id-2"],
  "favorite_names": ["Material Name 1", "Material Name 2"],
  "theme": "dark",
  "window_size": [1400, 900],
  "recent_projects": [
    "uuid-1",
    "uuid-2",
    "uuid-3"
  ],
  "external_project_paths": {
    "uuid-1": "/Users/name/Desktop/Projekt_A.json",
    "uuid-2": "/Users/name/iCloud/Projekt_B.json"
  },
  "last_open_directory": "/Users/name/Desktop"
}
```

**Autosave-Logik:**
1. UI-Änderung → `orchestrator.notify_change()`
2. Timer (800ms Debounce) startet
3. Bei erneutem `notify_change()` → Timer reset
4. Nach Ablauf → `save_project()` + `save_snapshot()`
5. Cleanup: Älteste Snapshots > 20 löschen

**Auto-Restore:**
- Beim `load_project()`: Vergleiche Timestamp
- Wenn Snapshot neuer → restore aus Snapshot

## 5. CSV-Verarbeitung

**Auto-Erkennung:**
```python
1. Lese erste 8KB
2. Zähle Vorkommen: ';', ',', '\t'
3. Bestimme Trenner:
   - ';' count > ',' → Separator=';', Decimal=','
   - ',' count > ';' → Separator=',', Decimal='.'
   - '\t' vorhanden → Separator='\t', Decimal='.'
```

**Flexible Spalten-Zuordnung:**
- `id` / `ID` / `uuid` / `UUID`
- `name` / `Name` / `Bezeichnung`
- `gwp_a1a3` / `GWP_A1-A3` / `A1-A3`
- etc.

## 6. Berechnungslogik

**Nach DIN EN 15804:**

```python
# Modul A1-A3 (Herstellung)
result_a = quantity × material.gwp_a1a3

# Module A1-A3 + C3 + C4 (+ Entsorgung)
result_ac = quantity × (gwp_a1a3 + gwp_c3 + gwp_c4)

# Optional: + D (Gutschriften)
result_acd = result_ac + (quantity × gwp_d)
```

**Systemgrenzen (6 Optionen):**

Standard-Deklaration:
- A1-A3: Nur Herstellung
- A1-A3+C3+C4: Mit Entsorgung
- A1-A3+C3+C4+D: Mit Gutschriften

Bio-korrigierte Deklaration:
- A1-A3 (bio): Mit biogenem Kohlenstoff
- A1-A3+C3+C4 (bio): Herstellung + Entsorgung, bio-korrigiert
- A1-A3+C3+C4+D (bio): Mit Gutschriften, bio-korrigiert

**Fehlende Module:**
- C3/C4/D nicht vorhanden → automatisch 0
- Flag `c_modules_missing` / `d_module_missing` setzen
- Im UI anzeigen

## 7. Zentrale Farbverwaltung (Version 2.0)

**Problem:** Materialien hatten zuvor unterschiedliche Farben in Dashboard, Varianten-GUI und PDF-Export. Zudem änderten sich Farben beim An-/Abwählen von Varianten im Dashboard.

**Lösung:** Zentrale Farbverwaltung im `AppOrchestrator`

**Architektur:**

```python
# In core/orchestrator.py
class StateStore:
    material_colors: Dict[str, Tuple[float, float, float]] = {}
    
class AppOrchestrator:
    def update_material_colors(self, visible_variant_indices: List[int]):
        """
        Aktualisiert zentrale Farbzuordnung basierend auf sichtbaren Varianten
        - Sammelt alle Materialien aus sichtbaren Varianten
        - Sortiert alphabetisch
        - Weist Farben aus plt.cm.tab20.colors zu
        - Speichert in self.state.material_colors
        """
        
    def get_material_color(self, material_name: str) -> Tuple[float, float, float]:
        """
        Gibt konsistente Farbe für Material zurück
        - Falls nicht vorhanden: Standard-Farbe
        """
```

**Hierarchie:**

1. **Dashboard** = "Source of Truth"
   - Ruft `update_material_colors(visible_indices)` beim Rendern
   - Berücksichtigt ALLE sichtbaren Varianten
   - Setzt Farben für alle Materialien

2. **Varianten-GUI**
   - Nutzt `get_material_color(name)` für Balken & Legende
   - Überschreibt KEINE Farben (nur wenn noch nicht gesetzt)
   - Manuelle Legende (alphabetisch sortiert)

3. **PDF-Export**
   - `PDFChartCreator` erhält Orchestrator-Instanz
   - Nutzt gleiche API wie GUI: `get_material_color(name)`
   - Identische Farben wie in GUI-Ansicht

**Vorteile:**
- ✅ Konsistente Farben über alle Views
- ✅ Alphabetische Sortierung für reproduzierbare Zuordnung
- ✅ Keine doppelte Logik (DRY-Prinzip)
- ✅ Einfache Wartung & Erweiterbarkeit

## 8. Erweiterbarkeit

**Neue Umweltindikatoren hinzufügen:**

1. In `Material`: Neue Attribute + `additional_indicators` Dict
2. In `CalculationService`: Neue Berechnungsmethoden
3. In UI: Neue Tabellenspalten + Diagramme

**Neue Systemgrenzen:**

1. In `Project.system_boundary`: Neue Option
2. In `CalculationService.get_sum_for_boundary()`: Fall hinzufügen
3. In Dashboard/Variant: Dropdown erweitern

**PDF-Export implementieren:**

```python
# In orchestrator.py
def export_pdf(output_path, ...):
    # 1. Matplotlib-Charts als PNG speichern
    # 2. HTML-Template mit eingebetteten Bildern
    # 3. Mit reportlab oder weasyprint zu PDF
    # 4. Oder: HTML → Browser Print Dialog
```

## 8. Konventionen

**Code-Style:**
- Type Hints überall
- Docstrings für public methods
- Logging statt print()
- Exceptions mit logging.error()

**Naming:**
- Klassen: PascalCase
- Methoden/Funktionen: snake_case
- Private: _leading_underscore
- Callbacks: on_event_name()

**File Organization:**
- Ein Modul = Eine Verantwortlichkeit
- UI-Komponenten in eigenem Package
- Models ohne Business-Logik

---

**Version:** 2.0  
**Stand:** November 2024  
**App-Name:** CO₂-Bilanzierer

**Änderungen in 2.0:**
- **ℹ️ Info-Dialog** mit Programminformationen
  - Normative Grundlagen (DIN EN 15804, ISO 21931-1, ISO 14040/14044)
  - Feature-Übersicht
  - PDF-Opener für Entwurfstafeln (eingebunden in .app Bundle)
- **🎨 Farb-Konsistenz verbessert**
  - Materialfarben basieren auf ALLEN Materialien im Projekt
  - Farben bleiben konstant beim An-/Abwählen von Dashboard-Varianten
  - Konsistente Farben über Dashboard, Varianten-Tabs und PDF-Export
- **✏️ Umbenennungs-Funktionen mit Undo-Support**
  - Projektnamen ändern (mit Undo)
  - Variantennamen ändern (mit Undo)
  - Label "Projektname:" vor Eingabefeld für bessere UX

**Änderungen in 1.3.0:**
- **🔄 Undo/Redo-System** (max. 10 Schritte)
  - Stack-basierte History mit Deep Copy
  - Keyboard-Shortcuts (Cmd+Z / Ctrl+Z)
  - Zentrierte Buttons in Menüleiste
  - Loop-Prevention und automatisches Redo-Clearing
  - Integration mit allen State-ändernden Operationen
  - Separate Undo-Schritte für Zeile hinzufügen und Material auswählen

**Änderungen in 1.2.0:**
- Flexible UUID-basierte Projektverwaltung
- Externe Projekte mit automatischer Pfad-Aktualisierung
- "Speichern unter" erstellt neues unabhängiges Projekt
- ProjectPickerDialog für schnellen Projektwechsel
- Intelligente Summen-Anzeige mit Auto-Umschaltung Standard/Bio
- A+C+D Summe in Fußzeile
