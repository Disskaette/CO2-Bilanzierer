"""
Material-Repository - Lädt und verwaltet CSV/ÖKOBAUDAT-Datenbank
"""

import csv
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from datetime import datetime
from collections import Counter

from models.material import Material

logger = logging.getLogger(__name__)


class MaterialRepository:
    """
    Lädt und verwaltet die Materialdatenbank aus CSV
    - Auto-Erkennung von Trennzeichen und Dezimalformat
    - Suchfunktionen nach Name, Typ, Favoriten
    - Favoriten-Verwaltung basierend auf Nutzung
    """

    # Mapping: Deutsch (UI) → Englisch (CSV)
    TYPE_MAPPING = {
        'generisch': 'generic dataset',
        'spezifisch': 'specific dataset',
        'durchschnitt': 'average dataset',
        'repräsentativ': 'representative dataset',
        'vorlage': 'template dataset'
    }

    # Reverse Mapping: Englisch (CSV) → Deutsch (UI)
    TYPE_MAPPING_REVERSE = {v: k for k, v in TYPE_MAPPING.items()}

    def __init__(self):
        self.materials: List[Material] = []
        self.csv_path: Optional[str] = None
        self.loaded_at: Optional[str] = None
        self.separator: str = ";"
        self.decimal: str = ","

        # Favoriten (IDs und Namen)
        self.favorites: Set[str] = set()
        self.favorite_names: Set[str] = set()

        # Verwendungszähler
        self.usage_counter: Counter = Counter()

        self.logger = logger

    def load_csv(
        self,
        path: str,
        encoding: str = 'utf-8'
    ) -> bool:
        """
        Lädt CSV mit Auto-Erkennung von Trennzeichen und Dezimalformat

        Args:
            path: Pfad zur CSV-Datei
            encoding: Text-Encoding

        Returns:
            True bei Erfolg
        """

        try:
            self.logger.info(f"Lade CSV: {path}")

            # Datei öffnen und erste Zeilen lesen
            with open(path, 'r', encoding=encoding, errors='replace') as f:
                sample = f.read(8192)

            # Auto-Erkennung Trennzeichen
            separator, decimal = self._detect_format(sample)
            self.separator = separator
            self.decimal = decimal

            self.logger.info(
                f"Format erkannt: Trenner='{separator}', Dezimal='{decimal}'"
            )

            # CSV einlesen - ÖKOBAUDAT Format (ein Material = mehrere Zeilen)
            materials_dict = {}  # UUID -> Material-Daten

            # Verwende einfach cp1252 (Windows-Standard) - funktioniert für deutsche Umlaute
            # Dies ist schnell und zuverlässig für ÖKOBAUDAT
            used_encoding = 'cp1252'

            try:
                with open(path, 'r', encoding='cp1252') as f:
                    file_content = f.read()
                self.logger.info(f"CSV-Encoding: {used_encoding}")
            except Exception as e:
                # Fallback auf UTF-8
                self.logger.warning(
                    f"cp1252 fehlgeschlagen, verwende UTF-8: {e}")
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                    used_encoding = 'utf-8'
                except Exception:
                    # Letzter Fallback mit errors='replace'
                    with open(path, 'r', encoding='utf-8', errors='replace') as f:
                        file_content = f.read()
                    used_encoding = 'utf-8 (with errors replaced)'
                self.logger.info(f"CSV-Encoding: {used_encoding}")

            # Parse CSV aus String
            from io import StringIO
            reader = csv.DictReader(
                StringIO(file_content), delimiter=separator)

            for idx, row in enumerate(reader):
                try:
                    # UUID als eindeutige ID
                    uuid = row.get('UUID', f"mat_{idx}")

                    # Wenn UUID noch nicht existiert, Basisdaten erstellen
                    if uuid not in materials_dict:
                        # Name: Deutsch bevorzugt, sonst Englisch, sonst Fallback
                        name_de = row.get('Name (de)', '').strip()
                        name_en = row.get('Name (en)', '').strip()
                        name = name_de or name_en or f'Material {idx}'

                        # Einheit und Bezugsgröße auslesen
                        unit = row.get('Bezugseinheit', 'kg')
                        bezugsgroesse_str = row.get('Bezugsgroesse', '1')

                        # Bezugsgröße parsen (kann Komma als Dezimaltrennzeichen haben)
                        try:
                            bezugsgroesse = self._parse_float(
                                bezugsgroesse_str, decimal)
                        except (ValueError, TypeError):
                            bezugsgroesse = 1.0

                        # Wenn Bezugsgröße 1000 und Einheit kg ist, konvertiere zu Tonnen
                        if bezugsgroesse == 1000.0 and unit == 'kg':
                            unit = 't'

                        materials_dict[uuid] = {
                            'uuid': uuid,
                            'name': name,
                            'type': row.get('Typ', 'generisch'),
                            'source': row.get('Declaration owner', ''),
                            'conformity': row.get('Konformitaet', '').strip(),
                            'unit': unit,
                            'bezugsgroesse': bezugsgroesse,  # Speichere für spätere Referenz
                            'modules': {}  # Modul -> GWP-Wert
                        }

                    # Modul und GWP-Wert extrahieren
                    # WICHTIG: ÖKOBAUDAT verwendet "GWPtotal (A2)", nicht "GWP"!
                    modul = row.get('Modul', '').strip()
                    gwp_str = row.get('GWPtotal (A2)', row.get('GWP', '0'))

                    if modul and gwp_str:
                        gwp_value = self._parse_float(gwp_str, decimal)
                        materials_dict[uuid]['modules'][modul] = gwp_value

                    # Biogener Kohlenstoff extrahieren (nur einmal pro Material)
                    if 'biogenic_carbon' not in materials_dict[uuid]:
                        bio_str = row.get('Biogenic carbon content (A1-A3)',
                                          row.get('biogenic_carbon', None))
                        if bio_str:
                            materials_dict[uuid]['biogenic_carbon'] = self._parse_float(
                                bio_str, decimal)
                        else:
                            materials_dict[uuid]['biogenic_carbon'] = None

                except Exception as e:
                    self.logger.warning(f"Fehler in Zeile {idx + 2}: {e}")

            # Materialien aus Dict erstellen
            materials = []
            for uuid, data in materials_dict.items():
                try:
                    material = self._create_material_from_modules(uuid, data)
                    if material:
                        materials.append(material)
                except Exception as e:
                    self.logger.warning(
                        f"Fehler beim Erstellen von Material {uuid}: {e}")

            self.materials = materials
            self.csv_path = path
            self.loaded_at = datetime.now().isoformat()

            self.logger.info(
                f"CSV geladen: {len(materials)} Materialien aus {path}"
            )

            # Favoriten neu mappen
            self._remap_favorites()

            # Custom Materials laden (aus gleichem Verzeichnis)
            custom_count = self.load_custom_materials()
            if custom_count > 0:
                self.logger.info(
                    f"Zusätzlich {custom_count} Custom Materials geladen")

            return True

        except Exception as e:
            self.logger.error(f"Fehler beim Laden der CSV: {e}", exc_info=True)
            return False

    def _detect_format(self, sample: str) -> tuple[str, str]:
        """
        Erkennt Trennzeichen und Dezimalformat

        Reihenfolge:
        1. Semikolon + Komma als Dezimal
        2. Komma + Punkt als Dezimal
        3. Tab + Punkt als Dezimal

        Returns:
            (separator, decimal_char)
        """

        # Zähle mögliche Trenner
        semicolon_count = sample.count(';')
        comma_count = sample.count(',')
        tab_count = sample.count('\t')

        # Strategie 1: Semikolon + Komma
        if semicolon_count > comma_count:
            return ';', ','

        # Strategie 2: Komma + Punkt
        elif comma_count > semicolon_count:
            return ',', '.'

        # Strategie 3: Tab + Punkt
        elif tab_count > 0:
            return '\t', '.'

        # Fallback
        return ';', ','

    def _create_material_from_modules(
        self,
        uuid: str,
        data: Dict[str, Any]
    ) -> Optional[Material]:
        """
        Erstellt Material-Objekt aus gesammelten Modulen

        ÖKOBAUDAT-Module:
        - A1-A3: Herstellung
        - C3: Abfallbehandlung
        - C4: Deponie
        - D: Gutschriften
        - Biogenic carbon: biogene CO2-Speicherung

        Args:
            uuid: Material-UUID
            data: Dict mit name, type, source, unit, modules, biogenic_carbon

        Returns:
            Material-Objekt oder None
        """
        modules = data['modules']

        # GWP-Werte aus Modulen extrahieren
        gwp_a1a3 = modules.get('A1-A3', 0.0)
        gwp_c3 = modules.get('C3', 0.0)
        gwp_c4 = modules.get('C4', 0.0)
        gwp_d = modules.get('D', None)

        # Biogener Kohlenstoff
        biogenic_carbon = data.get('biogenic_carbon', None)

        # Typ von Englisch (CSV) nach Deutsch (UI) übersetzen
        csv_type = data['type']
        ui_type = self.TYPE_MAPPING_REVERSE.get(csv_type, csv_type)

        # Material erstellen
        return Material(
            id=uuid,
            name=data['name'],
            dataset_type=ui_type,  # Deutscher Name für UI
            source=data['source'],
            conformity=data.get('conformity', ''),
            unit=data['unit'],
            gwp_a1a3=gwp_a1a3,
            gwp_c3=gwp_c3,
            gwp_c4=gwp_c4,
            gwp_d=gwp_d,
            biogenic_carbon=biogenic_carbon,
            # Original speichern
            raw_data={'modules': modules, 'csv_type': csv_type,
                      'biogenic_carbon': biogenic_carbon, 'conformity': data.get('conformity', '')}
        )

    def _parse_row(
        self,
        row: Dict[str, str],
        idx: int,
        decimal: str
    ) -> Optional[Material]:
        """
        Parst eine CSV-Zeile zu einem Material-Objekt

        Erwartet Spalten (flexibel):
        - id / ID / uuid / UUID
        - name / Name / Bezeichnung
        - type / Typ / dataset_type / Datensatztyp
        - source / Quelle / Hersteller
        - unit / Einheit
        - gwp_a1a3 / GWP_A1-A3 / A1-A3
        - gwp_c3 / GWP_C3 / C3
        - gwp_c4 / GWP_C4 / C4
        - gwp_d / GWP_D / D
        """

        try:
            # Flexible Spalten-Zuordnung
            id_val = self._get_value(
                row, ['id', 'ID', 'uuid', 'UUID'], f"mat_{idx}")
            name = self._get_value(
                row, ['name', 'Name', 'Bezeichnung'], f"Material {idx}")
            dataset_type = self._get_value(
                row,
                ['type', 'Typ', 'dataset_type', 'Datensatztyp'],
                'generisch'
            )
            source = self._get_value(
                row, ['source', 'Quelle', 'Hersteller'], '')
            unit = self._get_value(row, ['unit', 'Einheit'], 'kg')

            # GWP-Werte (mit Dezimalkonvertierung)
            gwp_a1a3 = self._parse_float(
                self._get_value(
                    row, ['gwp_a1a3', 'GWP_A1-A3', 'A1-A3', 'gwp_a'], '0'),
                decimal
            )
            gwp_c3 = self._parse_float(
                self._get_value(row, ['gwp_c3', 'GWP_C3', 'C3'], '0'),
                decimal
            )
            gwp_c4 = self._parse_float(
                self._get_value(row, ['gwp_c4', 'GWP_C4', 'C4'], '0'),
                decimal
            )
            gwp_d_str = self._get_value(row, ['gwp_d', 'GWP_D', 'D'], None)
            gwp_d = self._parse_float(
                gwp_d_str, decimal) if gwp_d_str else None

            return Material(
                id=id_val,
                name=name,
                dataset_type=dataset_type,
                source=source,
                unit=unit,
                gwp_a1a3=gwp_a1a3,
                gwp_c3=gwp_c3,
                gwp_c4=gwp_c4,
                gwp_d=gwp_d,
                csv_row_index=idx,
                raw_data=dict(row)
            )

        except Exception as e:
            self.logger.warning(f"Fehler beim Parsen von Zeile {idx}: {e}")
            return None

    def _get_value(
        self,
        row: Dict[str, str],
        keys: List[str],
        default: str
    ) -> str:
        """Sucht Wert in verschiedenen Spaltennamen"""
        for key in keys:
            if key in row and row[key]:
                return row[key].strip()
        return default

    def _parse_float(self, value: str, decimal: str) -> float:
        """Parst Float mit Dezimalzeichen"""
        if not value:
            return 0.0

        # Ersetze Dezimalzeichen durch Punkt
        if decimal == ',':
            value = value.replace(',', '.')

        # Entferne Tausender-Trenner
        value = value.replace(' ', '').replace('\xa0', '')

        try:
            return float(value)
        except ValueError:
            return 0.0

    def search(
        self,
        query: str = "",
        dataset_type: Optional[str] = None,
        favorites_only: bool = False,
        en15804_a2_only: bool = False
    ) -> List[Material]:
        """
        Sucht Materialien

        Args:
            query: Suchbegriff (Volltext in Name, ID, Quelle)
            dataset_type: Filter nach Typ (None = alle)
            favorites_only: Nur Favoriten
            en15804_a2_only: Nur EN 15804+A2 Materialien

        Returns:
            Liste passender Materialien
        """

        results = self.materials

        # Filter: Favoriten
        if favorites_only:
            results = [
                m for m in results
                if m.id in self.favorites or m.name in self.favorite_names
            ]

        # Filter: Datensatztyp
        if dataset_type and dataset_type != "alle":
            results = [m for m in results if m.dataset_type == dataset_type]

        # Filter: EN 15804+A2
        if en15804_a2_only:
            results = [m for m in results if m.is_en15804_a2()]

        # Filter: Volltext
        if query:
            query_lower = query.lower()
            results = [
                m for m in results
                if query_lower in m.name.lower()
                or query_lower in m.id.lower()
                or query_lower in m.source.lower()
            ]

        return results

    def get_material_by_id(self, material_id: str) -> Optional[Material]:
        """
        Holt Material anhand der ID (UUID)

        Args:
            material_id: Material-ID (UUID)

        Returns:
            Material oder None wenn nicht gefunden
        """
        for material in self.materials:
            if material.id == material_id:
                return material
        return None

    def is_favorite(self, material_id: str) -> bool:
        """Prüft ob Material ein Favorit ist"""
        return material_id in self.favorites

    def add_favorite(self, material_id: str, material_name: str) -> None:
        """Fügt Material zu Favoriten hinzu"""
        self.favorites.add(material_id)
        self.favorite_names.add(material_name)

    def remove_favorite(self, material_id: str) -> None:
        """Entfernt Material aus Favoriten"""
        self.favorites.discard(material_id)

        # Auch den Namen entfernen, um Remapping zu verhindern
        for material in self.materials:
            if material.id == material_id:
                self.favorite_names.discard(material.name)
                break

    def add_to_favorites(self, material_id: str, material_name: str) -> None:
        """Fügt Material zu Favoriten hinzu (Alias für Kompatibilität)"""
        self.add_favorite(material_id, material_name)

    def get_recently_used(self, limit: int = 30) -> List[Material]:
        """Gibt die zuletzt/am häufigsten verwendeten Materialien zurück (max. 30)"""
        if not self.usage_counter:
            return []

        # Sortiere nach Verwendungshäufigkeit (absteigend)
        sorted_ids = [mat_id for mat_id,
                      _ in self.usage_counter.most_common(limit)]

        # Material-Objekte holen
        result = []
        for mat_id in sorted_ids:
            for material in self.materials:
                if material.id == mat_id:
                    result.append(material)
                    break

        return result

    def track_usage(self, material_id: str, material_name: str) -> None:
        """Zählt Verwendung eines Materials (ohne automatische Favoriten-Hinzufügung)"""
        self.usage_counter[material_id] += 1

        # Begrenze auf max 30 Einträge (entferne am wenigsten genutzte)
        if len(self.usage_counter) > 30:
            # Finde das am wenigsten genutzte Material
            least_used = self.usage_counter.most_common()[-1]
            del self.usage_counter[least_used[0]]

    def restore_favorites(self, favorite_ids: List[str], favorite_names: List[str]) -> None:
        """
        Stellt Favoriten aus gespeicherter Konfiguration wieder her

        Args:
            favorite_ids: Liste von Material-IDs
            favorite_names: Liste von Material-Namen
        """
        self.favorites = set(favorite_ids)
        self.favorite_names = set(favorite_names)
        self.logger.info(
            f"Favoriten wiederhergestellt: {len(self.favorites)} IDs, {len(self.favorite_names)} Namen")

    def restore_usage_counter(self, usage_data: Dict[str, int]) -> None:
        """
        Stellt Verwendungszähler aus gespeicherter Konfiguration wieder her

        Args:
            usage_data: Dictionary mit material_id: count
        """
        self.usage_counter = Counter(usage_data)
        self.logger.info(
            f"Verwendungszähler wiederhergestellt: {len(self.usage_counter)} Einträge")

    def _remap_favorites(self) -> None:
        """
        Mappt Favoriten nach CSV-Wechsel neu
        Versucht IDs und Namen zu matchen
        """

        new_favorites = set()

        for material in self.materials:
            if material.id in self.favorites or material.name in self.favorite_names:
                new_favorites.add(material.id)

        self.favorites = new_favorites

        self.logger.info(
            f"Favoriten neu gemappt: {len(self.favorites)} gefunden")

    def get_top_favorites(self, limit: int = 20) -> List[Material]:
        """Gibt die am häufigsten verwendeten Materialien zurück"""
        top_ids = [mat_id for mat_id,
                   _ in self.usage_counter.most_common(limit)]
        return [m for m in self.materials if m.id in top_ids]

    def get_metadata(self) -> Dict[str, Any]:
        """Gibt Metadaten der geladenen CSV zurück"""
        custom_count = sum(1 for m in self.materials if m.is_custom)
        return {
            'path': self.csv_path,
            'loaded_at': self.loaded_at,
            'separator': self.separator,
            'decimal': self.decimal,
            'count': len(self.materials),
            'favorites': len(self.favorites),
            'custom_materials': custom_count
        }

    # ========================================================================
    # CUSTOM MATERIALS
    # ========================================================================

    def get_custom_materials_path(self) -> Path:
        """Gibt Pfad zur custom_materials.csv zurück"""
        if self.csv_path:
            # Im gleichen Verzeichnis wie die Haupt-CSV
            return Path(self.csv_path).parent / 'custom_materials.csv'
        # Fallback: data-Ordner im Projektverzeichnis
        return Path(__file__).parent / 'custom_materials.csv'

    def load_custom_materials(self) -> int:
        """
        Lädt eigene Materialien aus custom_materials.csv

        Returns:
            Anzahl geladener Custom Materials
        """
        custom_path = self.get_custom_materials_path()

        if not custom_path.exists():
            self.logger.info(f"Keine Custom Materials gefunden: {custom_path}")
            return 0

        try:
            loaded_count = 0
            with open(custom_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')

                for row in reader:
                    # Leere Zeilen überspringen
                    if not row.get('UUID') or not row.get('Name'):
                        continue

                    try:
                        # Custom Materials verwenden Punkt als Dezimalzeichen
                        # Material erstellen
                        material = Material(
                            id=row['UUID'],
                            name=row['Name'],
                            source=row['Quelle'],
                            dataset_type=row['Datensatztyp'],
                            unit=row['Einheit'],
                            gwp_a1a3=self._parse_float(row['GWP_A1-A3'], '.'),
                            gwp_c3=self._parse_float(
                                row.get('GWP_C3', '0'), '.'),
                            gwp_c4=self._parse_float(
                                row.get('GWP_C4', '0'), '.'),
                            gwp_d=self._parse_float(
                                row.get('GWP_D', ''), '.') if row.get('GWP_D') else None,
                            biogenic_carbon=self._parse_float(
                                row.get('biogenic_carbon', ''), '.') if row.get('biogenic_carbon') else None,
                            conformity=row.get('conformity', 'Eigene EPD'),
                            is_custom=True
                        )

                        self.materials.append(material)
                        loaded_count += 1

                    except Exception as e:
                        self.logger.warning(
                            f"Fehler beim Laden von Custom Material: {e}")
                        continue

            self.logger.info(f"{loaded_count} Custom Materials geladen")
            return loaded_count

        except Exception as e:
            self.logger.error(
                f"Fehler beim Laden von Custom Materials: {e}", exc_info=True)
            return 0

    def save_custom_material(self, material: Material) -> bool:
        """
        Speichert ein neues Custom Material

        Args:
            material: Material-Objekt (mit is_custom=True)

        Returns:
            True bei Erfolg
        """
        if not material.is_custom:
            self.logger.error("Nur Custom Materials können gespeichert werden")
            return False

        custom_path = self.get_custom_materials_path()

        try:
            # Prüfen ob Datei existiert
            file_exists = custom_path.exists()

            # Ans Ende anhängen
            with open(custom_path, 'a', encoding='utf-8', newline='') as f:
                writer = csv.writer(f, delimiter=';')

                # Header schreiben wenn neue Datei
                if not file_exists or custom_path.stat().st_size == 0:
                    writer.writerow([
                        'UUID', 'Name', 'Quelle', 'Datensatztyp', 'Einheit',
                        'GWP_A1-A3', 'GWP_C3', 'GWP_C4', 'GWP_D', 'biogenic_carbon', 'conformity'
                    ])

                # Material schreiben
                writer.writerow([
                    material.id,
                    material.name,
                    material.source,
                    material.dataset_type,
                    material.unit,
                    f"{material.gwp_a1a3:.6f}",
                    f"{material.gwp_c3:.6f}",
                    f"{material.gwp_c4:.6f}",
                    f"{material.gwp_d:.6f}" if material.gwp_d is not None else "",
                    f"{material.biogenic_carbon:.6f}" if material.biogenic_carbon is not None else "",
                    material.conformity
                ])

            # Zu materials hinzufügen
            self.materials.append(material)
            self.logger.info(f"Custom Material gespeichert: {material.name}")
            return True

        except Exception as e:
            self.logger.error(
                f"Fehler beim Speichern von Custom Material: {e}", exc_info=True)
            return False

    def delete_custom_material(self, material_id: str) -> bool:
        """
        Löscht ein Custom Material

        Args:
            material_id: UUID des Materials

        Returns:
            True bei Erfolg
        """
        # Material finden
        material = next((m for m in self.materials if m.id ==
                        material_id and m.is_custom), None)
        if not material:
            self.logger.error(f"Custom Material nicht gefunden: {material_id}")
            return False

        custom_path = self.get_custom_materials_path()

        try:
            # Alle Materials außer dem zu löschenden einlesen
            remaining_materials = []

            with open(custom_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    if row['UUID'] != material_id:
                        remaining_materials.append(row)

            # Neu schreiben
            with open(custom_path, 'w', encoding='utf-8', newline='') as f:
                if remaining_materials:
                    fieldnames = ['UUID', 'Name', 'Quelle', 'Datensatztyp', 'Einheit',
                                  'GWP_A1-A3', 'GWP_C3', 'GWP_C4', 'GWP_D', 'biogenic_carbon', 'conformity']
                    writer = csv.DictWriter(
                        f, fieldnames=fieldnames, delimiter=';')
                    writer.writeheader()
                    writer.writerows(remaining_materials)

            # Aus materials entfernen
            self.materials = [m for m in self.materials if m.id != material_id]
            self.logger.info(f"Custom Material gelöscht: {material.name}")
            return True

        except Exception as e:
            self.logger.error(
                f"Fehler beim Löschen von Custom Material: {e}", exc_info=True)
            return False
