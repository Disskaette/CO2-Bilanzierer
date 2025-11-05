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
        self.geometry("1400x750")
        
        # Zentrieren
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (1400 // 2)
        y = (self.winfo_screenheight() // 2) - (750 // 2)
        self.geometry(f"1400x750+{x}+{y}")
        
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
        
        # EN 15804+A2 Checkbox
        self.en15804_var = ctk.BooleanVar(value=True)  # Standardmäßig aktiviert
        self.en15804_cb = ctk.CTkCheckBox(
            filter_frame,
            text="Nur EN 15804+A2",
            variable=self.en15804_var,
            command=self._perform_search
        )
        self.en15804_cb.grid(row=0, column=4, padx=10, pady=5)
        
        # Button: Eigenes Material
        custom_btn = ctk.CTkButton(
            filter_frame,
            text="+ Eigenes Material",
            width=140,
            command=self._on_add_custom_material,
            fg_color="darkgreen"
        )
        custom_btn.grid(row=0, column=5, padx=10, pady=5)
        
        filter_frame.columnconfigure(1, weight=1)
        
        # Info-Label
        self.info_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.info_label.pack(anchor="w", padx=15, pady=(0, 5))
        
        # Tab-System (nur für Filterung, keine Inhalte)
        self.tab_view = ctk.CTkTabview(self, height=40)
        self.tab_view.pack(fill="x", padx=10, pady=(0, 5))
        
        # Tabs erstellen
        self.tab_all = self.tab_view.add("Alle Materialien")
        self.tab_recent = self.tab_view.add("Zuletzt benutzt")
        self.tab_favorites = self.tab_view.add("Favoriten")
        
        # Tab-Wechsel-Handler
        self.tab_view.configure(command=self._on_tab_changed)
        
        # Tabelle (außerhalb der Tabs, immer sichtbar)
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
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
            "fav", "name", "source", "type", "unit",
            "gwp_a", "gwp_c3", "gwp_c4", "gwp_d", "id"
        )
        
        self.tree = ttk.Treeview(
            parent,
            columns=columns,
            show="tree headings",
            height=20
        )
        
        # Überschriften
        self.tree.heading("#0", text="★")  # Favoriten-Spalte
        self.tree.heading("fav", text="Fav")
        self.tree.heading("name", text="Name")
        self.tree.heading("source", text="Quelle/Hersteller")
        self.tree.heading("type", text="Datensatztyp")
        self.tree.heading("unit", text="Einheit")
        self.tree.heading("gwp_a", text="GWP A1-A3")
        self.tree.heading("gwp_c3", text="GWP C3")
        self.tree.heading("gwp_c4", text="GWP C4")
        self.tree.heading("gwp_d", text="GWP D")
        self.tree.heading("id", text="ID")
        
        # Spaltenbreiten (angepasst)
        self.tree.column("#0", width=30, stretch=False)  # Favoriten-Icon
        self.tree.column("fav", width=0, stretch=False)  # Versteckt, nur für Daten
        self.tree.column("name", width=300, minwidth=200)  # Volle Namen
        self.tree.column("source", width=180, minwidth=150)
        self.tree.column("type", width=100, stretch=False)  # Feste Breite
        self.tree.column("unit", width=60, stretch=False)  # Feste Breite
        self.tree.column("gwp_a", width=90, stretch=False)
        self.tree.column("gwp_c3", width=70, stretch=False)
        self.tree.column("gwp_c4", width=70, stretch=False)
        self.tree.column("gwp_d", width=70, stretch=False)
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
        
        # Klick auf Favoriten-Spalte → Toggle Favorit
        self.tree.bind("<Button-1>", self._on_tree_click)
        
        # Rechtsklick für Custom Materials → Löschen
        self.tree.bind("<Button-2>", self._on_right_click)  # Mac
        self.tree.bind("<Button-3>", self._on_right_click)  # Windows/Linux
    
    def _on_tab_changed(self) -> None:
        """Handler für Tab-Wechsel"""
        self._perform_search()
    
    def _perform_search(self) -> None:
        """Führt Suche durch und aktualisiert Tabelle"""
        
        # Suchparameter
        query = self.search_entry.get()
        dataset_type = self.type_combo.get()
        en15804_a2_only = self.en15804_var.get()
        
        # Prüfen welcher Tab aktiv ist
        active_tab = self.tab_view.get()
        recently_used_only = (active_tab == "Zuletzt benutzt")
        favorites_only = (active_tab == "Favoriten")
        
        # Suche durchführen
        try:
            if recently_used_only:
                # Zuletzt benutzte Materialien holen
                results = self.orchestrator.get_recently_used_materials()
                
                # Optional: Filter anwenden (query, dataset_type, en15804_a2)
                if query:
                    query_lower = query.lower()
                    results = [
                        mat for mat in results
                        if query_lower in mat.name.lower() or
                           query_lower in mat.source.lower() or
                           query_lower in mat.id.lower()
                    ]
                
                if dataset_type and dataset_type != "alle":
                    results = [mat for mat in results if mat.dataset_type == dataset_type]
                
                if en15804_a2_only:
                    results = [mat for mat in results if mat.is_en15804_a2()]
            else:
                # Normale Suche (Alle Materialien oder Favoriten)
                results = self.orchestrator.search_materials(
                    query=query,
                    dataset_type=dataset_type if dataset_type != "alle" else None,
                    favorites_only=favorites_only,
                    en15804_a2_only=en15804_a2_only
                )
            
            self.search_results = results
            
            # Info aktualisieren
            csv_meta = self.orchestrator.get_csv_metadata()
            total = csv_meta.get('count', 0)
            info_text = f"{len(results)} von {total} Materialien"
            if recently_used_only:
                info_text = f"{len(results)} zuletzt benutzte Materialien"
            elif favorites_only:
                info_text = f"{len(results)} Favoriten"
            self.info_label.configure(text=info_text)
            
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
            # Prüfen ob Favorit
            is_fav = self.orchestrator.material_repo.is_favorite(mat.id)
            
            # Icon: Custom=🔧, Favorit=★, Normal=☆
            if mat.is_custom:
                icon = "🔧"
            elif is_fav:
                icon = "★"
            else:
                icon = "☆"
            
            values = (
                "1" if is_fav else "0",  # Versteckter Wert für Sortierung
                mat.name,  # Voller Name, nicht abgeschnitten
                mat.source,  # Volle Quelle
                mat.dataset_type,
                mat.unit,
                f"{mat.gwp_a1a3:.3f}",
                f"{mat.gwp_c3:.3f}",
                f"{mat.gwp_c4:.3f}",
                f"{mat.gwp_d:.3f}" if mat.gwp_d is not None else "-",
                mat.id
            )
            
            # Tags für Custom Materials
            tags = []
            if is_fav:
                tags.append("fav")
            if mat.is_custom:
                tags.append("custom")
            
            self.tree.insert("", "end", text=icon, values=values, iid=str(i), tags=tuple(tags))
        
        if len(materials) > 500:
            self.info_label.configure(
                text=f"{len(materials)} Treffer (erste 500 angezeigt)"
            )
    
    def _on_tree_click(self, event) -> None:
        """Handler für Klick auf Tree (Favoriten-Toggle)"""
        region = self.tree.identify("region", event.x, event.y)
        if region == "tree":  # Klick auf Icon-Spalte
            item = self.tree.identify_row(event.y)
            if item:
                try:
                    index = int(item)
                    if 0 <= index < len(self.search_results):
                        mat = self.search_results[index]
                        
                        # Toggle Favorit
                        was_favorite = self.orchestrator.material_repo.is_favorite(mat.id)
                        if was_favorite:
                            self.orchestrator.material_repo.remove_favorite(mat.id)
                        else:
                            self.orchestrator.material_repo.add_favorite(mat.id, mat.name)
                        
                        # Konfiguration speichern um Favoriten zu persistieren
                        self.orchestrator.save_config()
                        
                        # Optimierte Aktualisierung
                        active_tab = self.tab_view.get()
                        if active_tab in ["Favoriten", "Zuletzt benutzt"]:
                            # Filter ist aktiv: Komplette Suche neu durchführen
                            # (Material könnte aus der Liste verschwinden müssen)
                            self._perform_search()
                        else:
                            # Kein Filter aktiv: Nur Icon in der Zeile aktualisieren
                            # -> Viel schneller!
                            is_now_favorite = not was_favorite
                            if mat.is_custom:
                                new_icon = "🔧"
                            elif is_now_favorite:
                                new_icon = "★"
                            else:
                                new_icon = "☆"
                            
                            # Icon und versteckten Wert aktualisieren
                            values = list(self.tree.item(item, "values"))
                            values[0] = "1" if is_now_favorite else "0"
                            
                            # Tags aktualisieren
                            tags = list(self.tree.item(item, "tags"))
                            if is_now_favorite and "fav" not in tags:
                                tags.append("fav")
                            elif not is_now_favorite and "fav" in tags:
                                tags.remove("fav")
                            
                            self.tree.item(item, text=new_icon, values=values, tags=tuple(tags))
                            
                except (ValueError, IndexError):
                    pass
    
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
    
    def _on_add_custom_material(self) -> None:
        """Handler für '+ Eigenes Material' Button"""
        from ui.dialogs.custom_material_dialog import CustomMaterialDialog
        
        def on_save(material: Material) -> None:
            """Callback wenn Custom Material gespeichert wurde"""
            # In Repository speichern
            success = self.orchestrator.material_repo.save_custom_material(material)
            
            if success:
                messagebox.showinfo(
                    "Erfolg",
                    f"Material '{material.name}' wurde gespeichert.\n\n"
                    f"Es ist jetzt in der Suche verfügbar."
                )
                
                # Suche aktualisieren
                self._perform_search()
            else:
                messagebox.showerror(
                    "Fehler",
                    "Das Material konnte nicht gespeichert werden."
                )
        
        # Dialog öffnen
        dialog = CustomMaterialDialog(self, on_save)
        dialog.focus()
    
    def _on_right_click(self, event) -> None:
        """Handler für Rechtsklick (Context Menu für Custom Materials)"""
        # Item unter Maus finden
        item = self.tree.identify_row(event.y)
        if not item:
            return
        
        try:
            index = int(item)
            if 0 <= index < len(self.search_results):
                material = self.search_results[index]
                
                # Nur für Custom Materials Context-Menu anzeigen
                if material.is_custom:
                    import tkinter as tk
                    
                    # Context Menu erstellen
                    menu = tk.Menu(self, tearoff=0)
                    menu.add_command(
                        label=f"🗑️ '{material.name}' löschen",
                        command=lambda: self._delete_custom_material(material)
                    )
                    
                    # Menu anzeigen
                    menu.post(event.x_root, event.y_root)
        except (ValueError, IndexError):
            pass
    
    def _delete_custom_material(self, material: Material) -> None:
        """Löscht ein Custom Material"""
        # Bestätigung
        answer = messagebox.askyesno(
            "Material löschen",
            f"Möchten Sie das eigene Material\n\n'{material.name}'\n\nwirklich löschen?\n\n"
            f"Diese Aktion kann nicht rückgängig gemacht werden."
        )
        
        if answer:
            success = self.orchestrator.material_repo.delete_custom_material(material.id)
            
            if success:
                messagebox.showinfo(
                    "Gelöscht",
                    f"Material '{material.name}' wurde gelöscht."
                )
                
                # Suche aktualisieren
                self._perform_search()
            else:
                messagebox.showerror(
                    "Fehler",
                    "Das Material konnte nicht gelöscht werden."
                )
