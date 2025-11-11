# CO₂-Bilanzierer - App erstellen

**Version**: 2.0  
**Letzte Aktualisierung**: November 2024

## 🚀 Schnelle Methode: Automatischer Build

### Schritt 1: Build-Script ausführen

```bash
cd CO2-Bilanzierung
python3 build_app.py
```

Das Script:
- Installiert PyInstaller automatisch
- Erstellt die .spec Datei
- Baut die macOS App
- Legt sie in `dist/ABC-CO₂-Bilanzierer.app` ab

**Dauer:** 2-5 Minuten (beim ersten Mal)

### Schritt 2: App installieren

1. Öffne Finder
2. Navigiere zum Projektordner → `dist/`
3. Ziehe `ABC-CO₂-Bilanzierer.app` in den **Programme-Ordner**
4. Fertig! Die App ist jetzt installiert

### Schritt 3: Desktop-Icon erstellen (Optional)

**Variante A - Alias:**
1. Gehe zu Programme/ABC-CO₂-Bilanzierer.app
2. Rechtsklick → "Alias erstellen"
3. Ziehe Alias auf den Desktop

**Variante B - Dock:**
1. Öffne die App aus dem Programme-Ordner
2. Rechtsklick auf Icon im Dock
3. Optionen → "Im Dock behalten"

---

## 📦 Was macht PyInstaller?

PyInstaller erstellt eine **eigenständige macOS App**, die:
- ✅ **Ohne Python-Installation läuft**
- ✅ **Alle Dependencies enthält** (CustomTkinter, Matplotlib, ReportLab, etc.)
- ✅ **Per Doppelklick startet**
- ✅ **Kein Terminal-Fenster öffnet**
- ✅ **Im Programme-Ordner installierbar ist**
- ✅ **3 Logos inkludiert** (für professionellen PDF-Export)

---

## 🔧 Manuelle Methode

Falls du den Prozess manuell steuern möchtest:

### 1. PyInstaller installieren

```bash
pip install pyinstaller
```

### 2. App bauen

```bash
pyinstaller --clean --noconfirm ABC-CO2-Bilanzierer.spec
```

### 3. Testen

```bash
open dist/ABC-CO₂-Bilanzierer.app
```

---

## 🎨 App-Icon hinzufügen (Optional)

### 1. Icon erstellen

Du benötigst ein Icon im `.icns` Format (macOS-Standard).

**Online-Konverter:**
- [iConvert Icons](https://iconverticons.com/online/)
- Lade ein PNG hoch (512x512 oder 1024x1024)
- Lade die `.icns` Datei herunter

### 2. Icon hinzufügen

1. Speichere die `.icns` Datei als `icon.icns` im Projektordner
2. Öffne `ABC-CO2-Bilanzierer.spec`
3. Ändere Zeile:
   ```python
   icon=None,  # ← Ändere zu:
   icon='icon.icns',
   ```
4. Baue die App neu:
   ```bash
   python3 build_app.py
   ```

---

## ⚠️ macOS Sicherheitshinweis

Beim **ersten Start** zeigt macOS möglicherweise:
> "ABC-CO₂-Bilanzierer kann nicht geöffnet werden, da es von einem nicht verifizierten Entwickler stammt."

### Lösung:

1. **Systemeinstellungen** → **Datenschutz & Sicherheit**
2. Klicke auf **"Trotzdem öffnen"**
3. Bestätige mit deinem Passwort

**Nur beim ersten Mal nötig!** Danach startet die App normal.

---

## 📁 Verzeichnisstruktur nach Build

```
CO2-Bilanzierung/
├── build/                    # Temporäre Build-Dateien (löschbar)
├── dist/
│   └── ABC-CO₂-Bilanzierer.app  # ← FERTIGE APP
├── ABC-CO2-Bilanzierer.spec  # PyInstaller-Konfiguration
└── build_app.py              # Build-Script
```

**Die fertige App:** `dist/ABC-CO₂-Bilanzierer.app`

---

## 🗑️ Build-Dateien löschen

Nach erfolgreicher Installation kannst du aufräumen:

```bash
# Temporäre Build-Dateien löschen
rm -rf build/

# Falls du die App neu bauen möchtest:
rm -rf dist/
python3 build_app.py
```

---

## 🐛 Probleme beim Build?

### Problem: "ModuleNotFoundError"

**Lösung:** Fehlende Dependencies hinzufügen

Öffne `ABC-CO2-Bilanzierer.spec` und füge in `hiddenimports` hinzu:
```python
hiddenimports=[
    'PIL._tkinter_finder',
    'customtkinter',
    'matplotlib',
    'numpy',
    'dein_fehlendes_modul',  # ← Hier hinzufügen
],
```

### Problem: "Icon nicht gefunden"

**Lösung:** Icon-Pfad prüfen

In `ABC-CO2-Bilanzierer.spec`:
```python
icon='icon.icns',  # Stelle sicher, dass die Datei existiert
```

### Problem: App startet nicht

**Debug-Modus aktivieren:**

1. Öffne Terminal
2. Starte App direkt:
   ```bash
   ./dist/ABC-CO₂-Bilanzierer.app/Contents/MacOS/ABC-CO₂-Bilanzierer
   ```
3. Lies Fehlermeldungen im Terminal

---

## 💡 Tipps

### App-Größe reduzieren

Die App ist ~150-200 MB groß (wegen Matplotlib, NumPy & ReportLab). Das ist normal!

**Inkludierte Dateien:**
- OBD_Datenbank.csv (Materialdatenbank)
- 3 Logos für PDF-Export (Hochschule Karlsruhe, Zimmerei Stark, merz kley partner)
- README.md

### Updates verteilen

Bei neuen Versionen:
1. Code aktualisieren
2. Version in `build_app.py` erhöhen (aktuell: 2.0)
3. `python3 build_app.py` erneut ausführen
4. Neue App verteilen

**Version 2.0 Features:**
- ✨ Professioneller PDF-Export (7 Module)
- ✨ Konsistente Material-Farben (Dashboard, Varianten, PDF)
- ✨ Info-Blöcke, Kommentarfelder, Logo-Unterstützung
- ✨ Zentrale Farbverwaltung im Orchestrator

### Für andere weitergeben

Die App funktioniert auf jedem macOS (10.13+) **ohne Python-Installation**!

---

## ✅ Zusammenfassung

```bash
# 1. App bauen
python3 build_app.py

# 2. App installieren
# Ziehe dist/ABC-CO₂-Bilanzierer.app in den Programme-Ordner

# 3. Fertig!
# Starte die App per Doppelklick
```

**Das war's! Du hast jetzt eine eigenständige macOS-App! 🎉**
