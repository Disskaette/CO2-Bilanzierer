"""
Material-Picker-Dialog - Suchfenster für Materialauswahl
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
from typing import Callable, Optional, List
import logging

from core.orchestrator import AppOrchestrator
from models.material import Material

logger = logging.getLogger(__name__)


class MaterialPickerDialog(ctk.CTkToplevel):
    """
    Dialog zur Materialauswahl aus CSV-Datenbank
    
    Features:
    - Suchfeld (live filter)
    - Dropdown Datensatztyp
    - Checkbox "nur Favoriten"
    - Tabelle mit Treffern
    - OK / Abbrechen
    """
    
    def __init__(
        self,
        parent,
        orchestrator: AppOrchestrator,
        on_select: Callable[[Material], None]
    ):
        """
        Args:
            parent: Parent-Fenster
            orchestrator: AppOrchestrator-Instanz
            on_select: Callback bei Auswahl (Material-Objekt)
        """
        super().__init__(parent)
        
        self.orchestrator = orchestrator
        self.on_select = on_select
        self.logger = logger
        
        self.selected_material: Optional[Material] = None
        self.search_results: List[Material] = []
        
        # Fenster-Konfiguration
        self.title("Material auswählen")
        self.geometry("1000x700")
        
        # Zentrieren
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"1000x700+{x}+{y}")
        
        # Modal
        self.transient(parent)
        self.grab_set()
        
        self._build_ui()
        
        # Initiale Suche
        self._perform_search()
    
    def _build_ui(self) -> None:
        """Erstellt UI"""
        
        # Header: Suchfilter
        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=10, pady=10)
        
        # Suchfeld
        search_label = ctk.CTkLabel(
            filter_frame,
            text="Suche:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        search_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.search_entry = ctk.CTkEntry(
            filter_frame,
            placeholder_text="Materialname, ID, Quelle...",
            width=300
        )
        self.search_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.search_entry.bind("<KeyRelease>", lambda e: self._perform_search())
        
        # Datensatztyp
        type_label = ctk.CTkLabel(
            filter_frame,
            text="Datensatztyp:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        type_label.grid(row=0, column=2, padx=(20, 5), pady=5, sticky="w")
        
        self.type_combo = ctk.CTkComboBox(
            filter_frame,
            values=["alle", "generisch", "spezifisch", "durchschnitt", "repräsentativ", "vorlage"],
            width=150,
            command=lambda v: self._perform_search()
        )
        self.type_combo.set("alle")
        self.type_combo.grid(row=0, column=3, padx=5, pady=5)
        
        # Favoriten-Checkbox
        self.favorites_var = ctk.BooleanVar(value=False)
        self.favorites_cb = ctk.CTkCheckBox(
            filter_frame,
            text="Nur Favoriten",
            variable=self.favorites_var,
            command=self._perform_search
        )
        self.favorites_cb.grid(row=0, column=4, padx=20, pady=5)
        
        filter_frame.columnconfigure(1, weight=1)
        
        # Info-Label
        self.info_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.info_label.pack(anchor="w", padx=15)
        
        # Tabelle
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self._create_table(table_frame)
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ok_btn = ctk.CTkButton(
            button_frame,
            text="OK",
            command=self._on_ok,
            width=120,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        ok_btn.pack(side="right", padx=5)
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Abbrechen",
            command=self.destroy,
            width=120,
            height=40
        )
        cancel_btn.pack(side="right", padx=5)
    
    def _create_table(self, parent: ctk.CTkFrame) -> None:
        """Erstellt Treffer-Tabelle"""
        
        columns = (
            "name", "source", "type", "unit",
            "gwp_a", "gwp_c3", "gwp_c4", "gwp_d", "id"
        )
        
        self.tree = ttk.Treeview(
            parent,
            columns=columns,
            show="headings",
            height=20
        )
        
        # Überschriften
        self.tree.heading("name", text="Name")
        self.tree.heading("source", text="Quelle/Hersteller")
        self.tree.heading("type", text="Datensatztyp")
        self.tree.heading("unit", text="Einheit")
        self.tree.heading("gwp_a", text="GWP A1-A3")
        self.tree.heading("gwp_c3", text="GWP C3")
        self.tree.heading("gwp_c4", text="GWP C4")
        self.tree.heading("gwp_d", text="GWP D")
        self.tree.heading("id", text="ID")
        
        # Spaltenbreiten
        self.tree.column("name", width=250)
        self.tree.column("source", width=150)
        self.tree.column("type", width=120)
        self.tree.column("unit", width=60)
        self.tree.column("gwp_a", width=90)
        self.tree.column("gwp_c3", width=80)
        self.tree.column("gwp_c4", width=80)
        self.tree.column("gwp_d", width=80)
        self.tree.column("id", width=120)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Doppelklick → OK
        self.tree.bind("<Double-Button-1>", lambda e: self._on_ok())
        
        # Auswahl-Handler
        self.tree.bind("<<TreeviewSelect>>", self._on_selection_changed)
    
    def _perform_search(self) -> None:
        """Führt Suche durch und aktualisiert Tabelle"""
        
        # Suchparameter
        query = self.search_entry.get()
        dataset_type = self.type_combo.get()
        favorites_only = self.favorites_var.get()
        
        # Suche durchführen
        try:
            results = self.orchestrator.search_materials(
                query=query,
                dataset_type=dataset_type if dataset_type != "alle" else None,
                favorites_only=favorites_only
            )
            
            self.search_results = results
            
            # Info aktualisieren
            csv_meta = self.orchestrator.get_csv_metadata()
            total = csv_meta.get('count', 0)
            self.info_label.configure(
                text=f"{len(results)} von {total} Materialien"
            )
            
            # Tabelle füllen
            self._populate_table(results)
            
        except Exception as e:
            self.logger.error(f"Fehler bei Suche: {e}", exc_info=True)
            messagebox.showerror("Fehler", f"Fehler bei der Suche:\n{e}")
    
    def _populate_table(self, materials: List[Material]) -> None:
        """Füllt Tabelle mit Materialien"""
        
        # Alte Einträge löschen
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Neue Einträge einfügen (max. 500 zur Performance)
        for i, mat in enumerate(materials[:500]):
            values = (
                mat.name[:50],
                mat.source[:30],
                mat.dataset_type,
                mat.unit,
                f"{mat.gwp_a1a3:.3f}",
                f"{mat.gwp_c3:.3f}",
                f"{mat.gwp_c4:.3f}",
                f"{mat.gwp_d:.3f}" if mat.gwp_d is not None else "-",
                mat.id[:20]
            )
            
            self.tree.insert("", "end", values=values, iid=str(i))
        
        if len(materials) > 500:
            self.info_label.configure(
                text=f"{len(materials)} Treffer (erste 500 angezeigt)"
            )
    
    def _on_selection_changed(self, event=None) -> None:
        """Handler für Auswahl-Änderung"""
        selection = self.tree.selection()
        if selection:
            try:
                index = int(selection[0])
                if 0 <= index < len(self.search_results):
                    self.selected_material = self.search_results[index]
            except (ValueError, IndexError):
                pass
    
    def _on_ok(self) -> None:
        """Handler für OK-Button"""
        if not self.selected_material:
            messagebox.showwarning(
                "Keine Auswahl",
                "Bitte wählen Sie ein Material aus"
            )
            return
        
        self.logger.info(f"Material ausgewählt: {self.selected_material.name}")
        
        # Callback aufrufen
        self.on_select(self.selected_material)
        
        # Dialog schließen
        self.destroy()
