# PDF-Export - Professionelle Implementierung

## Übersicht

Der PDF-Export wurde komplett neu implementiert nach professionellen Standards und gemäß Ihrer Excel-Tool-Vorgabe. Die Implementierung ist modular aufgebaut in 7 separaten Modulen.

## Architektur

### Modul-Struktur

```
services/pdf/
├── __init__.py                 # Package-Initialisierung
├── pdf_config.py              # Konfigurationsklassen
├── pdf_styles.py              # Style-Definitionen
├── pdf_charts.py              # Diagramm-Erstellung
├── pdf_tables.py              # Tabellen-Erstellung
├── pdf_header_footer.py       # Header/Footer-Renderer
└── pdf_export_pro.py          # Hauptklasse (Orchestrator)
```

### Komponenten

#### 1. **pdf_config.py** - Konfigurationsklassen
- `InfoBlock`: Datenstruktur für Info-Blöcke (Methodik, Projektbeschreibung, etc.)
- `ExportConfig`: Zentrale Konfiguration mit allen Export-Optionen
- `PREDEFINED_INFO_BLOCKS`: Vordefinierte Info-Blöcke
- `create_default_config()`: Factory für Standard-Konfiguration

#### 2. **pdf_styles.py** - Style-Definitionen
- `PDFStyles`: Container für alle Text-Styles
- `PDFColors`: Zentrale Farb-Palette
- Styles: ProjectTitle, SectionHeading, BodyText, Comment, Metadata, Disclaimer

#### 3. **pdf_charts.py** - Diagramm-Erstellung
- `PDFChartCreator`: Erstellt Matplotlib-Diagramme
- `create_dashboard_chart()`: Gestapeltes Balkendiagramm
- `create_variant_chart()`: Horizontales Balkendiagramm
- Hohe DPI-Qualität (200 DPI)

#### 4. **pdf_tables.py** - Tabellen-Erstellung
- `PDFTableCreator`: Erstellt ReportLab-Tabellen
- `create_dashboard_table()`: Zusammenfassungstabelle
- `create_variant_table()`: Materialtabelle mit SUMMEN-Zeile
- Formatierung: graue Header, alternierende Zeilen, Grid

#### 5. **pdf_header_footer.py** - Header/Footer
- `PDFHeaderFooter`: Zeichnet Header und Footer auf jeder Seite
- Header: Logo, Projektname, Metadaten, Trennlinie
- Footer: Seitenzahl, Disclaimer, Trennlinie

#### 6. **pdf_export_pro.py** - Hauptklasse
- `PDFExporterPro`: Orchestriert den gesamten Export-Prozess
- Verwendet `BaseDocTemplate` und `PageTemplate`
- Baut Story aus Sektionen (Dashboard, Varianten, Info-Blöcke)

#### 7. **export_dialog_pro.py** - Erweiterter GUI-Dialog
- `ExportDialogPro`: CustomTkinter-Dialog mit allen Optionen
- Checkboxen für: Varianten, Dashboard, Info-Blöcke
- Kommentar-Felder pro Variante
- Logo/Zusatzbild-Auswahl

## Verwendung

### Einfacher Export

```python
from services.pdf import PDFExporterPro, ExportConfig, create_default_config

# Standard-Konfiguration
config = create_default_config()
config.include_variants = [0, 1, 2]  # Varianten 0, 1, 2
config.logo_path = "logo.png"

# Export
exporter = PDFExporterPro()
success = exporter.export(project, config, "output.pdf")
```

### Erweiterte Konfiguration

