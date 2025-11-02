# ABC-CO₂-Bilanzierer

Desktop-Anwendung für die Ökobilanzierung von Bauwerken nach ABC-Entwurfstafeln (Stand 2024-02) mit Schwerpunkt auf CO₂-Äquivalent (GWP).

## Normative Grundlagen

- **DIN EN 15804:2012 + A2:2019 + AC:2021** - Umweltproduktdeklarationen
- **DIN EN 15978-1 (Entwurf 2024-05)** - Systemgrenzen und Berichtsstruktur
- **ABC-Entwurfstafeln "Ökobilanzierung in der Tragwerksplanung"** (Stand 2024-02)
- **ÖKOBAUDAT-Struktur** - Datensatztypen und Klassifikation

## Features

### ✅ Vollständig implementiert

- **Modulare Architektur** mit strikter Trennung (Models, Core, Services, UI)
- **CSV-Auto-Erkennung** (Trennzeichen und Dezimalformat)
- **Materialdatenbank-Verwaltung** mit Suche, Filterung und **persistenten Favoriten**
- **5 Bauwerksvarianten** parallel bearbeitbar
- **6 Systemgrenzen** (Standard + bio-korrigiert):
  - A1-A3 / A1-A3 (bio)
  - A1-A3 + C3 + C4 / A1-A3 + C3 + C4 (bio)
  - A1-A3 + C3 + C4 + D / A1-A3 + C3 + C4 + D (bio)
- **Dashboard** mit Variantenvergleich:
  - Gestapeltes Balkendiagramm mit konsistenten Farben
  - Vollständige Legende (horizontal + vertikal zentriert)
  - Material-Übersichtstabellen (2x2 Grid, dynamische Höhe)
  - Vertikales Scrolling für alle Varianten
- **Variantenansichten** mit:
  - Kompakte Einzeldiagramme (einheitliche Größe)
  - Vertikale Balken mit vollständiger Legende rechts
  - Inline-Mengenbearbeitung (Doppelklick)
  - Zeilen verschieben (↑ ↓)
- **Material-Picker-Dialog** mit:
  - Live-Suche und Favoriten-Markierung (★)
  - EN 15804+A2 Filter (Standard aktiviert)
  - Datensatztyp-Filter
- **Custom Materials** - Eigene EPDs hinzufügen/löschen
- **Autosave & Snapshots** (max. 20 pro Projekt, Debounce 800ms)
- **Persistenz** im Benutzerverzeichnis mit **Favoriten-Speicherung**
- **Demo-Projekt** beim ersten Start (3 Varianten: Holzbau, Stahlbau, Stahlbetonbau)
- **Dark/Light-Mode** umschaltbar mit optimierten Kontrasten
- **Logging** in Datei (logs/app.log)

### 🚧 TODO (in kommenden Versionen)

- **PDF-Export** für Reports
- **Erweiterte Umweltindikatoren** (EN 15804+A2: PENRT, AP, EP, etc.)
- **Dateibaum** mit Ordner-/Unterordner-Struktur
- **Einheiten-Konvertierung** (aktuell: Eingabe in CSV-Einheit)
- **Erweiterte Diagrammoptionen** (Legenden, Export als PNG)

## Installation

### Voraussetzungen

- Python 3.9 oder höher
- macOS / Windows / Linux

### Setup

```bash
# Repository klonen oder entpacken
cd CO2-Bilanzierung

# Virtuelle Umgebung erstellen (empfohlen)
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# oder: venv\Scripts\activate  # Windows

# Dependencies installieren
pip install -r requirements.txt

# Programm starten
python app.py
```

## Projektstruktur

```
CO2-Bilanzierung/
├── app.py                      # Einstiegspunkt
├── requirements.txt            # Python-Dependencies
├── README.md                   # Diese Datei
├── ARCHITEKTUR.md             # Detaillierte Architekturübersicht
│
├── models/                     # Datenmodelle
│   ├── material.py            # Material (CSV-Zeile/EPD)
│   ├── variant.py             # Bauwerksvariante mit Materialzeilen
│   └── project.py             # Projekt (Container für Varianten)
│
├── core/                       # Kernlogik
│   ├── orchestrator.py        # Zentrale Steuerungseinheit
│   └── persistence.py         # Speichern/Laden (JSON)
│
├── services/                   # Business-Logik
│   └── calculation_service.py # CO₂-Berechnungen
│
├── data/                       # Daten-Layer
│   └── material_repository.py # CSV-Verwaltung
│
├── ui/                         # Benutzeroberfläche
│   ├── welcome_window.py      # Startbildschirm
│   ├── main_window.py         # Hauptfenster
│   ├── project_tree.py        # Dateibaum (links)
│   ├── dashboard/
│   │   └── dashboard_view.py  # Vergleichsdiagramm (Tab 1)
│   ├── variants/
│   │   └── variant_view.py    # Variantenansicht (Tabs 2-6)
│   └── dialogs/
│       └── material_picker.py # Material-Such-Dialog
│
└── utils/                      # Hilfsfunktionen
    ├── demo_project.py        # Demo-Projekt-Generator
    └── logging_config.py      # Logging-Setup
```

