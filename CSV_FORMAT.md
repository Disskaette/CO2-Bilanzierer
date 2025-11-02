# ÖKOBAUDAT CSV-Format Dokumentation

## Format-Übersicht

Die ÖKOBAUDAT-CSV hat ein spezielles Format:
- **Ein Material = Mehrere Zeilen** (eine Zeile pro Modul)
- **Eindeutige ID**: UUID-Spalte identifiziert das Material
- **Module**: A1-A3, A4, A5, C1, C2, C3, C4, D

## Wichtige Spalten

| Spalte | Beschreibung | Beispiel |
|--------|--------------|----------|
| `UUID` | Eindeutige Material-ID | `c93da4c3-94c9-4c86-b092-610cf1cf012f` |
| `Name (de)` | Deutscher Name | `FOAMGLAS® T4+` |
| `Typ` | Datensatztyp (Englisch!) | `specific dataset` |
| `Bezugseinheit` | Einheit | `kg`, `m³`, `m²` |
| `Modul` | Lebenszyklusmodul | `A1-A3`, `C3`, `C4`, `D` |
| `GWPtotal (A2)` | CO₂-Äquivalent-Wert | `1,43` |
| `Declaration owner` | Hersteller/Quelle | `Pittsburgh Corning Europe NV` |

## Datensatztypen (Mapping)

Die CSV verwendet **englische** Begriffe, das UI zeigt **deutsche** an:

| CSV (Englisch) | UI (Deutsch) | Beschreibung |
|----------------|--------------|--------------|
| `generic dataset` | generisch | Allgemeine Durchschnittswerte |
| `specific dataset` | spezifisch | Herstellerspezifische EPDs |
| `average dataset` | durchschnitt | Durchschnitt mehrerer Produkte |
| `representative dataset` | repräsentativ | Repräsentativ für eine Produktgruppe |
| `template dataset` | vorlage | Vorlagen-Datensätze |

## Module (Lebenszyklusanalyse nach EN 15804)

### Produktionsphase
- **A1-A3**: Herstellung (Rohstoffgewinnung bis Werkstor)

### Transportphase
- **A4**: Transport zur Baustelle
- **A5**: Einbau

### Nutzungsphase
- **B1-B7**: Nutzung, Instandhaltung, Reparatur, Austausch, Umbau

### Entsorgungsphase
- **C1**: Rückbau/Abriss
- **C2**: Transport zur Entsorgung
- **C3**: Abfallbehandlung
- **C4**: Deponie

### Gutschriften
- **D**: Wiederverwendungs-, Rückgewinnungs- und Recyclingpotenzial

## Wichtig für die Implementierung

### 1. GWP-Werte
Die CO₂-Werte stehen in **`GWPtotal (A2)`**, NICHT in `GWP`!

```python
gwp_str = row.get('GWPtotal (A2)', row.get('GWP', '0'))
```

### 2. Zeilen gruppieren
Materialien müssen nach UUID gruppiert werden:

```python
materials_dict = {}
for row in reader:
    uuid = row.get('UUID')
    if uuid not in materials_dict:
        materials_dict[uuid] = {...}
    modul = row.get('Modul')
    gwp = row.get('GWPtotal (A2)')
    materials_dict[uuid]['modules'][modul] = gwp
```

### 3. Typ-Übersetzung
Englische Typen müssen zu Deutsch übersetzt werden:

```python
TYPE_MAPPING_REVERSE = {
    'generic dataset': 'generisch',
    'specific dataset': 'spezifisch',
    'average dataset': 'durchschnitt',
    'representative dataset': 'repräsentativ',
    'template dataset': 'vorlage'
}
```

## Statistik (Beispiel-CSV mit 26076 Zeilen)

| Datensatztyp | Anzahl Materialien |
|--------------|---------------------|
| generisch | 570 |
| spezifisch | 1468 |
| durchschnitt | 832 |
| repräsentativ | 57 |
| vorlage | 61 |
| **Gesamt** | **2988** |

## Beispiel-Zeilen

