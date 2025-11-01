# ABC-CO₂-Bilanzierer - Architekturübersicht

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
- Projects: JSON-Dateien
- Snapshots: Max. 20 pro Projekt
- Auto-Restore beim Start

### Services

**CalculationService** - CO₂-Berechnungen
```python
calc_gwp(material, quantity, boundary):
    gwp_a = quantity × gwp_a1a3
    gwp_ac = quantity × (gwp_a1a3 + gwp_c3 + gwp_c4)
    gwp_acd = gwp_ac + (quantity × gwp_d)
```

### Data Layer

**MaterialRepository** - CSV-Verwaltung
- Auto-Erkennung: Trennzeichen (`;`, `,`, `\t`) und Dezimalformat
- Suche: Volltext, Datensatztyp, Favoriten
- Favoriten-Mapping bei CSV-Wechsel

### UI Layer

**WelcomeWindow** - Startbildschirm
- Zuletzt geöffnete Projekte
- Neues Projekt / Projekt öffnen

**MainWindow** - Hauptfenster
- Layout: ProjectTree (links) + Tab-Area (rechts)
- Tabs: Dashboard + 5 Varianten
- Menü: CSV laden, Export, Theme-Toggle

**DashboardView** - Vergleichsansicht (Tab 1)
- Gestapeltes Balkendiagramm (Matplotlib)
- Systemgrenze-Dropdown
- Varianten-Checkboxen

**VariantView** - Einzelvariante (Tabs 2-6)
- Kleines Diagramm (oben)
- Material-Tabelle (Treeview)
- Buttons: Add/Delete, Move Up/Down
- Summen (unten)

**MaterialPickerDialog** - Materialauswahl
- Suchfeld + Filter (Typ, Favoriten)
- Tabelle mit Treffern (max. 500)
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
├── config.json              # Einstellungen
├── projects/
│   └── <uuid>.json         # Projekt-Dateien
├── snapshots/
│   └── <project-id>/
│       └── autosave_*.json # Max. 20
└── logs/
    └── app.log             # Logging
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

**Systemgrenzen:**
- A1-A3: Nur Herstellung
- A1-A3+C3+C4: Mit Entsorgung
- A1-A3+C3+C4+D: Mit Gutschriften (falls vorhanden)

**Fehlende Module:**
- C3/C4/D nicht vorhanden → automatisch 0
- Flag `c_modules_missing` / `d_module_missing` setzen
- Im UI anzeigen

## 7. Erweiterbarkeit

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

**Version:** 1.0.0  
**Stand:** November 2024
