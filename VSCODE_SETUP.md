# VS Code Setup für ABC-CO₂-Bilanzierer

## ▶️ Programm mit Play-Button starten

### 1. Debug-Konfiguration ist bereits vorhanden

Die Datei `.vscode/launch.json` wurde automatisch erstellt mit zwei Konfigurationen:

- **"ABC-CO₂-Bilanzierer starten"** - Normaler Start
- **"ABC-CO₂-Bilanzierer (Debug-Modus)"** - Mit erweiterten Debug-Infos

### 2. Programm starten

1. **Öffnen Sie die Run & Debug-Ansicht:**
   - Klicken Sie auf das Play-Symbol in der linken Seitenleiste
   - ODER drücken Sie `Cmd+Shift+D` (macOS) / `Ctrl+Shift+D` (Windows/Linux)

2. **Konfiguration auswählen:**
   - Im Dropdown oben: "ABC-CO₂-Bilanzierer starten" auswählen

3. **Starten:**
   - Klicken Sie auf den grünen Play-Button ▶️
   - ODER drücken Sie `F5`

### 3. Was passiert beim Start

```
1. Python startet app.py
   ↓
2. Orchestrator wird initialisiert
   ↓
3. Logging wird eingerichtet
   → Log-Datei: ~/.abc_co2_bilanzierer/logs/app.log
   ↓
4. Demo-Projekt wird erstellt (beim ersten Mal)
   ↓
5. CSV wird automatisch geladen
   → data/OBD_Datenbank.csv (26076 Materialien!)
   ↓
6. Welcome-Window öffnet sich
   ↓
7. Hauptfenster nach Projektauswahl
```

## 🔧 Fehlerbehebung: Leeres Fenster

### Problem
Das Fenster öffnet sich, bleibt aber leer oder weiß.

### Lösung 1: Dependencies prüfen
```bash
# Alle Dependencies neu installieren
pip install --upgrade -r requirements.txt
```

### Lösung 2: CustomTkinter-Version
```bash
# Spezifische Version installieren
pip install customtkinter==5.2.1 --force-reinstall
```

### Lösung 3: Python-Version prüfen
```bash
# Mindestens Python 3.9 erforderlich
python --version

# Falls älter, Python aktualisieren
```

### Lösung 4: Aus Terminal starten
```bash
# Manchmal hilft direkter Start
cd "/Users/.../CO2-Bilanzierung"
python app.py
```

## 📊 Logs überprüfen

Wenn Probleme auftreten, prüfen Sie die Log-Datei:

```bash
# macOS/Linux
cat ~/.abc_co2_bilanzierer/logs/app.log

# Windows
type %APPDATA%\abc_co2_bilanzierer\logs\app.log
```

**Erfolgreicher Start zeigt:**
```
INFO - ABC-CO₂-Bilanzierer v1.1.0 gestartet
INFO - Lade Standard-CSV: .../data/OBD_Datenbank.csv
INFO - Format erkannt: Trenner=';', Dezimal=','
INFO - CSV geladen: 2988 Materialien
INFO - Favoriten wiederhergestellt: X IDs, Y Namen
INFO - 0 Custom Materials geladen
INFO - Standard-CSV erfolgreich geladen
INFO - Starte Hauptschleife
```

## 🐍 Python Interpreter in VS Code

### Richtigen Interpreter auswählen:

1. Drücken Sie `Cmd+Shift+P` (macOS) / `Ctrl+Shift+P` (Windows)
2. Tippen Sie: "Python: Select Interpreter"
3. Wählen Sie:
   - **Anaconda**: `/opt/anaconda3/bin/python` (wie in Ihrem Fall)
   - **System**: `/usr/bin/python3`
   - **venv**: `./venv/bin/python` (wenn virtuelle Umgebung erstellt)

## ⚙️ Empfohlene VS Code Extensions

- **Python** (Microsoft) - Python-Unterstützung
- **Pylance** (Microsoft) - Intellisense für Python
- **Python Debugger** (Microsoft) - Debug-Funktionen

## 🚀 Shortcuts

| Aktion | Shortcut (macOS) | Shortcut (Windows/Linux) |
|--------|------------------|--------------------------|
| Start/Debug | `F5` | `F5` |
| Run & Debug öffnen | `Cmd+Shift+D` | `Ctrl+Shift+D` |
| Terminal öffnen | `Ctrl+`` | `Ctrl+`` |
| Kommando-Palette | `Cmd+Shift+P` | `Ctrl+Shift+P` |

## 📝 Debug-Konfiguration (launch.json)

Falls Sie die Konfiguration anpassen möchten:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "ABC-CO₂-Bilanzierer starten",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/app.py",
            "console": "integratedTerminal",
            "justMyCode": true,
            "cwd": "${workspaceFolder}",
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            }
        }
    ]
}
```

**Parameter-Erklärung:**
- `program`: Hauptdatei (app.py)
- `console`: Terminal im VS Code verwenden
- `justMyCode`: Nur eigenen Code debuggen (nicht Libraries)
- `cwd`: Arbeitsverzeichnis = Projektordner
- `PYTHONPATH`: Stelle sicher, dass Imports funktionieren

## ✅ Checkliste für erfolgreichen Start

- [ ] Python >= 3.9 installiert
- [ ] Dependencies installiert (`pip install -r requirements.txt`)
- [ ] CSV vorhanden: `data/OBD_Datenbank.csv`
- [ ] Richtiger Python Interpreter in VS Code ausgewählt
- [ ] `.vscode/launch.json` existiert
- [ ] Run & Debug: "ABC-CO₂-Bilanzierer starten" ausgewählt
- [ ] Play-Button ▶️ geklickt oder F5 gedrückt

---

**Bei weiteren Problemen:** Prüfen Sie die Log-Datei oder starten Sie aus dem Terminal mit `python app.py`
