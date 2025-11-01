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

            with open(path, 'r', encoding=encoding, errors='replace') as f:
                reader = csv.DictReader(f, delimiter=separator)

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
                            
                            materials_dict[uuid] = {
                                'uuid': uuid,
                                'name': name,
                                'type': row.get('Typ', 'generisch'),
                                'source': row.get('Declaration owner', ''),
                                'unit': row.get('Bezugseinheit', 'kg'),
                                'modules': {}  # Modul -> GWP-Wert
                            }

                        # Modul und GWP-Wert extrahieren
                        # WICHTIG: ÖKOBAUDAT verwendet "GWPtotal (A2)", nicht "GWP"!
                        modul = row.get('Modul', '').strip()
                        gwp_str = row.get('GWPtotal (A2)', row.get('GWP', '0'))

                        if modul and gwp_str:
                            gwp_value = self._parse_float(gwp_str, decimal)
                            materials_dict[uuid]['modules'][modul] = gwp_value

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

        Args:
            uuid: Material-UUID
            data: Dict mit name, type, source, unit, modules

        Returns:
            Material-Objekt oder None
        """
        modules = data['modules']

        # GWP-Werte aus Modulen extrahieren
        gwp_a1a3 = modules.get('A1-A3', 0.0)
        gwp_c3 = modules.get('C3', 0.0)
        gwp_c4 = modules.get('C4', 0.0)
        gwp_d = modules.get('D', None)

        # Typ von Englisch (CSV) nach Deutsch (UI) übersetzen
        csv_type = data['type']
        ui_type = self.TYPE_MAPPING_REVERSE.get(csv_type, csv_type)

        # Material erstellen
        return Material(
            id=uuid,
            name=data['name'],
            dataset_type=ui_type,  # Deutscher Name für UI
            source=data['source'],
            unit=data['unit'],
            gwp_a1a3=gwp_a1a3,
            gwp_c3=gwp_c3,
            gwp_c4=gwp_c4,
            gwp_d=gwp_d,
            # Original speichern
            raw_data={'modules': modules, 'csv_type': csv_type}
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
        favorites_only: bool = False
    ) -> List[Material]:
        """
        Sucht Materialien

        Args:
            query: Suchbegriff (Volltext in Name, ID, Quelle)
            dataset_type: Filter nach Typ (None = alle)
            favorites_only: Nur Favoriten

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

    def add_to_favorites(self, material_id: str, material_name: str) -> None:
        """Fügt Material zu Favoriten hinzu"""
        self.favorites.add(material_id)
        self.favorite_names.add(material_name)

    def track_usage(self, material_id: str, material_name: str) -> None:
        """Zählt Verwendung eines Materials"""
        self.usage_counter[material_id] += 1
        self.add_to_favorites(material_id, material_name)

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
        return {
            'path': self.csv_path,
            'loaded_at': self.loaded_at,
            'separator': self.separator,
            'decimal': self.decimal,
            'count': len(self.materials),
            'favorites': len(self.favorites)
        }
