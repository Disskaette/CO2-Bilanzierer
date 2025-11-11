"""
CO₂-Bilanzierer
Haupteinstiegspunkt der Anwendung

Ökobilanzierung nach ABC-Entwurfstafeln (Stand 2024-02)
Normative Grundlage:
- DIN EN 15804:2012 + A2:2019 + AC:2021
- DIN EN 15978-1 (Entwurf 2024-05)
- ABC-Entwurfstafeln "Ökobilanzierung in der Tragwerksplanung"
"""

import sys
import logging
from pathlib import Path

# CustomTkinter muss vor anderen Imports kommen
import customtkinter as ctk

from core.orchestrator import AppOrchestrator
from ui.welcome_window import WelcomeWindow
from ui.main_window import MainWindow
from ui.splash_screen import SplashScreen
from utils.logging_config import setup_logging
from utils.demo_project import create_demo_project


class Application:
    """
    Hauptanwendung
    Verwaltet Welcome-Window → Main-Window Übergang
    """

    VERSION = "2.0"

    def __init__(self):
        # Temporäres Root-Window SOFORT erstellen
        self.temp_root = ctk.CTk()
        self.temp_root.withdraw()  # Komplett verstecken
        
        # Splash Screen SOFORT anzeigen (vor allem anderen!)
        self.splash = SplashScreen(self.temp_root, version=self.VERSION)
        
        # Attribute initialisieren
        self.orchestrator = None
        self.logger = None
        self.main_window = None
        
        # Schwere Initialisierung asynchron (damit Splash Screen sofort sichtbar ist)
        self.temp_root.after(50, self._initialize)

    def _initialize(self):
        """Initialisiert Orchestrator und lädt Daten mit Splash-Screen Status-Updates"""
        
        # Orchestrator und Logging initialisieren
        self.splash.update_status("Initialisiere...")
        self.orchestrator = AppOrchestrator()
        log_path = Path(self.orchestrator.get_log_path())
        setup_logging(log_path)
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"CO₂-Bilanzierer v{self.VERSION} gestartet")
        
        # Tcl/Tk Error-Handler für harmlose Fehler beim Beenden
        def report_callback_exception(exc_type, exc_value, exc_tb):
            # Ignoriere "invalid command name" Fehler beim Beenden
            if "invalid command name" in str(exc_value):
                return
            # Andere Fehler normal loggen
            if self.logger:
                self.logger.error(f"Tcl/Tk Fehler: {exc_value}", exc_info=(exc_type, exc_value, exc_tb))
        
        self.temp_root.report_callback_exception = report_callback_exception
        
        # Standard-CSV laden
        self.splash.update_status("Lade CSV-Datenbank...")
        self._load_default_csv()

        # Demo-Projekt laden oder erstellen
        self.splash.update_status("Lade Projekt...")
        self._load_or_create_demo_project()

        # Splash Screen schließen und Welcome-Window anzeigen
        self.temp_root.after(500, self._finish_startup)

    def _load_or_create_demo_project(self) -> None:
        """Lädt letztes Projekt oder erstellt Demo-Projekt"""
        projects = self.orchestrator.list_projects()

        if projects:
            # Letztes Projekt laden
            last_project_id = projects[0]['id']
            self.orchestrator.load_project(last_project_id)
            self.logger.info(f"Letztes Projekt geladen: {last_project_id}")
        else:
            self.logger.info("Kein Projekt vorhanden - erstelle Demo-Projekt")

            demo_project = create_demo_project()
            self.orchestrator.state.current_project = demo_project
            self.orchestrator.save_project()

            self.logger.info(f"Demo-Projekt erstellt: {demo_project.name}")

    def _finish_startup(self):
        """Beendet Startup-Prozess"""
        self.splash.close()
        self._show_welcome()

    def _load_default_csv(self) -> None:
        """Lädt Standard-CSV aus dem Data-Ordner, falls vorhanden"""
        # Pfad zur CSV im Projektverzeichnis
        project_dir = Path(__file__).parent
        csv_path = project_dir / "data" / "OBD_Datenbank.csv"

        if csv_path.exists():
            self.logger.info(f"Lade Standard-CSV: {csv_path}")
            success = self.orchestrator.load_csv(str(csv_path))
            if success:
                self.logger.info("Standard-CSV erfolgreich geladen")
            else:
                self.logger.warning("Fehler beim Laden der Standard-CSV")
        else:
            self.logger.info(f"Keine Standard-CSV gefunden unter: {csv_path}")
            self.logger.info(
                "Sie können später über 'CSV laden' eine Datenbank laden")

    def _show_welcome(self) -> None:
        """Zeigt Welcome-Window"""
        projects = self.orchestrator.list_projects()

        WelcomeWindow(
            self.temp_root,
            recent_projects=projects,
            on_new_project=self._on_new_project,
            on_open_project=self._on_open_project,
            on_open_file_dialog=self._on_open_file_dialog
        )

    def _show_main_window(self) -> None:
        """Zeigt Main-Window"""
        # Temp-Root schließen und mainloop beenden
        self.temp_root.quit()
        self.temp_root.destroy()

        # Main-Window als neues Root erstellen
        if not self.main_window:
            self.main_window = MainWindow(self.orchestrator)

            # Tcl/Tk Error-Handler auch für main_window setzen
            def report_callback_exception(exc_type, exc_value, exc_tb):
                # Ignoriere "invalid command name" Fehler beim Beenden
                if "invalid command name" in str(exc_value):
                    return
                # Andere Fehler normal loggen
                self.logger.error(
                    f"Tcl/Tk Fehler: {exc_value}", exc_info=(exc_type, exc_value, exc_tb))

            self.main_window.report_callback_exception = report_callback_exception

        self.logger.info("Main-Window angezeigt")
        
        # WICHTIG: MainWindow mainloop starten
        self.main_window.mainloop()

    def _on_new_project(self) -> None:
        """Handler: Neues Projekt erstellen"""
        self.logger.info("Erstelle neues Projekt")

        project = self.orchestrator.create_project("Neues Projekt")
        self.orchestrator.save_project()

        self._show_main_window()

    def _on_open_project(self, project_id: str) -> None:
        """Handler: Projekt öffnen"""
        if self.logger:
            self.logger.info(f"Öffne Projekt: {project_id}")

        success = self.orchestrator.load_project(project_id)

        if success:
            self._show_main_window()
        else:
            if self.logger:
                self.logger.error(f"Fehler beim Laden von Projekt {project_id}")
            # Fallback: Neues Projekt
            self._on_new_project()

    def _on_open_file_dialog(self) -> None:
        """Handler: Datei-Dialog für Projekt-Auswahl"""
        from tkinter import filedialog
        from pathlib import Path
        
        # Letzten verwendeten Pfad aus config.json holen
        config = self.orchestrator.load_config()
        
        # Startverzeichnis bestimmen
        initial_dir = None
        
        # 1. Priorität: Zuletzt verwendetes Verzeichnis (für Öffnen)
        last_open_dir = config.get('last_open_directory')
        if last_open_dir:
            last_dir_path = Path(last_open_dir)
            if last_dir_path.exists() and last_dir_path.is_dir():
                initial_dir = str(last_dir_path)
        
        # 2. Priorität: Ordner des letzten externen Projekts
        if not initial_dir:
            external_paths = config.get('external_project_paths', {})
            recent_projects = config.get('recent_projects', [])
            
            if recent_projects and external_paths:
                last_id = recent_projects[0]
                if last_id in external_paths:
                    last_path = Path(external_paths[last_id])
                    if last_path.exists():
                        initial_dir = str(last_path.parent)
        
        # 3. Fallback: Benutzer-Home-Verzeichnis (NICHT projects-Ordner!)
        if not initial_dir:
            initial_dir = str(Path.home())
        
        # Dateiauswahl-Dialog
        filepath = filedialog.askopenfilename(
            title="Projekt öffnen",
            initialdir=initial_dir,
            filetypes=[
                ("Projekt-Dateien", "*.json"),
                ("Alle Dateien", "*.*")
            ]
        )
        
        if filepath:
            # Speichere Verzeichnis für nächstes Mal
            selected_dir = str(Path(filepath).parent)
            config['last_open_directory'] = selected_dir
            self.orchestrator.persistence.save_config(config)
            
            # Lade Projekt aus Datei
            try:
                import json
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                project_id = data.get('id')
                if project_id:
                    # Registriere externen Pfad
                    self.orchestrator.persistence._register_external_project(project_id, filepath)
                    
                    # Öffne Projekt
                    self._on_open_project(project_id)
                else:
                    if self.logger:
                        self.logger.error("Ungültige Projekt-Datei: Keine ID gefunden")
                    self._on_new_project()
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Fehler beim Öffnen der Projekt-Datei: {e}")
                self._on_new_project()
        else:
            # User hat abgebrochen
            pass

    def run(self) -> None:
        """Startet Hauptschleife"""
        try:
            if self.logger:
                self.logger.info("Starte Hauptschleife")
            # Temp root mainloop für Welcome-Window
            self.temp_root.mainloop()
            
            # Nach temp_root.mainloop() endet (durch quit() beim MainWindow-Start)
            # wird automatisch die MainWindow.mainloop() in _show_main_window() gestartet
            
        except KeyboardInterrupt:
            if self.logger:
                self.logger.info("Programm durch Benutzer beendet")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Fehler in Hauptschleife: {e}", exc_info=True)
        finally:
            # Unterdrücke Tcl/Tk Fehler beim Beenden
            from io import StringIO
            old_stderr = sys.stderr
            try:
                sys.stderr = StringIO()  # Unterdrücke stderr temporär
                self._cleanup()
            finally:
                sys.stderr = old_stderr

    def _cleanup(self) -> None:
        """Cleanup beim Beenden"""
        if self.logger:
            self.logger.info("Cleanup...")

        try:
            # Konfiguration speichern
            if self.orchestrator:
                self.orchestrator.save_config()

                # Aktuelles Projekt speichern
                if self.orchestrator.state.current_project:
                    self.orchestrator.save_project()

            # WICHTIG: Alle geplanten Callbacks abbrechen BEVOR Widgets zerstört werden
            if self.main_window:
                try:
                    # Hole alle after-IDs
                    after_ids = self.main_window.tk.call('after', 'info')
                    # Breche jeden einzeln ab
                    for after_id in after_ids:
                        try:
                            self.main_window.after_cancel(after_id)
                        except:
                            pass
                except:
                    pass

        except Exception as e:
            self.logger.error(f"Fehler beim Cleanup: {e}")

        self.logger.info("Programm beendet")


def main():
    """
    Hauptfunktion
    """
    try:
        app = Application()
        app.run()
    except Exception as e:
        print(f"KRITISCHER FEHLER: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
