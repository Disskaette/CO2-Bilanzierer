# CO₂-Bilanzierer - Schnellstart

## 🚀 Installation & Start (5 Minuten)

### 1. Python installieren

**macOS/Linux:**
```bash
python3 --version  # Sollte >= 3.9 sein
```

**Windows:**
- Download von [python.org](https://www.python.org/downloads/)
- Bei Installation "Add to PATH" aktivieren

### 2. Dependencies installieren

```bash
# In das Projektverzeichnis wechseln
cd CO2-Bilanzierung

# Virtuelle Umgebung erstellen (empfohlen)
python3 -m venv venv

# Aktivieren
source venv/bin/activate      # macOS/Linux
# ODER
venv\Scripts\activate         # Windows

# Packages installieren
pip install -r requirements.txt
```

### 3. Programm starten

```bash
python app.py
```

Das wars! 🎉

## 📋 Erste Schritte

### Beim ersten Start:

1. **Welcome-Screen** öffnet sich
2. Automatisch wird ein **Demo-Projekt** angelegt mit:
   - Variante 1: Holzbau (5 Materialien)
   - Variante 2: Stahlbau (1 Material)
   - Variante 3: Stahlbetonbau (3 Materialien)
3. Klicken Sie auf das Demo-Projekt

### Dashboard erkunden:

- **Tab 1 (Dashboard)**:
  - Vergleichsdiagramm mit **konsistenten Farben** über alle Varianten
  - **Vollständige Legende** rechts (horizontal + vertikal zentriert)
  - **Material-Übersichtstabellen** (2x2 Grid) mit CO₂-Summen
  - Vertikales Scrolling bei vielen Varianten
- **Tabs 2-6**: Einzelne Varianten mit **einheitlichen Diagrammen** und Legenden
- **Systemgrenze** ändern: Dropdown oben (6 Optionen inkl. bio-korrigiert)
- **Varianten ein-/ausblenden**: Checkboxen im Dashboard

### CSV-Datenbank laden:

1. Klicken Sie **"CSV laden"** in der Menüleiste
2. Wählen Sie Ihre ÖKOBAUDAT-CSV aus
3. Fertig - das Programm erkennt Format automatisch!

**CSV-Format-Beispiel:**
```csv
id;name;type;unit;gwp_a1a3;gwp_c3;gwp_c4;gwp_d
1;Stahlbeton C30/37;generisch;m³;320,0;5,0;2,0;-15,0
2;Brettschichtholz GL24h;generisch;m³;185,0;3,0;1,5;-1850,0
```

**Hinweis**: Das Programm akzeptiert:
- Trennzeichen: `;` oder `,` oder Tab
- Dezimalformat: `,` oder `.`
- Auto-Erkennung erfolgt automatisch!

### Material hinzufügen:

1. Wechseln Sie zu einem Varianten-Tab (z.B. Tab 2)
2. Klicken Sie **"+ Zeile hinzufügen"**
3. Im Material-Dialog:
   - Geben Sie Suchbegriff ein (z.B. "Beton")
   - **EN 15804+A2 Filter** ist standardmäßig aktiv ✓
   - Optional: Filter nach Datensatztyp
   - Optional: "Nur Favoriten" für gespeicherte Materialien
   - **Favoriten markieren**: Klick auf ★-Spalte
   - Doppelklick auf Material ODER auswählen + OK
4. **Inline-Bearbeitung**: Doppelklick auf **Menge** in der Tabelle
5. Fertig - CO₂-Werte werden automatisch berechnet!

## 💾 Speicherung

- **Automatisch** nach jeder Änderung (800ms Verzögerung)
- **Speicherort**: `~/.abc_co2_bilanzierer/`
- **Snapshots**: Max. 20 pro Projekt (auto-cleanup)
- **Auto-Restore**: Bei Absturz wird letzter Snapshot geladen

## 🎨 Theme wechseln

Klicken Sie auf **"Theme"** in der Menüleiste.

## 📊 Systemgrenzen

Wählen Sie im Dashboard (6 Optionen):

**Standard-Deklaration:**
| Systemgrenze | Beschreibung |
|--------------|------------|
| **A1-A3** | Nur Herstellung (Product Stage) |
| **A1-A3+C3+C4** | Herstellung + Entsorgung (End of Life) |
| **A1-A3+C3+C4+D** | + Gutschriften (Benefits & Loads) |

**Bio-korrigierte Deklaration:**
| Systemgrenze | Beschreibung |
|--------------|------------|
| **A1-A3 (bio)** | Mit biogenem Kohlenstoff |
| **A1-A3+C3+C4 (bio)** | Herstellung + Entsorgung, bio-korrigiert |
| **A1-A3+C3+C4+D (bio)** | + Gutschriften, bio-korrigiert |

**Hinweis**: Bio-korrigierte Werte berücksichtigen die temporäre CO₂-Speicherung in biogenen Materialien.

## ⭐ Material-Favoriten

**Favoriten werden dauerhaft gespeichert!**

- **Markieren**: Klick auf ★ im Material-Picker
- **Filter**: "Nur Favoriten"-Checkbox aktivieren
- **Speicherort**: `~/.abc_co2_bilanzierer/config.json`
- **Persistierung**: Bleiben nach Neustart erhalten
- **Auto-Mapping**: Bei CSV-Wechsel werden IDs und Namen gemappt

## 🏭 Custom Materials

**Eigene EPDs hinzufügen:**

1. Im Material-Picker: Rechtsklick → "Eigene EPD hinzufügen"
2. Formular ausfüllen (Name, GWP-Werte, etc.)
3. Speichern → Material erscheint in der Liste

**Löschen**: Rechtsklick auf Custom Material → "Löschen"

**Speicherort**: `custom_materials.csv` im gleichen Verzeichnis wie Haupt-CSV

## ⚠️ Wichtige Hinweise

### Mengen-Eingabe:
- **Immer in der Einheit der CSV/EPD eingeben!**
- Einheit wird in Tabelle angezeigt
- Keine automatische Konvertierung (aktuell)

### Fehlende Module:
- Wenn C3/C4/D in CSV fehlen → automatisch 0
- Wird als "nicht belegt" markiert

### Performance:
- Material-Picker zeigt max. 500 Treffer
- Bei großen CSV-Dateien: Suchbegriff eingrenzen
- EN 15804+A2 Filter reduziert Treffermenge

## 🆘 Probleme?

### Programm startet nicht:

```bash
# Python-Version prüfen
python3 --version

# Dependencies neu installieren
pip install --upgrade -r requirements.txt
```

### Fehler beim CSV-Laden:

- **Encoding-Probleme**: CSV sollte UTF-8 sein
- **Spalten fehlen**: Mindestens `name`, `gwp_a1a3` erforderlich
- **Prüfen Sie die Logs**: `~/.abc_co2_bilanzierer/logs/app.log`

### Autosave-Fehler:

- **Berechtigung**: Prüfen Sie Schreibrechte auf `~/.abc_co2_bilanzierer/`
- **Festplatte voll**: Prüfen Sie freien Speicherplatz

## 📚 Weiterführende Dokumentation

- **README.md** - Vollständige Feature-Liste
- **ARCHITEKTUR.md** - Technische Details
- **DIN EN 15804** - Normative Grundlagen

## 🎯 Workflow-Beispiel

**Szenario: Vergleich Massivbau vs. Holzbau**

1. Neues Projekt erstellen
2. CSV laden (ÖKOBAUDAT)
3. Variante 1 "Massivbau":
   - Stahlbeton C30/37: 150 m³
   - Mauerziegel: 800 m²
   - Stahlbewehrung: 25 t
4. Variante 2 "Holzbau":
   - Brettschichtholz: 120 m³
   - Brettsperrholz: 180 m³
   - Holzfaserdämmung: 85 m³
5. Dashboard: Systemgrenze "A1-A3+C3+C4+D" wählen
6. Vergleich im Diagramm → Holzbau zeigt negative Werte durch D-Module!

**Ergebnis**: Direkt sichtbar, welche Variante klimafreundlicher ist.

---

**Viel Erfolg mit der Ökobilanzierung! 🌱**
