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
        
        # Autosave-Timer
        self._autosave_timer: Optional[threading.Timer] = None
        self._autosave_delay = 0.8  # Sekunden
        
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
        project = Project(name=name)
        self.state.current_project = project
        
        self.logger.info(f"Neues Projekt erstellt: {name}")
        return project
    
    def load_project(self, project_id: str) -> bool:
        """
        Lädt Projekt
        
        Args:
            project_id: ID des zu ladenden Projekts
        
        Returns:
            True bei Erfolg
        """
        project = self.persistence.load_project(project_id)
        
        if not project:
            self.logger.error(f"Projekt nicht gefunden: {project_id}")
            return False
        
        self.state.current_project = project
        
        # CSV neu laden, falls Pfad vorhanden
        if project.last_csv_path:
            self.load_csv(project.last_csv_path)
        
        self.logger.info(f"Projekt geladen: {project.name}")
        self.state.trigger('project_loaded', project)
        
        return True
    
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
        Speichert Projekt unter benutzerdefiniertem Pfad
        
        Args:
            filepath: Vollständiger Dateipfad
        
        Returns:
            True bei Erfolg
        """
        if not self.state.current_project:
            self.logger.warning("Kein Projekt zum Speichern vorhanden")
            return False
        
        success = self.persistence.save_project(self.state.current_project, custom_path=filepath)
        
        if success:
            # Auch Snapshot speichern
            self.persistence.save_snapshot(self.state.current_project)
        
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
    
    def load_csv(self, path: str) -> bool:
        """
        Lädt CSV-Datenbank
        
        Args:
            path: Pfad zur CSV
        
        Returns:
            True bei Erfolg
        """
        success = self.material_repo.load_csv(path)
        
        if success and self.state.current_project:
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
        favorites_only: bool = False
    ) -> List[Material]:
        """
        Sucht Materialien in der CSV
        
        Args:
            query: Suchbegriff
            dataset_type: Filter nach Typ
            favorites_only: Nur Favoriten
        
        Returns:
            Liste passender Materialien
        """
        return self.material_repo.search(query, dataset_type, favorites_only)
    
    def get_csv_metadata(self) -> Dict[str, Any]:
        """Gibt CSV-Metadaten zurück"""
        return self.material_repo.get_metadata()
    
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
        
        variant = Variant(name=name)
        
        if self.state.current_project.add_variant(variant):
            self.notify_change()
            return variant
        
        return None
    
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
        
        row = MaterialRow()
        variant.add_row(row)
        
        self.notify_change()
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
        
        variant.move_row_up(row_id)
        self.notify_change()
        self.state.trigger('row_moved', variant_index)
        
        return True
    
    def move_row_down(self, variant_index: int, row_id: str) -> bool:
        """Verschiebt Zeile nach unten"""
        variant = self.get_variant(variant_index)
        if not variant:
            return False
        
        variant.move_row_down(row_id)
        self.notify_change()
        self.state.trigger('row_moved', variant_index)
        
        return True
    
    # ========================================================================
    # SYSTEMGRENZE & DIAGRAMME
    # ========================================================================
    
    def set_system_boundary(self, boundary: str) -> None:
        """
        Setzt Systemgrenze
        
        Args:
            boundary: "A1-A3", "A1-A3+C3+C4", "A1-A3+C3+C4+D"
        """
        if self.state.current_project:
            self.state.current_project.system_boundary = boundary
            self.notify_change()
            self.state.trigger('boundary_changed', boundary)
    
    def set_variant_visibility(self, index: int, visible: bool) -> None:
        """
        Setzt Sichtbarkeit einer Variante im Vergleichsdiagramm
        
        Args:
            index: Varianten-Index
            visible: Sichtbar ja/nein
        """
        if self.state.current_project:
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
                self.logger.debug("Autosave erfolgreich")
                self.state.trigger('autosave_success')
            else:
                self.logger.warning("Autosave fehlgeschlagen")
                self.state.trigger('autosave_failed')
        except Exception as e:
            self.logger.error(f"Fehler beim Autosave: {e}", exc_info=True)
            self.state.trigger('autosave_failed')
    
    # ========================================================================
    # EXPORT
    # ========================================================================
    
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
        """Speichert aktuelle Konfiguration"""
        config = {
            'last_project_id': (
                self.state.current_project.id
                if self.state.current_project
                else None
            ),
            'last_csv_path': (
                self.state.current_project.last_csv_path
                if self.state.current_project
                else None
            ),
            'theme': 'dark',  # TODO: aus UI übernehmen
            'window_size': [1400, 900]  # TODO: aus UI übernehmen
        }
        
        self.persistence.save_config(config)
    
    def load_config(self) -> Dict[str, Any]:
        """Lädt Konfiguration"""
        return self.persistence.load_config()
    
    def get_log_path(self) -> str:
        """Gibt Log-Pfad zurück"""
        return str(self.persistence.get_log_path())
