# Export-Funktionalität - Anleitung

## Übersicht

Die CO₂-Bilanzierer-App bietet umfassende Export-Möglichkeiten für PDF und Excel.

## Features

### PDF-Export

Der PDF-Export erstellt professionelle Berichte mit:

- **Logo/Kopfzeile**: Platzhalter für Firmenlogo (optional)
- **Projektinformationen**: Name, Datum, Systemgrenze
- **Dashboard-Vergleich**: Gestapeltes Balkendiagramm aller Varianten
- **Zusammenfassungstabelle**: CO₂-Werte aller Varianten
- **Varianten-Details**: Für jede ausgewählte Variante:
  - Individuelles Diagramm
  - Detaillierte Materialtabelle mit CO₂-Werten
- **Zusatzbild**: Optional ein weiteres Bild am Ende (z.B. Lebenszyklusphasen-Tabelle)
- **Seitenzahlen**: Automatische Nummerierung

### Excel-Export

Der Excel-Export erstellt Arbeitsblätter mit:

- **Dashboard-Sheet**: Übersicht aller Varianten mit CO₂-Summen
- **Varianten-Sheets**: Für jede Variante ein separates Sheet mit:
  - Position, Material, Menge, Einheit
  - GWP-Werte (A1-A3, C3, C4, D)
  - Berechnete CO₂-Werte
  - Summenzeile
- **Optional Diagramme**: Balkendiagramme für jede Variante

## Nutzung

### 1. Export-Dialog öffnen

- Klicken Sie auf **"Export"** in der Menüleiste
- Der Export-Dialog öffnet sich

### 2. PDF-Export konfigurieren

**Optionen:**
- ☑ Dashboard-Vergleich einschließen
- ☑ Varianten auswählen (mehrere möglich)
- Logo-Datei auswählen (optional, PNG/JPG)
- Zusatzbild auswählen (optional, PNG/JPG)

**Exportieren:**
- Klicken Sie auf **"Als PDF exportieren"**
- Wählen Sie Speicherort und Dateinamen
- PDF wird erstellt

### 3. Excel-Export konfigurieren

**Optionen:**
- ☐ Diagramme einschließen (optional)

**Exportieren:**
- Klicken Sie auf **"Als Excel exportieren"**
- Wählen Sie Speicherort und Dateinamen
- Excel wird erstellt

## Tipps

### Logo-Vorbereitung

- **Format**: PNG mit Transparenz empfohlen
- **Größe**: Ca. 400x200 Pixel optimal
- **Platzierung**: Wird oben links eingefügt (4cm x 2cm)

### Zusatzbild

- Eignet sich für:
  - Lebenszyklusphasen-Übersicht
  - Projekt-Fotos
  - Zusätzliche Tabellen/Grafiken
- **Format**: PNG, JPG
- **Größe**: Wird auf 15cm x 10cm skaliert

### Systemgrenze beachten

Die exportierten CO₂-Werte entsprechen der im Projekt eingestellten Systemgrenze:
- A1-A3
- A1-A3 + C3 + C4
- A1-A3 + C3 + C4 + D
- Varianten mit biogener Speicherung (bio)

### Excel-Formeln

Die Excel-Datei enthält reine Werte, keine Formeln. Dies ermöglicht:
- Einfaches Weiterverwenden der Daten
- Import in andere Tools
- Keine Abhängigkeiten

## Technische Details

### Verwendete Bibliotheken

- **PDF**: `reportlab` für Layouterstellung, `matplotlib` für Diagramme
- **Excel**: `openpyxl` für .xlsx-Dateien

### Dateigrößen

- PDF: Ca. 100-500 KB (abhängig von Varianten und Bildern)
- Excel: Ca. 20-100 KB (ohne Diagramme kleiner)

### Kompatibilität

- **PDF**: Alle PDF-Reader (Adobe Reader, Preview, etc.)
- **Excel**: Excel 2007+, LibreOffice Calc, Google Sheets

## Fehlerbehebung

### "Fehler beim PDF-Export"

**Ursachen:**
- Logo/Bild-Datei nicht gefunden
- Keine Schreibrechte im Zielordner
- Datei ist bereits geöffnet

**Lösung:**
- Überprüfen Sie Dateipfade
- Wählen Sie anderen Speicherort
- Schließen Sie offene Dateien

### "Fehler beim Excel-Export"

**Ursachen:**
- Keine Schreibrechte
- Datei ist in Excel geöffnet

**Lösung:**
- Schließen Sie die Excel-Datei
- Wählen Sie anderen Speicherort

### Diagramme werden nicht angezeigt

**Ursache:** Matplotlib-Backend-Problem

**Lösung:**
- Starten Sie die Anwendung neu
- Überprüfen Sie matplotlib-Installation:
  ```bash
  pip install --upgrade matplotlib
  ```

## Beispiel-Workflow

1. **Projekt vorbereiten**
   - Alle Varianten erstellen
   - Materialien eingeben
   - Systemgrenze wählen

2. **Export durchführen**
   - Export-Dialog öffnen
   - PDF mit allen Varianten exportieren
   - Excel als Backup/Datenquelle exportieren

3. **Nachbearbeitung**
   - PDF in Präsentationen einbinden
   - Excel-Daten in andere Tools importieren

## Support

Bei Fragen oder Problemen:
- Prüfen Sie die Logs in der Konsole
- Überprüfen Sie die requirements.txt
- Stellen Sie sicher, dass alle Dependencies installiert sind:
  ```bash
  pip install -r requirements.txt
  ```