```csv
UUID;Name (de);Typ;Bezugseinheit;Modul;GWPtotal (A2)
c93da4c3...;FOAMGLAS® T4+;specific dataset;kg;A1-A3;1,43
c93da4c3...;FOAMGLAS® T4+;specific dataset;kg;A4;0,0296
c93da4c3...;FOAMGLAS® T4+;specific dataset;kg;C3;0,00241
c93da4c3...;FOAMGLAS® T4+;specific dataset;kg;C4;0,0153
c93da4c3...;FOAMGLAS® T4+;specific dataset;kg;D;-0,0479
```

→ Ergibt **1 Material** mit:
- GWP A1-A3: 1,43 kg CO₂-Äq/kg
- GWP C3: 0,00241 kg CO₂-Äq/kg
- GWP C4: 0,0153 kg CO₂-Äq/kg
- GWP D: -0,0479 kg CO₂-Äq/kg (negativ = Gutschrift!)

## Filter-Funktionalität

### Suche nach Namen
```python
repo.search(query="Beton", dataset_type=None)
# → 335 Materialien
```

### Filter nach Typ
```python
repo.search(query="Beton", dataset_type="spezifisch")
# → 262 Materialien
```

### Nur Favoriten
```python
repo.search(query="", dataset_type=None, favorites_only=True)
# → Nur gespeicherte Favoriten (persistiert in config.json)
```

### EN 15804+A2 Filter
```python
repo.search(query="Beton", en15804_a2_only=True)
# → Nur Materialien mit conformity="EN 15804+A2"
# Standard-aktiviert im Material-Picker-Dialog
```

### Kombinierte Filter
```python
repo.search(
    query="Holz",
    dataset_type="spezifisch",
    favorites_only=True,
    en15804_a2_only=True
)
# → Spezifische Holz-EPDs, die favorisiert sind und EN 15804+A2 entsprechen
```

## Custom Materials

Eigene EPDs können als **custom_materials.csv** im gleichen Verzeichnis wie die Haupt-CSV gespeichert werden:

```csv
UUID;Name;Quelle;Datensatztyp;Einheit;GWP_A1-A3;GWP_C3;GWP_C4;GWP_D;biogenic_carbon;conformity
c1234...;Eigene EPD;Hersteller XY;Eigene EPD;m³;125.5;2.3;1.2;-5.0;-10.5;Eigene EPD
```

**Unterschiede zur Haupt-CSV:**
- Eine Zeile pro Material (nicht pro Modul)
- Dezimalpunkt (`.`) statt Komma
- Separator: Semikolon (`;`)
- Spalte `biogenic_carbon` für bio-korrigierte Werte

**Im UI:**
- Custom Materials werden mit dem Tag "Eigene EPD" markiert
- Löschbar über Rechtsklick im Material-Picker
- Bleiben nach Neustart erhalten

## Favoriten-Persistierung

Favoriten werden in `~/.abc_co2_bilanzierer/config.json` gespeichert:

```json
{
  "favorites": [
    "c93da4c3-94c9-4c86-b092-610cf1cf012f",
    "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  ],
  "favorite_names": [
    "FOAMGLAS® T4+",
    "Brettschichtholz - Sonderformen"
  ]
}
```

**Funktionsweise:**
- Beim Programm-Start werden Favoriten aus config.json geladen
- Nach CSV-Laden werden IDs und Namen gemappt
- Änderungen werden sofort gespeichert
- Favoriten bleiben über Sitzungen hinweg erhalten

## Qualitätsprüfung

Vor dem Laden einer CSV sollte geprüft werden:
1. ✅ UTF-8 Encoding
2. ✅ Semikolon als Trennzeichen
3. ✅ Komma als Dezimaltrennzeichen
4. ✅ Spalten `UUID`, `Modul`, `GWPtotal (A2)` vorhanden
5. ✅ Mindestens ein Material mit A1-A3-Modul
6. ✅ Optional: `conformity` Spalte für EN 15804+A2 Filter

---

**Stand:** November 2024  
**ÖKOBAUDAT-Version:** Kompatibel mit aktuellem Format
