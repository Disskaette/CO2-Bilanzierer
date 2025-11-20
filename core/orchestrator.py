"""
App-Orchestrator - Zentrale Steuerungseinheit
Koordiniert alle Services und UI-Komponenten
"""

import logging
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
import threading

from models.project import Project
from models.variant import Variant, MaterialRow
from models.material import Material
from core.persistence import PersistenceService
from core.undo_redo_manager import UndoRedoManager
from data.material_repository import MaterialRepository
from services.calculation_service import CalculationService

logger = logging.getLogger(__name__)


class StateStore:
    """Einfacher State-Store für UI-Zustand"""

    def __init__(self):
        self.current_project: Optional[Project] = None
        self.open_tabs: List[int] = [0]  # Tab-Indices
        self.active_tab: int = 0
        self.ui_callbacks: Dict[str, List[Callable]] = {}
        # Zentrale Farbzuordnung für Materialien
        self.material_colors: Dict[str, tuple] = {}

    def register_callback(self, event: str, callback: Callable) -> None:
        """Registriert UI-Callback"""
        if event not in self.ui_callbacks:
            self.ui_callbacks[event] = []
        self.ui_callbacks[event].append(callback)

    def trigger(self, event: str, *args, **kwargs) -> None:
        """Löst Event aus"""
        if event in self.ui_callbacks:
            for callback in self.ui_callbacks[event]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Fehler in Callback für {event}: {e}")


