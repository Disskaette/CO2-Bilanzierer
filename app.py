"""
ABC-CO₂-Bilanzierer
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
from utils.logging_config import setup_logging
from utils.demo_project import create_demo_project


class Application:
    """
    Hauptanwendung
    Verwaltet Welcome-Window → Main-Window Übergang
    """

    VERSION = "1.0.0"

    def __init__(self):
        # Orchestrator initialisieren
        self.orchestrator = AppOrchestrator()

        # Logging einrichten
        log_path = Path(self.orchestrator.get_log_path())
        setup_logging(log_path)

        self.logger = logging.getLogger(__name__)
        self.logger.info(f"ABC-CO₂-Bilanzierer v{self.VERSION} gestartet")

        # Temporäres Root-Window für WelcomeWindow
        self.temp_root = ctk.CTk()
        self.temp_root.withdraw()  # Komplett verstecken
        
        # Main-Window (wird später erstellt und ist dann das echte Root)
        self.main_window = None

        # Standard-CSV laden
        self._load_default_csv()

        # Demo-Projekt laden oder erstellen
        self._load_or_create_demo_project()

        # Welcome-Window anzeigen (nach kurzer Verzögerung für GUI-Init)
        self.temp_root.after(100, self._show_welcome)

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
            self.logger.info("Sie können später über 'CSV laden' eine Datenbank laden")

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
        # Temp-Root schließen
        self.temp_root.destroy()
        
        # Main-Window als neues Root erstellen
        if not self.main_window:
            self.main_window = MainWindow(self.orchestrator)

        self.logger.info("Main-Window angezeigt")

    def _on_new_project(self) -> None:
        """Handler: Neues Projekt erstellen"""
        self.logger.info("Erstelle neues Projekt")

        project = self.orchestrator.create_project("Neues Projekt")
        self.orchestrator.save_project()

        self._show_main_window()

    def _on_open_project(self, project_id: str) -> None:
        """Handler: Projekt öffnen"""
        self.logger.info(f"Öffne Projekt: {project_id}")

        success = self.orchestrator.load_project(project_id)

        if success:
            self._show_main_window()
        else:
            self.logger.error(f"Fehler beim Laden von Projekt {project_id}")
            # Fallback: Neues Projekt
            self._on_new_project()

    def _on_open_file_dialog(self) -> None:
        """Handler: Datei-Dialog für Projekt-Auswahl"""
        # TODO: Implementiere Dateiauswahl-Dialog
        self.logger.warning("Datei-Dialog noch nicht implementiert")
        self._on_new_project()

    def run(self) -> None:
        """Startet Hauptschleife"""
        try:
            self.logger.info("Starte Hauptschleife")
            self.temp_root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("Programm durch Benutzer beendet")
        except Exception as e:
            self.logger.error(f"Fehler in Hauptschleife: {e}", exc_info=True)
        finally:
            self._cleanup()

    def _cleanup(self) -> None:
        """Cleanup beim Beenden"""
        self.logger.info("Cleanup...")

        # Konfiguration speichern
        self.orchestrator.save_config()

        # Aktuelles Projekt speichern
        if self.orchestrator.state.current_project:
            self.orchestrator.save_project()

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