```python
from services.pdf import ExportConfig, InfoBlock, PREDEFINED_INFO_BLOCKS

config = ExportConfig(
    # Logo
    logo_path="firma_logo.png",
    
    # Dashboard
    include_dashboard=True,
    include_dashboard_chart=True,
    include_dashboard_table=True,
    
    # Varianten
    include_variants=[0, 1, 2],
    include_variant_charts=True,
    include_variant_tables=True,
    
    # Kommentare
    comments={
        0: "Holzbau: Beste CO₂-Bilanz durch hohen Holzanteil",
        1: "Stahlbau: Mittlere CO₂-Bilanz, hohe Festigkeit"
    },
    
    # Zusatzbild
    additional_image_path="projekt_visualisierung.png"
)

# Info-Blöcke hinzufügen
methodik = PREDEFINED_INFO_BLOCKS["methodik"].copy()
methodik.include = True
config.add_info_block(methodik)

# Export
exporter = PDFExporterPro()
success = exporter.export(project, config, "report.pdf")
```

### Eigene Info-Blöcke

```python
from services.pdf import InfoBlock

custom_block = InfoBlock(
    id="bauvorhaben",
    title="Bauvorhaben",
    text="Beschreibung des Bauvorhabens...",
    image_path="bauplan.png",
    include=True
)

config.add_info_block(custom_block)
```

## GUI-Integration

Der Export-Dialog ist in `main_window.py` integriert:

```python
# In main_window.py
from ui.dialogs.export_dialog_pro import ExportDialogPro

def _show_export_menu(self):
    project = self.orchestrator.get_current_project()
    if project:
        ExportDialogPro(self, project)
```

Aufruf über: **Menü → Export**

## Features

### PDF-Layout (wie Excel-Tool)

#### Header (jede Seite)
- Logo oben links (4cm x 2cm)
- Projektname oben rechts (blau, fett, 16pt)
- Datum und Systemgrenze (grau, 9pt)
- Blaue Trennlinie

#### Footer (jede Seite)
- Seitenzahl rechts ("Seite X")
- Disclaimer links (mehrzeilig, 7pt)
- Graue Trennlinie

#### Inhalt
1. **Untertitel**: "CO₂-Bilanzierung Variantenvergleich" (gelber Balken)
2. **Info-Blöcke**: Methodik (optional am Anfang)
3. **Dashboard**: Variantenvergleich
   - Gestapeltes Balkendiagramm
   - Zusammenfassungstabelle
4. **Varianten**: Pro Variante
   - Kommentar-Box (falls vorhanden)
   - Diagramm (horizontale Balken)
   - Materialtabelle mit SUMMEN-Zeile
5. **Info-Blöcke**: Ergebnisse, Projektbeschreibung (am Ende)
6. **Zusatzbild**: Optional am Ende

### Tabellen-Formatierung

