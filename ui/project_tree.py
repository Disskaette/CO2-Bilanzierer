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
        
        # Tree (readonly Textbox mit selektierbarem Text)
        tree_container = ctk.CTkFrame(self)
        tree_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.tree_text = ctk.CTkTextbox(
            tree_container,
            wrap="none"
        )
        self.tree_text.pack(fill="both", expand=True)
        
        # Textbox nicht editierbar machen, aber Text selektierbar lassen
        # Binding für readonly verhalten
        def make_readonly(event):
            return "break"  # Verhindert Textänderungen
        
        self.tree_text.bind("<Key>", make_readonly)
        self.tree_text.bind("<Control-v>", make_readonly)
        self.tree_text.bind("<Command-v>", make_readonly)
        
        # Buttons (in einer Linie)
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
        
        self.refresh()
    
    def refresh(self) -> None:
        """Aktualisiert Baum"""
        project = self.orchestrator.get_current_project()
        
        # Textbox kurz entsperren für Aktualisierung
        self.tree_text.configure(state="normal")
        self.tree_text.delete("1.0", "end")
        
        if not project:
            self.tree_text.insert("1.0", "Kein Projekt geladen")
            self.tree_text.configure(state="disabled")
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
        
        # Textbox wieder sperren
        self.tree_text.configure(state="disabled")
    
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
        """Öffnet Dialog zur Auswahl der zu löschenden Variante"""
        from tkinter import messagebox
        
        project = self.orchestrator.get_current_project()
        if not project or not project.variants:
            messagebox.showwarning("Keine Variante", "Keine Variante zum Löschen vorhanden")
            return
        
        # Dialog zur Auswahl der Variante
        self._show_variant_selection_dialog(project)
    
    def _show_variant_selection_dialog(self, project) -> None:
        """Zeigt Dialog zur Auswahl einer zu löschenden Variante"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Variante löschen")
        dialog.geometry("400x300")
        dialog.transient(self.master)
        dialog.grab_set()
        
        # Titel
        title_label = ctk.CTkLabel(
            dialog,
            text="Welche Variante möchten Sie löschen?",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.pack(pady=10)
        
        # Varianten-Liste
        list_frame = ctk.CTkFrame(dialog)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        selected_index = ctk.IntVar(value=-1)
        
        for i, variant in enumerate(project.variants):
            row_count = len(variant.rows)
            radio = ctk.CTkRadioButton(
                list_frame,
                text=f"{variant.name} ({row_count} Zeilen)",
                variable=selected_index,
                value=i
            )
            radio.pack(anchor="w", padx=10, pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(fill="x", padx=20, pady=10)
        
        def on_delete():
            idx = selected_index.get()
            if idx == -1:
                from tkinter import messagebox
                messagebox.showwarning("Keine Auswahl", "Bitte wählen Sie eine Variante aus")
                return
            
            variant_to_delete = project.variants[idx]
            
            from tkinter import messagebox
            if messagebox.askyesno("Bestätigen", f"Variante '{variant_to_delete.name}' wirklich löschen?"):
                # Variante löschen
                project.variants.pop(idx)
                self.orchestrator.notify_change()
                self.refresh()
                self.logger.info(f"Variante gelöscht: {variant_to_delete.name}")
                
                # Trigger Event für MainWindow um Tabs neu zu bauen
                self.orchestrator.state.trigger('variant_deleted', len(project.variants))
                
                dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        delete_btn = ctk.CTkButton(
            button_frame,
            text="Löschen",
            fg_color="darkred",
            command=on_delete
        )
        delete_btn.pack(side="left", padx=5, expand=True, fill="x")
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Abbrechen",
            command=on_cancel
        )
        cancel_btn.pack(side="right", padx=5, expand=True, fill="x")
