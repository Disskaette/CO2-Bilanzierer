"""
Project-Tree-View - Dateibaum für Projekte
"""

import customtkinter as ctk
from tkinter import ttk
from typing import Optional
import logging

from core.orchestrator import AppOrchestrator

logger = logging.getLogger(__name__)


class ProjectTreeView(ctk.CTkFrame):
    """
    Dateibaum-Ansicht (links im Hauptfenster)
    
    Zeigt:
    - Projekt-Struktur
    - Varianten
    - Suchfeld
    """
    
    def __init__(self, parent, orchestrator: AppOrchestrator):
        super().__init__(parent)
        
        self.orchestrator = orchestrator
        self.logger = logger
        
        self._build_ui()
    
    def _build_ui(self) -> None:
        """Erstellt UI"""
        
        # Titel
        title_label = ctk.CTkLabel(
            self,
            text="Projekt",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.pack(pady=10, padx=10, anchor="w")
        
        # Tree (readonly Textbox)
        tree_container = ctk.CTkFrame(self)
        tree_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.tree_text = ctk.CTkTextbox(
            tree_container,
            wrap="none"
        )
        self.tree_text.pack(fill="both", expand=True)
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        add_btn = ctk.CTkButton(
            button_frame,
            text="+ Variante",
            width=100,
            command=self._add_variant
        )
        add_btn.pack(side="left", padx=2)
        
        del_btn = ctk.CTkButton(
            button_frame,
            text="- Variante",
            width=100,
            fg_color="darkred",
            command=self._delete_variant
        )
        del_btn.pack(side="left", padx=2)
        
        refresh_btn = ctk.CTkButton(
            button_frame,
            text="↻",
            width=40,
            command=self.refresh
        )
        refresh_btn.pack(side="right", padx=2)
        
        self.refresh()
    
    def refresh(self) -> None:
        """Aktualisiert Baum"""
        project = self.orchestrator.get_current_project()
        
        self.tree_text.delete("1.0", "end")
        
        if not project:
            self.tree_text.insert("1.0", "Kein Projekt geladen")
            return
        
        # Projekt-Name
        self.tree_text.insert("end", f"📁 {project.name}\n\n")
        
        # Varianten (nur Namen ohne Nummerierung)
        if project.variants:
            for variant in project.variants:
                row_count = len(variant.rows)
                self.tree_text.insert(
                    "end",
                    f"  📄 {variant.name} ({row_count} Zeilen)\n"
                )
        else:
            self.tree_text.insert("end", "  Keine Varianten vorhanden\n")
    
    def _add_variant(self) -> None:
        """Fügt neue Variante hinzu"""
        variant = self.orchestrator.create_variant()
        if variant:
            self.refresh()
            self.logger.info("Variante hinzugefügt")
            
            # Trigger Event für MainWindow um Tabs neu zu bauen
            project = self.orchestrator.get_current_project()
            if project:
                self.orchestrator.state.trigger('variant_added', len(project.variants))
        else:
            self.logger.warning("Maximale Anzahl Varianten (5) erreicht")
    
    def _delete_variant(self) -> None:
        """Löscht die zuletzt ausgewählte/letzte Variante"""
        from tkinter import messagebox
        
        project = self.orchestrator.get_current_project()
        if not project or not project.variants:
            messagebox.showwarning("Keine Variante", "Keine Variante zum Löschen vorhanden")
            return
        
        # Letzte Variante löschen
        last_variant = project.variants[-1]
        
        if messagebox.askyesno("Bestätigen", f"Variante '{last_variant.name}' wirklich löschen?"):
            project.variants.pop()
            self.orchestrator.notify_change()
            self.refresh()
            self.logger.info(f"Variante gelöscht: {last_variant.name}")
            
            # Trigger Event für MainWindow um Tabs neu zu bauen
            self.orchestrator.state.trigger('variant_deleted', len(project.variants))
