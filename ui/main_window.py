"""
Main-Window - Hauptfenster der Anwendung
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Optional
import logging

from core.orchestrator import AppOrchestrator
from ui.project_tree import ProjectTreeView
from ui.dashboard.dashboard_view import DashboardView
from ui.variants.variant_view import VariantView

logger = logging.getLogger(__name__)


class MainWindow(ctk.CTk):
    """
    Hauptfenster der Anwendung
    
    Layout:
    - Oben: Menüleiste
    - Links: Dateibaum (ProjectTreeView)
    - Rechts: Tab-Leiste + Inhalt (Dashboard oder Varianten)
    """
    
    def __init__(self, orchestrator: AppOrchestrator):
        super().__init__()
        
        self.orchestrator = orchestrator
        self.logger = logger
        
        # Fenster-Konfiguration
        self.title("ABC-CO₂-Bilanzierer")
        self.geometry("1400x900")
        
        # Theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # UI-Komponenten
        self.project_tree: Optional[ProjectTreeView] = None
        self.dashboard_view: Optional[DashboardView] = None
        self.variant_views: list[Optional[VariantView]] = [None] * 5
        
        # Aktuelle Tab-Ansicht
        self.current_tab = 0
        self.tab_buttons: list[ctk.CTkButton] = []
        
        # Event-Registrierung
        self._register_orchestrator_events()
        
        self._build_ui()
        
        self.logger.info("MainWindow initialisiert")
    
    def _register_orchestrator_events(self) -> None:
        """Registriert Callbacks beim Orchestrator"""
        self.orchestrator.state.register_callback('project_loaded', self._on_project_loaded)
        self.orchestrator.state.register_callback('csv_loaded', self._on_csv_loaded)
        self.orchestrator.state.register_callback('row_updated', self._on_row_updated)
        self.orchestrator.state.register_callback('rebuild_charts', self._on_rebuild_charts)
        self.orchestrator.state.register_callback('autosave_failed', self._on_autosave_failed)
        self.orchestrator.state.register_callback('variant_renamed', self._on_variant_renamed)
        self.orchestrator.state.register_callback('variant_deleted', self._on_variant_deleted)
        self.orchestrator.state.register_callback('variant_added', self._on_variant_added)
    
    def _build_ui(self) -> None:
        """Erstellt UI-Struktur"""
        
        # Menüleiste
        self._create_menu()
        
        # Hauptlayout: Links Dateibaum, rechts Content
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Links: Project Tree
        tree_frame = ctk.CTkFrame(main_container, width=250)
        tree_frame.pack(side="left", fill="y", padx=(0, 5))
        tree_frame.pack_propagate(False)
        
        self.project_tree = ProjectTreeView(tree_frame, self.orchestrator)
        self.project_tree.pack(fill="both", expand=True)
        
        # Rechts: Tab-Area
        right_container = ctk.CTkFrame(main_container)
        right_container.pack(side="right", fill="both", expand=True)
        
        # Systemgrenze-Leiste (über Tabs)
        boundary_bar = ctk.CTkFrame(right_container, height=45)
        boundary_bar.pack(fill="x", padx=5, pady=(5, 0))
        
        boundary_label = ctk.CTkLabel(
            boundary_bar,
            text="Systemgrenze:",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        boundary_label.pack(side="left", padx=15)
        
        project = self.orchestrator.get_current_project()
        current_boundary = project.system_boundary if project else "A1-A3"
        boundaries = ["A1-A3", "A1-A3+C3+C4", "A1-A3+C3+C4+D"]
        
        self.boundary_combo = ctk.CTkComboBox(
            boundary_bar,
            values=boundaries,
            width=200,
            command=self._on_boundary_changed
        )
        self.boundary_combo.set(current_boundary)
        self.boundary_combo.pack(side="left", padx=5)
        
        # Info-Label für CSV
        csv_info = self._get_csv_info()
        self.csv_info_label = ctk.CTkLabel(
            boundary_bar,
            text=csv_info,
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.csv_info_label.pack(side="right", padx=15)
        
        # Tab-Leiste
        tab_bar = ctk.CTkFrame(right_container, height=50)
        tab_bar.pack(fill="x", padx=5, pady=5)
        
        self._create_tab_bar(tab_bar)
        
        # Content-Area
        self.content_frame = ctk.CTkFrame(right_container)
        self.content_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        # Initial: Dashboard anzeigen
        self._show_dashboard()
    
    def _create_menu(self) -> None:
        """Erstellt Menüleiste (vereinfacht als Button-Leiste)"""
        menu_frame = ctk.CTkFrame(self, height=40)
        menu_frame.pack(fill="x", padx=5, pady=5)
        
        # Datei-Menü
        file_btn = ctk.CTkButton(
            menu_frame,
            text="Datei",
            width=80,
            command=self._show_file_menu
        )
        file_btn.pack(side="left", padx=2)
        
        # CSV laden
        csv_btn = ctk.CTkButton(
            menu_frame,
            text="CSV laden",
            width=100,
            command=self._load_csv_dialog
        )
        csv_btn.pack(side="left", padx=2)
        
        # Export
        export_btn = ctk.CTkButton(
            menu_frame,
            text="Export",
            width=80,
            command=self._show_export_menu
        )
        export_btn.pack(side="left", padx=2)
        
        # Theme-Toggle
        theme_btn = ctk.CTkButton(
            menu_frame,
            text="Theme",
            width=80,
            command=self._toggle_theme
        )
        theme_btn.pack(side="right", padx=2)
    
    def _create_tab_bar(self, parent: ctk.CTkFrame) -> None:
        """
        Erstellt Tab-Leiste dynamisch
        
        Tabs:
        0: Dashboard (Vergleich)
        1-N: Varianten (nur für vorhandene)
        """
        self.tab_bar_frame = parent
        self._rebuild_tabs()
    
    def _rebuild_tabs(self) -> None:
        """Baut Tab-Leiste neu basierend auf vorhandenen Varianten"""
        # Alte Buttons entfernen
        for btn in self.tab_buttons:
            btn.destroy()
        self.tab_buttons.clear()
        
        # Dashboard-Tab (immer vorhanden)
        dashboard_btn = ctk.CTkButton(
            self.tab_bar_frame,
            text="Dashboard",
            width=120,
            command=lambda: self._switch_tab(0)
        )
        dashboard_btn.pack(side="left", padx=2, pady=5)
        self.tab_buttons.append(dashboard_btn)
        
        # Varianten-Tabs (nur für vorhandene Varianten)
        project = self.orchestrator.get_current_project()
        if project:
            for i, variant in enumerate(project.variants):
                btn = ctk.CTkButton(
                    self.tab_bar_frame,
                    text=variant.name,
                    width=120,
                    command=lambda idx=i: self._switch_tab(idx + 1)
                )
                btn.pack(side="left", padx=2, pady=5)
                self.tab_buttons.append(btn)
        
        # Tab-Styles aktualisieren
        self._update_tab_buttons()
    
    def _switch_tab(self, tab_index: int) -> None:
        """
        Wechselt zu anderem Tab
        
        Args:
            tab_index: 0=Dashboard, 1-5=Varianten
        """
        self.current_tab = tab_index
        self._update_tab_buttons()
        
        if tab_index == 0:
            self._show_dashboard()
        else:
            self._show_variant(tab_index - 1)
    
    def _update_tab_buttons(self) -> None:
        """Aktualisiert Tab-Button-Styles"""
        for i, btn in enumerate(self.tab_buttons):
            if i == self.current_tab:
                btn.configure(fg_color=("gray75", "gray30"))
            else:
                btn.configure(fg_color=("gray85", "gray20"))
    
    def _show_dashboard(self) -> None:
        """Zeigt Dashboard an"""
        # Content leeren
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Dashboard erstellen/anzeigen
        if not self.dashboard_view:
            self.dashboard_view = DashboardView(self.content_frame, self.orchestrator)
        else:
            self.dashboard_view = DashboardView(self.content_frame, self.orchestrator)
        
        self.dashboard_view.pack(fill="both", expand=True)
    
    def _show_variant(self, variant_index: int) -> None:
        """
        Zeigt Varianten-View an
        
        Args:
            variant_index: 0-4
        """
        # Content leeren
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Variante holen (NICHT automatisch erstellen)
        variant = self.orchestrator.get_variant(variant_index)
        
        if not variant:
            # Fehlermeldung anzeigen
            error_frame = ctk.CTkFrame(self.content_frame)
            error_frame.pack(fill="both", expand=True)
            
            ctk.CTkLabel(
                error_frame,
                text="Variante nicht gefunden",
                font=ctk.CTkFont(size=16)
            ).pack(pady=20)
            
            return
        
        # View erstellen
        view = VariantView(
            self.content_frame,
            self.orchestrator,
            variant_index
        )
        view.pack(fill="both", expand=True)
        
        self.variant_views[variant_index] = view
    
    def _show_file_menu(self) -> None:
        """Zeigt Datei-Menü"""
        # Vereinfacht: Buttons in Dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Datei")
        dialog.geometry("300x200")
        dialog.transient(self)
        
        ctk.CTkButton(
            dialog,
            text="Neues Projekt",
            command=lambda: [dialog.destroy(), self._new_project()]
        ).pack(pady=5, padx=20, fill="x")
        
        ctk.CTkButton(
            dialog,
            text="Projekt öffnen",
            command=lambda: [dialog.destroy(), self._open_project()]
        ).pack(pady=5, padx=20, fill="x")
        
        ctk.CTkButton(
            dialog,
            text="Projekt speichern",
            command=lambda: [dialog.destroy(), self._save_project()]
        ).pack(pady=5, padx=20, fill="x")
        
        ctk.CTkButton(
            dialog,
            text="Projekt speichern unter...",
            command=lambda: [dialog.destroy(), self._save_project_as()]
        ).pack(pady=5, padx=20, fill="x")
        
        ctk.CTkButton(
            dialog,
            text="Schließen",
            command=dialog.destroy
        ).pack(pady=20, padx=20, fill="x")
    
    def _show_export_menu(self) -> None:
        """Zeigt Export-Menü"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Export")
        dialog.geometry("300x150")
        dialog.transient(self)
        
        ctk.CTkButton(
            dialog,
            text="PDF-Report",
            command=lambda: [dialog.destroy(), self._export_pdf()]
        ).pack(pady=5, padx=20, fill="x")
        
        ctk.CTkButton(
            dialog,
            text="Schließen",
            command=dialog.destroy
        ).pack(pady=20, padx=20, fill="x")
    
    def _new_project(self) -> None:
        """Erstellt neues Projekt"""
        project = self.orchestrator.create_project("Neues Projekt")
        self.orchestrator.save_project()
        self._refresh_ui()
        messagebox.showinfo("Erfolg", "Neues Projekt erstellt")
    
    def _open_project(self) -> None:
        """Öffnet Projekt über Dateibrowser"""
        from pathlib import Path
        
        # Standard-Projektordner ermitteln
        default_dir = Path.home() / '.abc_co2_bilanzierer' / 'projects'
        
        filepath = filedialog.askopenfilename(
            title="Projekt öffnen",
            initialdir=str(default_dir) if default_dir.exists() else None,
            filetypes=[
                ("Projekt-Dateien", "*.json"),
                ("Alle Dateien", "*.*")
            ]
        )
        
        if filepath:
            # Projekt-ID aus Dateinamen extrahieren
            project_id = Path(filepath).stem
            
            if self.orchestrator.load_project(project_id):
                self._refresh_ui()
                messagebox.showinfo("Erfolg", f"Projekt geladen:\n{filepath}")
            else:
                messagebox.showerror("Fehler", "Fehler beim Laden des Projekts")
    
    def _save_project(self) -> None:
        """Speichert aktuelles Projekt"""
        if self.orchestrator.save_project():
            messagebox.showinfo("Erfolg", "Projekt gespeichert")
        else:
            messagebox.showerror("Fehler", "Fehler beim Speichern")
    
    def _save_project_as(self) -> None:
        """Speichert Projekt unter neuem Namen/Pfad"""
        from pathlib import Path
        
        project = self.orchestrator.get_current_project()
        if not project:
            messagebox.showerror("Fehler", "Kein Projekt geladen")
            return
        
        # Standard-Projektordner
        default_dir = Path.home() / '.abc_co2_bilanzierer' / 'projects'
        
        # Dateiname vorschlagen
        suggested_name = f"{project.name.replace(' ', '_')}.json"
        
        filepath = filedialog.asksaveasfilename(
            title="Projekt speichern unter",
            initialdir=str(default_dir) if default_dir.exists() else None,
            initialfile=suggested_name,
            defaultextension=".json",
            filetypes=[
                ("Projekt-Dateien", "*.json"),
                ("Alle Dateien", "*.*")
            ]
        )
        
        if filepath:
            # Speichere mit benutzerdefiniertem Pfad
            if self.orchestrator.save_project_as(filepath):
                messagebox.showinfo("Erfolg", f"Projekt gespeichert unter:\n{filepath}")
                self._refresh_ui()
            else:
                messagebox.showerror("Fehler", "Fehler beim Speichern")
    
    def _load_csv_dialog(self) -> None:
        """Öffnet Dateiauswahl für CSV"""
        filepath = filedialog.askopenfilename(
            title="CSV-Datenbank auswählen",
            filetypes=[
                ("CSV-Dateien", "*.csv"),
                ("Alle Dateien", "*.*")
            ]
        )
        
        if filepath:
            if self.orchestrator.load_csv(filepath):
                messagebox.showinfo("Erfolg", f"CSV geladen:\n{filepath}")
            else:
                messagebox.showerror("Fehler", "Fehler beim Laden der CSV")
    
    def _export_pdf(self) -> None:
        """Exportiert PDF"""
        filepath = filedialog.asksaveasfilename(
            title="PDF speichern",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")]
        )
        
        if filepath:
            # TODO: PDF-Export implementieren
            messagebox.showwarning(
                "Noch nicht verfügbar",
                "PDF-Export wird in zukünftiger Version implementiert"
            )
    
    def _toggle_theme(self) -> None:
        """Wechselt zwischen Dark/Light Mode"""
        current = ctk.get_appearance_mode()
        new_mode = "light" if current == "Dark" else "dark"
        ctk.set_appearance_mode(new_mode)
    
    def _on_boundary_changed(self, value: str) -> None:
        """Systemgrenze wurde geändert"""
        self.orchestrator.set_system_boundary(value)
        self.logger.info(f"Systemgrenze geändert: {value}")
        
        # Alle Ansichten aktualisieren
        if self.dashboard_view:
            self.dashboard_view.refresh()
        
        for view in self.variant_views:
            if view:
                view.refresh_chart()
    
    def _get_csv_info(self) -> str:
        """Gibt CSV-Info-String zurück"""
        from pathlib import Path
        metadata = self.orchestrator.get_csv_metadata()
        
        if metadata['path']:
            filename = Path(metadata['path']).name
            return f"📊 {filename} ({metadata['count']} Materialien)"
        
        return "Keine CSV geladen"
    
    def _refresh_ui(self) -> None:
        """Aktualisiert gesamte UI"""
        # Tabs neu bauen
        self._rebuild_tabs()
        
        if self.project_tree:
            self.project_tree.refresh()
        
        if self.current_tab == 0:
            self._show_dashboard()
        else:
            # Prüfen ob Variante noch existiert
            project = self.orchestrator.get_current_project()
            if project and self.current_tab - 1 < len(project.variants):
                self._show_variant(self.current_tab - 1)
            else:
                # Fallback auf Dashboard
                self._switch_tab(0)
    
    # ========================================================================
    # EVENT-HANDLER
    # ========================================================================
    
    def _on_project_loaded(self, project) -> None:
        """Callback: Projekt wurde geladen"""
        self.logger.info(f"Projekt geladen: {project.name}")
        self._refresh_ui()
    
    def _on_csv_loaded(self, metadata) -> None:
        """Callback: CSV wurde geladen"""
        self.logger.info(f"CSV geladen: {metadata['count']} Materialien")
    
    def _on_row_updated(self, variant_index: int, row_id: str) -> None:
        """Callback: Zeile wurde aktualisiert"""
        # View aktualisieren
        if self.current_tab == variant_index + 1:
            self._show_variant(variant_index)
        
        # Dashboard aktualisieren
        if self.dashboard_view:
            self.dashboard_view.refresh()
    
    def _on_rebuild_charts(self) -> None:
        """Callback: Diagramme neu zeichnen"""
        if self.current_tab == 0 and self.dashboard_view:
            self.dashboard_view.refresh()
        elif self.current_tab > 0:
            view = self.variant_views[self.current_tab - 1]
            if view:
                view.refresh_chart()
    
    def _on_autosave_failed(self) -> None:
        """Callback: Autosave fehlgeschlagen"""
        messagebox.showwarning(
            "Autosave fehlgeschlagen",
            "Das automatische Speichern ist fehlgeschlagen.\n"
            "Bitte prüfen Sie den Speicherort und die Berechtigungen."
        )
    
    def _on_variant_renamed(self, variant_index: int) -> None:
        """Callback: Varianten-Name wurde geändert"""
        # Tabs neu bauen um neuen Namen anzuzeigen
        self._rebuild_tabs()
        
        # Projekt-Tree aktualisieren
        if self.project_tree:
            self.project_tree.refresh()
    
    def _on_variant_deleted(self, remaining_count: int) -> None:
        """Callback: Variante wurde gelöscht"""
        # Tabs neu bauen
        self._rebuild_tabs()
        
        # Zurück zum Dashboard wenn aktuelle Variante gelöscht wurde
        if self.current_tab > remaining_count:
            self._switch_tab(0)
        
        # Dashboard aktualisieren
        if self.dashboard_view:
            self.dashboard_view.refresh()
    
    def _on_variant_added(self, new_count: int) -> None:
        """Callback: Variante wurde hinzugefügt"""
        # Tabs neu bauen
        self._rebuild_tabs()
        
        # Dashboard aktualisieren
        if self.dashboard_view:
            self.dashboard_view.refresh()
        
        # Zum neuen Tab wechseln
        self._switch_tab(new_count)