class AppOrchestrator:
    """
    Zentrale Steuerungseinheit der Anwendung

    Verwaltet:
    - ProjectManager (Projekte und Dateibaum)
    - MaterialRepository (CSV/EPD)
    - CalculationService (CO₂-Berechnung)
    - PersistenceService (Speichern/Laden)
    - StateStore (UI-Zustand)

    Stellt Methoden bereit:
    - load_project, save_project, create_project
    - load_csv
    - open_variant_tab, close_tab
    - add_material_row, update_material_row, delete_material_row
    - rebuild_charts
    - notify_change (Autosave mit Debounce)
    - export_pdf
    """

    def __init__(self):
        # Services initialisieren
        self.persistence = PersistenceService()
        self.material_repo = MaterialRepository()
        self.calc_service = CalculationService()
        self.state = StateStore()
        self.undo_redo_manager = UndoRedoManager(max_history=10)

        # Autosave-Timer
        self._autosave_timer: Optional[threading.Timer] = None
        self._autosave_delay = 0.8  # Sekunden

        # Flag um Undo/Redo-Loop zu vermeiden
        self._applying_undo_redo = False

        self.logger = logger
        self.logger.info("AppOrchestrator initialisiert")

    # ========================================================================
    # PROJEKT-VERWALTUNG
    # ========================================================================

    def create_project(self, name: str = "Neues Projekt") -> Project:
        """
        Erstellt neues Projekt

        Args:
            name: Projektname

        Returns:
            Neues Project-Objekt
        """
        # Undo/Redo History löschen beim Erstellen eines neuen Projekts
        self.undo_redo_manager.clear()

        project = Project(name=name)
        self.state.current_project = project

        # Initialen State für Undo speichern
        self.undo_redo_manager.push_state(project)

        self.logger.info(f"Neues Projekt erstellt: {name}")
        return project

    def load_project(self, project_id: str) -> bool:
        """
        Lädt Projekt

        Args:
            project_id: Projekt-ID

        Returns:
            True bei Erfolg
        """
        project = self.persistence.load_project(project_id)

        if not project:
            self.logger.error(f"Projekt nicht gefunden: {project_id}")
            return False

        # Undo/Redo History löschen beim Laden eines neuen Projekts
        self.undo_redo_manager.clear()

        self.state.current_project = project

        # CSV neu laden wenn Projekt CSV-Pfad hat
        if project.last_csv_path:
            self.logger.info(
                f"Lade projektspezifische CSV: {project.last_csv_path}")
            self.material_repo.load_csv(project.last_csv_path)

            # Sanfte Aktualisierung: Materialnamen aus aktueller CSV holen
            # OHNE alte Materialien zu löschen die nicht mehr in CSV sind
            self._update_material_names_from_csv(project)

        # Initialen State für Undo speichern (damit erste Änderung rückgängig gemacht werden kann)
        self.undo_redo_manager.push_state(project)

        # Recent Projects Liste aktualisieren
        self._update_recent_projects(project_id)

        self.logger.info(f"Projekt geladen: {project.name}")
        self.state.trigger('project_loaded', project)

        return True

    def _update_material_names_from_csv(self, project: Project) -> None:
        """
        Aktualisiert Materialnamen aus aktueller CSV (für korrektes Encoding)
        Behält alte Daten bei wenn Material nicht mehr in CSV existiert

        Args:
            project: Projekt dessen Materialien aktualisiert werden sollen
        """
        updated_count = 0
        missing_count = 0

        for variant in project.variants:
            for row in variant.rows:
                if not row.material_id:
                    continue

                # Versuche Material in aktueller CSV zu finden
                material = self.material_repo.get_material_by_id(
                    row.material_id)

                if material:
                    # Material gefunden: Aktualisiere Namen (für korrektes Encoding)
                    if row.material_name != material.name:
                        old_name = row.material_name
                        row.material_name = material.name
                        updated_count += 1
                        self.logger.debug(
                            f"Material-Name aktualisiert: '{old_name}' -> '{material.name}'")
                else:
                    # Material nicht mehr in CSV: Behalte alten Stand
                    missing_count += 1
                    self.logger.debug(
                        f"Material nicht in CSV gefunden (behalte alten Stand): {row.material_name}")

        if updated_count > 0:
            self.logger.info(
                f"✓ {updated_count} Material-Namen aktualisiert (Encoding korrigiert)")
        if missing_count > 0:
            self.logger.info(
                f"ℹ {missing_count} Materialien nicht mehr in CSV (alte Daten beibehalten)")

    def save_project(self) -> bool:
        """
        Speichert aktuelles Projekt

        Returns:
            True bei Erfolg
        """
        if not self.state.current_project:
            self.logger.warning("Kein Projekt zum Speichern vorhanden")
            return False

        success = self.persistence.save_project(self.state.current_project)

        if success:
            # Auch Snapshot speichern
            self.persistence.save_snapshot(self.state.current_project)

        return success

    def save_project_as(self, filepath: str) -> bool:
        """
        Speichert Projekt unter benutzerdefiniertem Pfad als NEUES Projekt
        Generiert eine neue UUID um ein unabhängiges Projekt zu erstellen

        Args:
            filepath: Vollständiger Dateipfad

        Returns:
            True bei Erfolg
        """
        if not self.state.current_project:
            self.logger.warning("Kein Projekt zum Speichern vorhanden")
            return False

        import uuid

        # Alte UUID merken für Logging
        old_id = self.state.current_project.id

        # Neue UUID generieren -> Neues, unabhängiges Projekt!
        new_id = str(uuid.uuid4())
        self.state.current_project.id = new_id

        self.logger.info(
            f"Speichern unter: Neues Projekt erstellt (alte UUID: {old_id[:8]}, neue UUID: {new_id[:8]})")

        success = self.persistence.save_project(
            self.state.current_project, custom_path=filepath)

        if success:
            # Auch Snapshot speichern
            self.persistence.save_snapshot(self.state.current_project)

            # Recent Projects Liste aktualisieren (wichtig für externe Pfade!)
            self._update_recent_projects(self.state.current_project.id)

        return success

    def list_projects(self) -> List[Dict[str, Any]]:
        """
        Listet alle Projekte auf

        Returns:
            Liste mit Projekt-Metadaten
        """
        return self.persistence.list_projects()

    def delete_project(self, project_id: str) -> bool:
        """
        Löscht Projekt

        Args:
            project_id: ID des zu löschenden Projekts

        Returns:
            True bei Erfolg
        """
        return self.persistence.delete_project(project_id)

    # ========================================================================
    # CSV / MATERIAL-REPOSITORY
    # ========================================================================

    def _load_csv_with_fallback(self, project_csv_path: Optional[str] = None) -> bool:
        """
        Lädt CSV mit 3-stufiger Fallback-Strategie:
        1. Projektspezifischer Pfad (falls vorhanden und existiert)
        2. Global gespeicherter Pfad (aus Konfiguration)
        3. Fallback: data/OBD_Datenbank.csv im Projektordner

        Args:
            project_csv_path: Projektspezifischer CSV-Pfad (optional)

        Returns:
            True bei Erfolg
        """
        from pathlib import Path

        # 1. Versuch: Projektspezifischer Pfad
        if project_csv_path and Path(project_csv_path).exists():
            self.logger.info(
                f"Lade projektspezifische CSV: {project_csv_path}")
            return self.load_csv(project_csv_path)

        # 2. Versuch: Global gespeicherter Pfad
        config = self.load_config()
        global_csv_path = config.get('global_csv_path')

        if global_csv_path and Path(global_csv_path).exists():
            self.logger.info(
                f"Lade global gespeicherte CSV: {global_csv_path}")
            return self.load_csv(global_csv_path)

        # 3. Fallback: Standard-CSV im data-Ordner
        import __main__
        app_dir = Path(__main__.__file__).parent if hasattr(
            __main__, '__file__') else Path.cwd()
        default_csv = app_dir / "data" / "OBD_Datenbank.csv"

        if default_csv.exists():
            self.logger.info(f"Lade Standard-CSV: {default_csv}")
            return self.load_csv(str(default_csv))

        # Keine CSV gefunden
        self.logger.warning("Keine CSV-Datenbank gefunden.")
        self.logger.warning(
            "Bitte laden Sie eine CSV über 'CSV laden' im Menü.")
        return False

    def load_csv(self, path: str) -> bool:
        """
        Lädt CSV-Datenbank und stellt Favoriten wieder her

        Args:
            path: Pfad zur CSV

        Returns:
            True bei Erfolg
        """
        # Favoriten und Usage Counter vor dem Laden sichern
        config = self.load_config()
        favorite_ids = config.get('favorites', [])
        favorite_names = config.get('favorite_names', [])
        usage_data = config.get('usage_counter', {})

        success = self.material_repo.load_csv(path)

        if success:
            # Favoriten wiederherstellen
            if favorite_ids or favorite_names:
                self.material_repo.restore_favorites(
                    favorite_ids, favorite_names)

            # Usage Counter wiederherstellen
            if usage_data:
                self.material_repo.restore_usage_counter(usage_data)

            if self.state.current_project:
                # Metadaten im Projekt speichern
                metadata = self.material_repo.get_metadata()
                self.state.current_project.last_csv_path = path
                self.state.current_project.csv_loaded_at = metadata['loaded_at']
                self.state.current_project.csv_separator = metadata['separator']
                self.state.current_project.csv_decimal = metadata['decimal']

                self.notify_change()
                self.state.trigger('csv_loaded', metadata)

        return success

    def search_materials(
        self,
        query: str = "",
        dataset_type: Optional[str] = None,
        favorites_only: bool = False,
        en15804_a2_only: bool = False
    ) -> List[Material]:
        """
        Sucht Materialien in der CSV

        Args:
            query: Suchbegriff
            dataset_type: Filter nach Typ
            favorites_only: Nur Favoriten
            en15804_a2_only: Nur EN 15804+A2 Materialien

        Returns:
            Liste passender Materialien
        """
        return self.material_repo.search(query, dataset_type, favorites_only, en15804_a2_only)

    def get_csv_metadata(self) -> Dict[str, Any]:
        """Gibt CSV-Metadaten zurück"""
        return self.material_repo.get_metadata()

    def get_recently_used_materials(self) -> List[Material]:
        """Gibt zuletzt/am häufigsten verwendete Materialien zurück"""
        return self.material_repo.get_recently_used()

    # ========================================================================
    # VARIANTEN-VERWALTUNG
    # ========================================================================

    def get_current_project(self) -> Optional[Project]:
        """Gibt aktuelles Projekt zurück"""
        return self.state.current_project

    def get_variant(self, index: int) -> Optional[Variant]:
        """
        Gibt Variante nach Index zurück

        Args:
            index: Varianten-Index (0-4)

        Returns:
            Variant oder None
        """
        if not self.state.current_project:
            return None
        return self.state.current_project.get_variant(index)

    def create_variant(self, name: str = "Variante") -> Optional[Variant]:
        """
        Erstellt neue Variante

        Args:
            name: Variantenname

        Returns:
            Neue Variant oder None (wenn max. 5 erreicht)
        """
        if not self.state.current_project:
            return None

        # State für Undo speichern
        self._save_state_for_undo()

        variant = Variant(name=name)

        if self.state.current_project.add_variant(variant):
            # Aktuellen State nach Änderung speichern (wichtig für Redo!)
            self.undo_redo_manager.update_current_state(
                self.state.current_project)
            self.notify_change()
            self.state.trigger('variant_added', len(
                self.state.current_project.variants))
            return variant

        return None

    def delete_variant(self, variant_index: int) -> bool:
        """
        Löscht Variante

        Args:
            variant_index: Index der zu löschenden Variante

        Returns:
            True bei Erfolg
        """
        if not self.state.current_project:
            return False

        if variant_index < 0 or variant_index >= len(self.state.current_project.variants):
            return False

        # State für Undo speichern
        self._save_state_for_undo()

        # Variante löschen
        self.state.current_project.variants.pop(variant_index)

        # Aktuellen State nach Änderung speichern (wichtig für Redo!)
        self.undo_redo_manager.update_current_state(self.state.current_project)
        self.notify_change()
        self.state.trigger('variant_deleted', len(
            self.state.current_project.variants))
        return True

    def rename_project(self, new_name: str) -> bool:
        """
        Benennt Projekt um

        Args:
            new_name: Neuer Projektname

        Returns:
            True bei Erfolg
        """
        if not self.state.current_project:
            return False

        if not new_name or not new_name.strip():
            return False

        new_name = new_name.strip()

        # Keine Änderung
        if new_name == self.state.current_project.name:
            return False

        # State für Undo speichern
        self._save_state_for_undo()

        old_name = self.state.current_project.name
        self.state.current_project.name = new_name

        # JSON-Datei umbenennen
        self.persistence.rename_project_file(
            self.state.current_project, old_name)

        self.notify_change()
        self.state.trigger('project_renamed', new_name)

        self.logger.info(f"Projekt umbenannt: '{old_name}' → '{new_name}'")
        return True

    def rename_variant(self, variant_index: int, new_name: str) -> bool:
        """
        Benennt Variante um

        Args:
            variant_index: Index der Variante
            new_name: Neuer Variantenname

        Returns:
            True bei Erfolg
        """
        variant = self.get_variant(variant_index)
        if not variant:
            return False

        if not new_name or not new_name.strip():
            return False

        new_name = new_name.strip()

        # Keine Änderung
        if new_name == variant.name:
            return False

        # State für Undo speichern
        self._save_state_for_undo()

        old_name = variant.name
        variant.name = new_name

        self.notify_change()
        self.state.trigger('variant_renamed', variant_index, new_name)

        self.logger.info(f"Variante umbenannt: '{old_name}' → '{new_name}'")
        return True

    # ========================================================================
    # MATERIALZEILEN-VERWALTUNG
    # ========================================================================

    def add_material_row(self, variant_index: int) -> Optional[MaterialRow]:
        """
        Fügt leere Materialzeile zu Variante hinzu

        Args:
            variant_index: Index der Variante

        Returns:
            Neue MaterialRow oder None
        """
        variant = self.get_variant(variant_index)
        if not variant:
            return None

        # State für Undo speichern
        self._save_state_for_undo()

        row = MaterialRow()
        variant.add_row(row)

        self.notify_change()
        self.state.trigger('row_added', variant_index, row.id)
        return row

    def update_material_row(
        self,
        variant_index: int,
        row_id: str,
        material: Optional[Material] = None,
        quantity: Optional[float] = None
    ) -> bool:
        """
        Aktualisiert Materialzeile

        Args:
            variant_index: Index der Variante
            row_id: ID der Zeile
            material: Optional neues Material
            quantity: Optional neue Menge

        Returns:
            True bei Erfolg
        """
        variant = self.get_variant(variant_index)
        if not variant:
            return False

        # Zeile finden
        row = next((r for r in variant.rows if r.id == row_id), None)
        if not row:
            return False

        # State für Undo speichern
        self._save_state_for_undo()

        # Material aktualisieren
        if material:
            self.calc_service.update_material_row(row, material, quantity)
            self.material_repo.track_usage(material.id, material.name)
        elif quantity is not None:
            row.quantity = quantity
            self.calc_service.recalculate_row(row)

        # Summen neu berechnen
        variant.calculate_sums()

        self.notify_change()
        self.state.trigger('row_updated', variant_index, row_id)

        return True

    def delete_material_row(self, variant_index: int, row_id: str) -> bool:
        """
        Löscht Materialzeile

        Args:
            variant_index: Index der Variante
            row_id: ID der Zeile

        Returns:
            True bei Erfolg
        """
        variant = self.get_variant(variant_index)
        if not variant:
            return False

        # State für Undo speichern
        self._save_state_for_undo()

        variant.remove_row(row_id)
        variant.calculate_sums()

        self.notify_change()
        self.state.trigger('row_deleted', variant_index, row_id)

        return True

    def move_row_up(self, variant_index: int, row_id: str) -> bool:
        """Verschiebt Zeile nach oben"""
        variant = self.get_variant(variant_index)
        if not variant:
            return False

        # State für Undo speichern
        self._save_state_for_undo()

        variant.move_row_up(row_id)
        self.notify_change()
        self.state.trigger('row_moved', variant_index)

        return True

    def move_row_down(self, variant_index: int, row_id: str) -> bool:
        """Verschiebt Zeile nach unten"""
        variant = self.get_variant(variant_index)
        if not variant:
            return False

        # State für Undo speichern
        self._save_state_for_undo()

        variant.move_row_down(row_id)
        self.notify_change()
        self.state.trigger('row_moved', variant_index)

        return True

    # ========================================================================
    # SYSTEMGRENZE & DIAGRAMME
    # ========================================================================

    def set_system_boundary(self, boundary: str) -> None:
        """
        Setzt Systemgrenze für alle Varianten

        Args:
            boundary: Systemgrenze ("A", "A+C", "A+C+D", mit optionalem " (bio)")
        """
        if self.state.current_project:
            # State für Undo speichern
            self._save_state_for_undo()

            self.state.current_project.system_boundary = boundary
            self.notify_change()
            self.state.trigger('boundary_changed', boundary)

    def set_variant_visibility(self, index: int, visible: bool) -> None:
        """Setzt Sichtbarkeit einer Variante im Dashboard"""
        if self.state.current_project:
            # State für Undo speichern
            self._save_state_for_undo()

            # Ensure visible_variants list exists and has correct length
            if not hasattr(self.state.current_project, 'visible_variants'):
                self.state.current_project.visible_variants = []

            while len(self.state.current_project.visible_variants) <= index:
                self.state.current_project.visible_variants.append(True)

            self.state.current_project.visible_variants[index] = visible
            self.notify_change()
            self.state.trigger('visibility_changed')

    def rebuild_charts(self) -> None:
        """Triggert Neuzeichnen aller Diagramme"""
        self.state.trigger('rebuild_charts')

    # ========================================================================
    # AUTOSAVE & ÄNDERUNGSBENACHRICHTIGUNG
    # ========================================================================

    def notify_change(self) -> None:
        """
        Benachrichtigt über Änderung
        Triggert Autosave mit Debounce (800ms)
        """
        # Vorherigen Timer abbrechen
        if self._autosave_timer:
            self._autosave_timer.cancel()

        # Neuen Timer starten
        self._autosave_timer = threading.Timer(
            self._autosave_delay,
            self._do_autosave
        )
        self._autosave_timer.daemon = True
        self._autosave_timer.start()

    def _do_autosave(self) -> None:
        """Führt Autosave durch"""
        try:
            success = self.save_project()
            if success:
                self.state.trigger('autosave_success')
            else:
                self.state.trigger('autosave_failed')
        except Exception as e:
            self.logger.error(f"Fehler beim Autosave: {e}", exc_info=True)
            self.state.trigger('autosave_failed')

    # ========================================================================
    # EXPORT
    # ========================================================================

    def update_material_colors(self, visible_variant_indices: Optional[List[int]] = None) -> None:
        """
        Aktualisiert die zentrale Materialfarb-Zuordnung basierend auf ALLEN Materialien im Projekt.
        Dies sorgt für konsistente Farben, unabhängig von der Sichtbarkeit der Varianten.

        Args:
            visible_variant_indices: Liste der sichtbaren Varianten-Indices (wird für Kompatibilität
                                    akzeptiert, aber ignoriert - Farben basieren immer auf allen Materialien)
        """
        import matplotlib.pyplot as plt

        project = self.state.current_project
        if not project or not project.variants:
            return

        # Sammle ALLE Materialien aus ALLEN Varianten im Projekt
        # (nicht nur aus sichtbaren, damit Farben konsistent bleiben)
        all_materials = set()
        for variant in project.variants:
            for row in variant.rows:
                if row.material_name:
                    all_materials.add(row.material_name)

        # Farben zuweisen (konsistent über alle Diagramme und Sichtbarkeiten)
        colors = plt.cm.tab20.colors
        self.state.material_colors.clear()
        sorted_materials = sorted(all_materials)
        for idx, material in enumerate(sorted_materials):
            self.state.material_colors[material] = colors[idx % len(colors)]

    def get_material_color(self, material_name: str) -> tuple:
        """
        Gibt die Farbe für ein Material zurück

        Args:
            material_name: Name des Materials

        Returns:
            RGB-Tupel (0-1) oder Standardfarbe
        """
        import matplotlib.pyplot as plt
        return self.state.material_colors.get(material_name, plt.cm.tab20.colors[0])

    def export_pdf(
        self,
        output_path: str,
        include_dashboard: bool = True,
        variant_indices: Optional[List[int]] = None
    ) -> bool:
        """
        Exportiert PDF-Report

        Args:
            output_path: Ausgabepfad
            include_dashboard: Dashboard einbeziehen
            variant_indices: Zu exportierende Varianten (None = alle)

        Returns:
            True bei Erfolg
        """
        # TODO: PDF-Export implementieren
        # Benötigt: matplotlib-Charts als PNG, HTML-Template, PDF-Lib

        self.logger.warning("PDF-Export noch nicht implementiert")
        self.logger.info(
            f"TODO: PDF-Export nach {output_path}, "
            f"Dashboard={include_dashboard}, Varianten={variant_indices}"
        )

        return False

    # ========================================================================
    # KONFIGURATION
    # ========================================================================

    def save_config(self) -> None:
        """Speichert aktuelle Konfiguration inkl. Favoriten und Usage Counter"""
        # Speichere nur die Top 30 häufigsten Materialien
        usage_dict = dict(self.material_repo.usage_counter.most_common(30))

        # Lade bestehende config um recent_projects, external_paths und last_open_directory zu erhalten
        existing_config = self.load_config()

        config = {
            'last_project_id': (
                self.state.current_project.id
                if self.state.current_project
                else None
            ),
            'recent_projects': existing_config.get('recent_projects', []),
            'external_project_paths': existing_config.get('external_project_paths', {}),
            # Bewahre letztes Verzeichnis
            'last_open_directory': existing_config.get('last_open_directory'),
            'global_csv_path': (
                self.material_repo.csv_path
                if self.material_repo.csv_path
                else None
            ),
            'favorites': list(self.material_repo.favorites),
            'favorite_names': list(self.material_repo.favorite_names),
            'usage_counter': usage_dict,
            'theme': 'dark',
            'window_size': [1400, 900]
        }

        self.persistence.save_config(config)

    def load_config(self) -> Dict[str, Any]:
        """Lädt Konfiguration"""
        return self.persistence.load_config()

    def _update_recent_projects(self, project_id: str) -> None:
        """Aktualisiert Liste der zuletzt verwendeten Projekte"""
        try:
            config = self.load_config()
            recent = config.get('recent_projects', [])

            # Entferne Projekt falls bereits in Liste
            if project_id in recent:
                recent.remove(project_id)

            # Füge an erster Stelle ein
            recent.insert(0, project_id)

            # Behalte nur die letzten 10
            recent = recent[:10]

            # Speichere zurück
            config['recent_projects'] = recent
            self.persistence.save_config(config)

            self.logger.info(
                f"Recent Projects aktualisiert: {project_id} ist jetzt #1 von {len(recent)}")

        except Exception as e:
            self.logger.warning(
                f"Fehler beim Aktualisieren der Recent Projects: {e}")

    def get_log_path(self) -> str:
        """Gibt Log-Pfad zurück"""
        return str(self.persistence.get_log_path())

    # ========================================================================
    # UNDO / REDO
    # ========================================================================

    def _save_state_for_undo(self) -> None:
        """
        Speichert aktuellen Project-State für Undo.
        Muss VOR jeder State-Änderung aufgerufen werden.
        """
        # Nicht speichern wenn wir gerade Undo/Redo anwenden
        if self._applying_undo_redo:
            return

        # Nur speichern wenn Projekt vorhanden
        if not self.state.current_project:
            return

        # State in Undo-Manager pushen
        self.undo_redo_manager.push_state(self.state.current_project)

    def perform_undo(self) -> bool:
        """
        Macht letzte Änderung rückgängig.

        Returns:
            True wenn Undo durchgeführt wurde, False wenn nicht möglich
        """
        if not self.undo_redo_manager.can_undo():
            return False

        # Flag setzen um Loop zu vermeiden
        self._applying_undo_redo = True

        try:
            # Vorherigen State vom Manager holen
            previous_state = self.undo_redo_manager.undo()

            if previous_state:
                # State wiederherstellen
                self.state.current_project = previous_state

                # UI aktualisieren
                self.state.trigger('project_loaded', previous_state)
                self.state.trigger('undo_performed')

                # Autosave triggern (State ist jetzt anders)
                self.notify_change()

                self.logger.info("Undo durchgeführt")
                return True

            return False

        finally:
            # Flag zurücksetzen
            self._applying_undo_redo = False

    def perform_redo(self) -> bool:
        """
        Stellt rückgängig gemachte Änderung wieder her.

        Returns:
            True wenn Redo durchgeführt wurde, False wenn nicht möglich
        """
        if not self.undo_redo_manager.can_redo():
            return False

        # Flag setzen um Loop zu vermeiden
        self._applying_undo_redo = True

        try:
            # Nächsten State vom Manager holen
            next_state = self.undo_redo_manager.redo()

            if next_state:
                # State wiederherstellen
                self.state.current_project = next_state

                # UI aktualisieren
                self.state.trigger('project_loaded', next_state)
                self.state.trigger('redo_performed')

                # Autosave triggern (State ist jetzt anders)
                self.notify_change()

                self.logger.info("Redo durchgeführt")
                return True

            return False

        finally:
            # Flag zurücksetzen
            self._applying_undo_redo = False

    def can_undo(self) -> bool:
        """Prüft ob Undo möglich ist"""
        return self.undo_redo_manager.can_undo()

    def can_redo(self) -> bool:
        """Prüft ob Redo möglich ist"""
        return self.undo_redo_manager.can_redo()

    def get_undo_redo_info(self) -> dict:
        """Gibt Undo/Redo Debug-Informationen zurück"""
        return self.undo_redo_manager.get_history_info()
