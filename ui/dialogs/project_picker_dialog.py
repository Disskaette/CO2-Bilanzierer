"""
Project Picker Dialog - Projekt aus Liste wählen oder durchsuchen
"""

import customtkinter as ctk
from tkinter import filedialog
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class ProjectPickerDialog(ctk.CTkToplevel):
    """
    Dialog zum Auswählen eines Projekts
    
    Zeigt:
    - Liste der zuletzt geöffneten Projekte
    - Button zum Durchsuchen
    """
    
    def __init__(self, parent, orchestrator):
        super().__init__(parent)
        
        self.orchestrator = orchestrator
        self.selected_project_id: Optional[str] = None
        self.selected_filepath: Optional[str] = None
        
        # Fenster-Konfiguration
        self.title("Projekt öffnen")
        self.geometry("600x500")
        self.resizable(False, False)
        
        # Modal
        self.transient(parent)
        self.grab_set()
        
        # Zentrieren
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.winfo_screenheight() // 2) - (500 // 2)
        self.geometry(f"+{x}+{y}")
        
        self._build_ui()
        
    def _build_ui(self):
        """Erstellt UI"""
        # Header
        header = ctk.CTkLabel(
            self,
            text="Projekt öffnen",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        header.pack(pady=20)
        
        # Zuletzt geöffnete Projekte
        projects = self.orchestrator.list_projects()
        
        if projects:
            # Label
            recent_label = ctk.CTkLabel(
                self,
                text="Zuletzt geöffnet:",
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w"
            )
            recent_label.pack(fill="x", padx=20, pady=(10, 5))
            
            # Scrollable Frame
            projects_frame = ctk.CTkScrollableFrame(
                self,
                height=250
            )
            projects_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            # Projekte anzeigen (max. 10)
            for project in projects[:10]:
                self._create_project_item(projects_frame, project)
        else:
            # Keine Projekte
            no_projects_label = ctk.CTkLabel(
                self,
                text="Keine zuletzt geöffneten Projekte vorhanden",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            no_projects_label.pack(pady=40)
        
        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=20)
        
        # Durchsuchen Button
        browse_btn = ctk.CTkButton(
            button_frame,
            text="Durchsuchen...",
            command=self._browse_file,
            height=40
        )
        browse_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        # Abbrechen Button
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Abbrechen",
            command=self._cancel,
            fg_color="gray",
            hover_color="darkgray",
            height=40
        )
        cancel_btn.pack(side="right", expand=True, fill="x", padx=(5, 0))
    
    def _create_project_item(self, parent, project: Dict[str, Any]):
        """Erstellt ein klickbares Projekt-Item"""
        item_frame = ctk.CTkFrame(parent)
        item_frame.pack(fill="x", pady=3)
        
        # Name
        name_text = project.get('name', 'Unbenannt')
        
        name_label = ctk.CTkLabel(
            item_frame,
            text=name_text,
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
                date_str = updated_at[:16] if len(updated_at) >= 16 else updated_at
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
            self._select_project(project['id'])
        
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
    
    def _select_project(self, project_id: str):
        """Projekt aus Liste ausgewählt"""
        self.selected_project_id = project_id
        self.destroy()
    
    def _browse_file(self):
        """Datei-Browser öffnen"""
        # Intelligentes Startverzeichnis
        config = self.orchestrator.load_config()
        initial_dir = None
        
        # 1. Priorität: Letztes Öffnen-Verzeichnis
        last_open_dir = config.get('last_open_directory')
        if last_open_dir:
            last_dir_path = Path(last_open_dir)
            if last_dir_path.exists() and last_dir_path.is_dir():
                initial_dir = str(last_dir_path)
        
        # 2. Fallback: Home
        if not initial_dir:
            initial_dir = str(Path.home())
        
        filepath = filedialog.askopenfilename(
            parent=self,
            title="Projekt öffnen",
            initialdir=initial_dir,
            filetypes=[
                ("Projekt-Dateien", "*.json"),
                ("Alle Dateien", "*.*")
            ]
        )
        
        if filepath:
            # Speichere Verzeichnis
            selected_dir = str(Path(filepath).parent)
            config['last_open_directory'] = selected_dir
            self.orchestrator.persistence.save_config(config)
            
            # Lese Projekt-ID aus Datei
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                project_id = data.get('id')
                if project_id:
                    # Registriere externen Pfad
                    self.orchestrator.persistence._register_external_project(project_id, filepath)
                    self.selected_project_id = project_id
                    self.destroy()
                else:
                    logger.error("Ungültige Projekt-Datei: Keine ID gefunden")
            except Exception as e:
                logger.error(f"Fehler beim Lesen der Projekt-Datei: {e}")
    
    def _cancel(self):
        """Abbrechen"""
        self.selected_project_id = None
        self.destroy()