## Verwendung

### 1. Programmstart

Beim ersten Start wird automatisch ein **Demo-Projekt** mit 3 Varianten erstellt:
- Massivbau
- Holzbau
- Hybrid (Holz/Beton)

### 2. CSV-Datenbank laden

1. Klicken Sie auf **"CSV laden"** in der Menüleiste
2. Wählen Sie Ihre ÖKOBAUDAT-kompatible CSV-Datei
3. Das Programm erkennt automatisch:
   - Trennzeichen (`;`, `,`, `\t`)
   - Dezimalformat (`,` oder `.`)

**Erwartete CSV-Spalten** (flexibel):
- `id` / `ID` / `uuid`
- `name` / `Name` / `Bezeichnung`
- `type` / `Typ` / `dataset_type` / `Datensatztyp`
- `source` / `Quelle` / `Hersteller`
- `unit` / `Einheit`
- `gwp_a1a3` / `GWP_A1-A3` / `A1-A3`
- `gwp_c3` / `GWP_C3` / `C3`
- `gwp_c4` / `GWP_C4` / `C4`
- `gwp_d` / `GWP_D` / `D` (optional)

### 3. Varianten bearbeiten

1. Wechseln Sie zu einem Varianten-Tab (2-6)
2. Klicken Sie **"+ Zeile hinzufügen"**
3. Im Material-Picker-Dialog:
   - Suchen Sie nach Materialname, ID oder Quelle
   - Filtern Sie nach Datensatztyp
   - Wählen Sie ein Material aus
4. Doppelklicken Sie auf die Menge, um sie zu bearbeiten
5. Das Programm berechnet automatisch die CO₂-Werte

### 4. Systemgrenze wählen

Im **Dashboard** können Sie die Systemgrenze wählen:
- **A1-A3**: Nur Herstellung
- **A1-A3+C3+C4**: Herstellung + Entsorgung
- **A1-A3+C3+C4+D**: Mit Gutschriften (falls vorhanden)

### 5. Varianten vergleichen

Im **Dashboard** (Tab 1):
- Gestapeltes Balkendiagramm zeigt alle Varianten
- Checkboxen zum Ein-/Ausblenden einzelner Varianten
- Automatische Aktualisierung bei Änderungen

### 6. Autosave

- Automatische Speicherung **800ms** nach jeder Änderung
- Snapshots (max. 20) im Verzeichnis `~/.abc_co2_bilanzierer/snapshots/`
- Automatische Wiederherstellung des neuesten Snapshots beim Start

## Datenverzeichnis

Alle Daten werden im Benutzerverzeichnis gespeichert:

**macOS/Linux**: `~/.abc_co2_bilanzierer/`  
**Windows**: `%APPDATA%/abc_co2_bilanzierer/`

```
.abc_co2_bilanzierer/
├── config.json                 # Konfiguration (inkl. Favoriten)
├── projects/
│   ├── <project-id>.json      # Projekt-Dateien
│   └── ...
├── snapshots/
│   ├── <project-id>/
│   │   ├── autosave_<timestamp>.json
│   │   └── ...
│   └── ...
└── logs/
    └── app.log                 # Log-Datei
```

**config.json** enthält:
- Zuletzt geöffnetes Projekt
- CSV-Pfad (global)
- **Material-Favoriten** (persistiert über Sitzungen)
- Theme-Einstellungen
- Fenstergrößen

## Entwicklung

### Code-Konventionen

- **Python 3.9+ Type Hints** in allen Modulen
- **Docstrings** für alle Klassen und öffentlichen Methoden
- **Logging** statt print() für Debugging
- **Strikte Trennung** zwischen UI, Business-Logik und Daten

### Architektur

Siehe **ARCHITEKTUR.md** für detaillierte Informationen über:
- Schichtenarchitektur
- Datenfluss
- Event-System
- Erweiterungspunkte

## Lizenz

Dieses Projekt ist für Bildungs- und Forschungszwecke entwickelt.

## Kontakt & Support

Bei Fragen oder Problemen erstellen Sie bitte ein Issue im Repository.

---

**Version**: 1.0.0  
**Stand**: November 2024