**Header:**
- Hintergrund: Grau (#D9D9D9)
- Text: Schwarz, fett, 11pt
- Zentriert

**Daten:**
- Alternierende Zeilen (weiß / hellgrau #F5F5F5)
- Pos: zentriert
- Material: linksbündig
- Zahlen: rechtsbündig
- Grid: schwarze Linien (1pt)

**SUMMEN-Zeile:**
- Hintergrund: Grau (#E0E0E0)
- Text: Fett, 10pt
- "SUMME" rechtsbündig
- Dicke Linie darüber (2pt)

### Diagramme

**Dashboard-Diagramm:**
- Gestapeltes Balkendiagramm
- Legende rechts neben Diagramm
- Grid (Y-Achse, gestrichelt, 30% Transparenz)
- Größe: 16cm x 11cm
- DPI: 200

**Varianten-Diagramm:**
- Horizontales Balkendiagramm
- Materialien auf Y-Achse
- Grid (X-Achse, gestrichelt, 30% Transparenz)
- Größe: 14cm x 9cm
- DPI: 200

## Export-Dialog Optionen

### Dashboard
- ☑ Dashboard einschließen
  - ☑ Dashboard-Diagramm
  - ☑ Dashboard-Tabelle

### Varianten
- ☑ Holzbau
- ☑ Stahlbau
- ☑ Stahlbetonbau
- ...
  - ☑ Varianten-Diagramme
  - ☑ Varianten-Tabellen

### Kommentare
- **Button**: "Kommentare bearbeiten"
  - Öffnet Dialog mit Textfeldern pro Variante
  - Kommentare werden unter Varianten-Überschrift als Box eingefügt

### Info-Blöcke
- ☐ Methodik
- ☐ Projektbeschreibung
- ☐ Zusammenfassung der Ergebnisse

### Bilder
- **Logo**: Durchsuchen... (PNG/JPG, 4cm x 2cm)
- **Zusatzbild**: Durchsuchen... (PNG/JPG, 15cm x 10cm)

## Systemgrenze-Unterstützung

Der Export berücksichtigt automatisch die gewählte Systemgrenze:

- **A1-A3**: Nur Herstellung
- **A1-A3 + C3 + C4**: Herstellung + Entsorgung
- **A1-A3 + C3 + C4 + D**: Mit Gutschriften
- **Mit (bio)**: Biogene Speicherung berücksichtigt

Die Werte werden korrekt aus den MaterialRow-Objekten extrahiert.

## Technische Details

### Dependencies
- `reportlab`: PDF-Erzeugung
- `matplotlib`: Diagramme
- `PIL (pillow)`: Bildverarbeitung
- `customtkinter`: GUI

### Performance
- Diagramme werden in-memory erstellt (BytesIO)
- Keine temporären Dateien
- DPI: 200 (gute Qualität, moderate Dateigröße)

### Fehlerbehandlung
- Try-Catch in allen Methoden
- Logging von Fehlern
- Graceful degradation (fehlende Bilder werden übersprungen)

## Erweiterbarkeit

### Neue Info-Blöcke hinzufügen

In `pdf_config.py`:

```python
PREDEFINED_INFO_BLOCKS["neuer_block"] = InfoBlock(
    id="neuer_block",
    title="Neuer Block",
    text="Text...",
    include=False
)
```

In `export_dialog_pro.py` wird der Block automatisch als Checkbox angezeigt.

### Styles anpassen

In `pdf_styles.py`:

```python
# Neue Farbe hinzufügen
PDFColors.MY_COLOR = colors.HexColor('#ABCDEF')

# Neuen Style erstellen
self.base_styles.add(ParagraphStyle(
    name='MyStyle',
    ...
))
```

### Tabellen-Layout ändern

In `pdf_tables.py`:

```python
# Spaltenbreiten anpassen
table = Table(data, colWidths=[2*cm, 9*cm, 3*cm, 2*cm, 2*cm])

# Style ändern
table.setStyle(TableStyle([...]))
```

## Vergleich: Alt vs. Neu

| Feature | Alt (pdf_export.py) | Neu (services/pdf/) |
|---------|---------------------|---------------------|
| Header/Footer | ❌ Nur Seitenzahl | ✅ Logo, Projektname, Metadaten, Disclaimer |
| Tabellen | ⚠️ Einfach | ✅ Professionell (wie Excel) |
| Diagramme | ⚠️ Basis | ✅ Hohe Qualität (200 DPI) |
| Kommentare | ❌ Keine | ✅ Pro Variante |
| Info-Blöcke | ❌ Keine | ✅ Methodik, Projektbeschreibung, etc. |
| Styles | ⚠️ Einfach | ✅ Professionell (gelbe Balken) |
| Modularität | ❌ Monolithisch | ✅ 7 Module |
| Erweiterbarkeit | ⚠️ Schwierig | ✅ Einfach |

## Zusammenfassung

Der neue PDF-Export ist:

✅ **Professionell**: Layout wie Excel-Tool  
✅ **Modular**: 7 separate Module  
✅ **Flexibel**: Viele Konfigurationsoptionen  
✅ **Erweiterbar**: Neue Features einfach hinzuzufügen  
✅ **Robust**: Umfangreiche Fehlerbehandlung  
✅ **Dokumentiert**: Alle Klassen und Methoden  

Der Export wird über **Menü → Export** aufgerufen und bietet einen erweiterten Dialog mit allen Optionen.
