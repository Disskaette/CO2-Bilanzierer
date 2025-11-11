"""
Welcome-Window - Startbildschirm der Anwendung
"""

import customtkinter as ctk
from typing import Optional, Callable, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class WelcomeWindow(ctk.CTkToplevel):
    """
    Welcome-Screen beim Programmstart

    Zeigt:
    - Programmtitel und Version
    - Liste zuletzt geöffneter Projekte
    - Buttons: Neues Projekt, Projekt öffnen
    """

    VERSION = "2.0"

    def __init__(
        self,
        parent,
        recent_projects: List[Dict[str, Any]],
        on_new_project: Callable,
        on_open_project: Callable[[str], None],
        on_open_file_dialog: Callable
    ):
        """
        Args:
            parent: Parent-Fenster
            recent_projects: Liste mit Projekt-Metadaten
            on_new_project: Callback für "Neues Projekt"
            on_open_project: Callback für Projekt-Auswahl (project_id)
            on_open_file_dialog: Callback für "Projekt öffnen"
        """
        super().__init__(parent)

        self.on_new_project = on_new_project
        self.on_open_project = on_open_project
        self.on_open_file_dialog = on_open_file_dialog
        self.recent_projects = recent_projects

        self.logger = logger

        # Fenster-Konfiguration
        self.title("CO₂-Bilanzierer")
        self.geometry("700x600")
        self.resizable(False, False)

        # Zentrieren
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.winfo_screenheight() // 2) - (600 // 2)
        self.geometry(f"700x600+{x}+{y}")

        # UI erstellen
        self._build_ui()

        # Nach UI-Aufbau: Modal machen und in Vordergrund
        self.lift()
        self.focus_force()
        self.grab_set()

    def _build_ui(self) -> None:
        """Erstellt UI-Elemente"""

        # Container
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=40, pady=40)

        # Titel
        title_label = ctk.CTkLabel(
            main_frame,
            text="CO₂-Bilanzierer",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title_label.pack(pady=(0, 5))

        # Untertitel
        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="Ökobilanzierung nach ABC-Entwurfstafeln (Stand 2024-12)",
            font=ctk.CTkFont(size=12)
        )
        subtitle_label.pack(pady=(0, 5))

        # Version
        version_label = ctk.CTkLabel(
            main_frame,
            text=f"Version {self.VERSION}",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        version_label.pack(pady=(0, 30))

        # Aktionen
        actions_frame = ctk.CTkFrame(main_frame)
        actions_frame.pack(fill="x", pady=(0, 30))

        new_btn = ctk.CTkButton(
            actions_frame,
            text="Neues Projekt",
            command=self._on_new_project_click,
            height=50,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        new_btn.pack(fill="x", pady=5)

        open_btn = ctk.CTkButton(
            actions_frame,
            text="Projekt öffnen...",
            command=self._on_open_file_click,
            height=50,
            font=ctk.CTkFont(size=14)
        )
        open_btn.pack(fill="x", pady=5)

        # Zuletzt geöffnet
        if self.recent_projects:
            recent_label = ctk.CTkLabel(
                main_frame,
                text="Zuletzt geöffnet:",
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w"
            )
            recent_label.pack(fill="x", pady=(10, 10))

            # Scrollable Frame für Projekte
            recent_frame = ctk.CTkScrollableFrame(
                main_frame,
                height=250
            )
            recent_frame.pack(fill="both", expand=True)

            for project in self.recent_projects[:10]:  # Max. 10 anzeigen
                self._create_project_item(recent_frame, project)
        else:
            # Keine Projekte
            no_projects_label = ctk.CTkLabel(
                main_frame,
                text="Noch keine Projekte vorhanden.\nErstellen Sie ein neues Projekt, um zu beginnen.",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            no_projects_label.pack(pady=40)

    def _create_project_item(
        self,
        parent: ctk.CTkFrame,
        project: Dict[str, Any]
    ) -> None:
        """
        Erstellt ein Projekt-Item

        Args:
            parent: Parent-Frame
            project: Projekt-Metadaten
        """
        item_frame = ctk.CTkFrame(parent)
        item_frame.pack(fill="x", pady=3)

        # Name
        name_label = ctk.CTkLabel(
            item_frame,
            text=project.get('name', 'Unbenannt'),
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        name_label.pack(side="left", padx=10, pady=8)

        # Datum
        updated_at = project.get('updated_at', '')
        if updated_at:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(updated_at)
                date_str = dt.strftime("%d.%m.%Y %H:%M")
            except:
                date_str = updated_at[:16] if len(
                    updated_at) >= 16 else updated_at
        else:
            date_str = ""

        date_label = ctk.CTkLabel(
            item_frame,
            text=date_str,
            font=ctk.CTkFont(size=10),
            text_color="gray",
            anchor="e"
        )
        date_label.pack(side="right", padx=10, pady=8)

        # Click-Handler
        def on_click(event=None):
            self._on_project_selected(project['id'])

        item_frame.bind("<Button-1>", on_click)
        name_label.bind("<Button-1>", on_click)
        date_label.bind("<Button-1>", on_click)

        # Hover-Effekt
        def on_enter(event):
            item_frame.configure(fg_color=("gray85", "gray25"))

        def on_leave(event):
            item_frame.configure(fg_color=("gray90", "gray20"))

        item_frame.bind("<Enter>", on_enter)
        item_frame.bind("<Leave>", on_leave)

    def _on_new_project_click(self) -> None:
        """Handler für "Neues Projekt" """
        self.logger.info("Neues Projekt wird erstellt")
        self.destroy()
        self.on_new_project()

    def _on_open_file_click(self) -> None:
        """Handler für "Projekt öffnen" """
        self.logger.info("Datei-Dialog wird geöffnet")
        self.destroy()
        self.on_open_file_dialog()

    def _on_project_selected(self, project_id: str) -> None:
        """Handler für Projekt-Auswahl"""
        self.logger.info(f"Projekt ausgewählt: {project_id}")
        self.destroy()
        self.on_open_project(project_id)
