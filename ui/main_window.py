"""
Main-Window - Hauptfenster der Anwendung
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Optional
import logging
import sys
import os
import subprocess
from pathlib import Path

from core.orchestrator import AppOrchestrator
from ui.project_tree import ProjectTreeView
from ui.dashboard.dashboard_view import DashboardView
from ui.variants.variant_view import VariantView
from ui.dialogs.export_dialog_pro import ExportDialogPro

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
        self.title("CO₂-Bilanzierer")
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

        # Undo/Redo Buttons (für Enable/Disable)
        self.undo_btn: Optional[ctk.CTkButton] = None
        self.redo_btn: Optional[ctk.CTkButton] = None

        # Event-Registrierung
        self._register_orchestrator_events()

        self._build_ui()

        # Keyboard-Shortcuts für Undo/Redo
        self._bind_keyboard_shortcuts()

        # Handler für Fenster schließen (X-Button)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.logger.info("MainWindow initialisiert")

    def _register_orchestrator_events(self) -> None:
        """Registriert Callbacks beim Orchestrator"""
        self.orchestrator.state.register_callback(
            'project_loaded', self._on_project_loaded)
        self.orchestrator.state.register_callback(
            'csv_loaded', self._on_csv_loaded)
        self.orchestrator.state.register_callback(
            'row_added', self._on_row_added)
        self.orchestrator.state.register_callback(
            'row_updated', self._on_row_updated)
        self.orchestrator.state.register_callback(
            'row_deleted', self._on_row_deleted)
        self.orchestrator.state.register_callback(
            'rebuild_charts', self._on_rebuild_charts)
        self.orchestrator.state.register_callback(
            'autosave_failed', self._on_autosave_failed)
        self.orchestrator.state.register_callback(
            'variant_renamed', self._on_variant_renamed)
        self.orchestrator.state.register_callback(
            'variant_deleted', self._on_variant_deleted)
        self.orchestrator.state.register_callback(
            'variant_added', self._on_variant_added)
        self.orchestrator.state.register_callback(
            'project_renamed', self._on_project_renamed)
        self.orchestrator.state.register_callback(
            'visibility_changed', self._on_visibility_changed)
        self.orchestrator.state.register_callback(
            'undo_performed', self._on_undo_redo_performed)
        self.orchestrator.state.register_callback(
            'redo_performed', self._on_undo_redo_performed)

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

        # Erweiterte Systemgrenzen mit biogener Speicherung
        boundaries = [
            "A1-A3",
            "A1-A3 + C3 + C4",
            "A1-A3 + C3 + C4 + D",
            "A1-A3 (bio)",
            "A1-A3 + C3 + C4 (bio)",
            "A1-A3 + C3 + C4 + D (bio)"
        ]

        self.boundary_combo = ctk.CTkComboBox(
            boundary_bar,
            values=boundaries,
            width=250,
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
        menu_frame.pack_propagate(False)  # Verhindert Auto-Resize

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

        # Container für zentrierte Undo/Redo-Buttons
        center_frame = ctk.CTkFrame(menu_frame, fg_color="transparent")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Undo Button
        self.undo_btn = ctk.CTkButton(
            center_frame,
            text="↶ Undo",
            width=85,
            command=self._on_undo,
            state="disabled"
        )
        self.undo_btn.pack(side="left", padx=3)

        # Redo Button
        self.redo_btn = ctk.CTkButton(
            center_frame,
            text="↷ Redo",
            width=85,
            command=self._on_redo,
            state="disabled"
        )
        self.redo_btn.pack(side="left", padx=3)

        # Theme-Toggle
        theme_btn = ctk.CTkButton(
            menu_frame,
            text="Theme",
            width=80,
            command=self._toggle_theme
        )
        theme_btn.pack(side="right", padx=2)

        # Info-Button (links vom Theme)
        info_btn = ctk.CTkButton(
            menu_frame,
            text="ℹ️ Info",
            width=80,
            command=self._show_info_dialog
        )
        info_btn.pack(side="right", padx=2)

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
                # Aktiver Tab: deutlich sichtbar in beiden Modi
                btn.configure(
                    fg_color=("#3b8ed0", "gray30"),
                    text_color=("white", "white")
                )
            else:
                # Inaktiver Tab: kontrastreicher in Light Mode
                btn.configure(
                    fg_color=("#d0d0d0", "gray20"),
                    text_color=("black", "white")
                )

    def _show_dashboard(self) -> None:
        """Zeigt Dashboard an"""
        # Content leeren
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Dashboard erstellen/anzeigen
        if not self.dashboard_view:
            self.dashboard_view = DashboardView(
                self.content_frame, self.orchestrator)
        else:
            self.dashboard_view = DashboardView(
                self.content_frame, self.orchestrator)

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
        dialog.geometry("300x280")
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
        """Zeigt professionellen Export-Dialog"""
        project = self.orchestrator.get_current_project()
        if not project:
            messagebox.showwarning(
                "Kein Projekt", "Bitte erstellen oder laden Sie ein Projekt.")
            return

        ExportDialogPro(self, project)

    def _new_project(self) -> None:
        """Erstellt neues Projekt"""
        project = self.orchestrator.create_project("Neues Projekt")
        self.orchestrator.save_project()
        self._refresh_ui()
        messagebox.showinfo("Erfolg", "Neues Projekt erstellt")

    def _open_project(self) -> None:
        """Öffnet Projekt über Dialog mit zuletzt geöffneten Projekten"""
        from ui.dialogs.project_picker_dialog import ProjectPickerDialog

        # Zeige Dialog
        dialog = ProjectPickerDialog(self, self.orchestrator)
        self.wait_window(dialog)

        # Projekt ausgewählt?
        if dialog.selected_project_id:
            if self.orchestrator.load_project(dialog.selected_project_id):
                self._refresh_ui()
                messagebox.showinfo("Erfolg", "Projekt geladen")
            else:
                messagebox.showerror(
                    "Fehler", "Fehler beim Laden des Projekts")

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

        # Intelligentes Startverzeichnis bestimmen
        config = self.orchestrator.load_config()
        initial_dir = None

        # 1. Priorität: Zuletzt verwendetes Verzeichnis (Öffnen/Speichern)
        last_open_dir = config.get('last_open_directory')
        if last_open_dir:
            last_dir_path = Path(last_open_dir)
            if last_dir_path.exists() and last_dir_path.is_dir():
                initial_dir = str(last_dir_path)

        # 2. Priorität: Ordner des aktuellen Projekts (falls extern)
        if not initial_dir:
            external_paths = config.get('external_project_paths', {})
            if project.id in external_paths:
                current_path = Path(external_paths[project.id])
                if current_path.exists():
                    initial_dir = str(current_path.parent)

        # 3. Fallback: Benutzer-Home-Verzeichnis
        if not initial_dir:
            initial_dir = str(Path.home())

        # Dateiname vorschlagen
        suggested_name = f"{project.name.replace(' ', '_')}.json"

        filepath = filedialog.asksaveasfilename(
            title="Projekt speichern unter",
            initialdir=initial_dir,
            initialfile=suggested_name,
            defaultextension=".json",
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

            # Speichere mit benutzerdefiniertem Pfad
            if self.orchestrator.save_project_as(filepath):
                messagebox.showinfo(
                    "Erfolg", f"Projekt gespeichert unter:\n{filepath}")
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

    def _toggle_theme(self) -> None:
        """Wechselt zwischen Dark/Light Mode"""
        current = ctk.get_appearance_mode()
        new_mode = "light" if current == "Dark" else "dark"
        ctk.set_appearance_mode(new_mode)

        # Alle Views neu laden um Theme-Änderungen zu übernehmen
        if self.current_tab == 0:
            # Dashboard komplett neu laden
            self._show_dashboard()
        else:
            # Aktuelle Variante neu laden
            variant_index = self.current_tab - 1
            self._show_variant(variant_index)

    def _show_info_dialog(self) -> None:
        """Zeigt Info-Dialog mit Programm-Informationen"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Programm-Information")
        dialog.transient(self)
        dialog.grab_set()

        # Main Frame
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Titel
        title_label = ctk.CTkLabel(
            main_frame,
            text="CO₂-Bilanzierer",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 10))

        # Version
        version_label = ctk.CTkLabel(
            main_frame,
            text="Version 2.0",
            font=ctk.CTkFont(size=14)
        )
        version_label.pack(pady=(0, 20))

        # Normative Grundlagen
        norm_frame = ctk.CTkFrame(main_frame)
        norm_frame.pack(fill="x", pady=10)

        norm_title = ctk.CTkLabel(
            norm_frame,
            text="Normative Grundlagen:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        norm_title.pack(anchor="w", padx=10, pady=(10, 5))

        norms = [
            "• DIN EN 15804:2022-03 – Nachhaltigkeit von Bauwerken",
            "• ISO 21931-1:2022 – Nachhaltigkeit im Bauwesen",
            "• ISO 14040:2021 – Ökobilanz – Grundsätze und Rahmenbedingungen",
            "• ISO 14044:2021 – Ökobilanz – Anforderungen und Anleitungen"
        ]

        for norm in norms:
            norm_label = ctk.CTkLabel(
                norm_frame,
                text=norm,
                font=ctk.CTkFont(size=12),
                anchor="w"
            )
            norm_label.pack(anchor="w", padx=20, pady=2)

        norm_frame.pack_configure(pady=(0, 10))

        # Features
        features_frame = ctk.CTkFrame(main_frame)
        features_frame.pack(fill="x", pady=10)

        features_title = ctk.CTkLabel(
            features_frame,
            text="Hauptfunktionen:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        features_title.pack(anchor="w", padx=10, pady=(10, 5))

        features = [
            "• Vergleich von bis zu 5 Bauwerksvarianten",
            "• 6 Systemgrenzen (A1-A3, A+C, A+C+D, jeweils Standard & Bio)",
            "• Undo/Redo-System (max. 10 Schritte)",
            "• Flexible Projektverwaltung (intern & extern)",
            "• Autosave mit Snapshot-System",
            "• PDF-Export mit professionellem Layout"
        ]

        for feature in features:
            feature_label = ctk.CTkLabel(
                features_frame,
                text=feature,
                font=ctk.CTkFont(size=12),
                anchor="w"
            )
            feature_label.pack(anchor="w", padx=20, pady=2)

        features_frame.pack_configure(pady=(0, 10))

        # PDF-Button
        pdf_btn = ctk.CTkButton(
            main_frame,
            text="📖 Entwurfstafeln Ökobilanzierung öffnen",
            command=self._open_documentation_pdf,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        pdf_btn.pack(pady=20, fill="x", padx=20)

        # Schließen-Button
        close_btn = ctk.CTkButton(
            dialog,
            text="Schließen",
            command=dialog.destroy,
            width=120
        )
        close_btn.pack(pady=(0, 20))
        
        # Fenster auf Inhalt anpassen (nach dem Packen aller Widgets)
        dialog.update_idletasks()
        dialog.minsize(600, 100)

    def _open_documentation_pdf(self) -> None:
        """Öffnet die Bilanzierungsprozess-PDF"""
        try:
            # Pfad zur PDF-Datei ermitteln
            # Für .app: Ressourcen sind im Bundle
            # Für Entwicklung: Im data-Ordner
            if getattr(sys, 'frozen', False):
                # Läuft als .app (PyInstaller)
                base_path = sys._MEIPASS
            else:
                # Läuft als Skript
                base_path = Path(__file__).parent.parent

            pdf_path = Path(base_path) / "data" / \
                "ABC_Entwurfstafeln_Oekobilanzierung_2024-12.pdf"

            if not pdf_path.exists():
                messagebox.showerror(
                    "PDF nicht gefunden",
                    f"Die PDF-Datei wurde nicht gefunden:\n{pdf_path}"
                )
                return

            # PDF öffnen (plattformabhängig)
            if sys.platform == "darwin":  # macOS
                subprocess.run(["open", str(pdf_path)], check=True)
            elif sys.platform == "win32":  # Windows
                os.startfile(str(pdf_path))
            else:  # Linux
                subprocess.run(["xdg-open", str(pdf_path)], check=True)

            self.logger.info(f"PDF geöffnet: {pdf_path}")

        except Exception as e:
            self.logger.error(f"Fehler beim Öffnen der PDF: {e}")
            messagebox.showerror(
                "Fehler",
                f"Die PDF konnte nicht geöffnet werden:\n{str(e)}"
            )

    def _on_boundary_changed(self, value: str) -> None:
        """Systemgrenze wurde geändert"""
        self.orchestrator.set_system_boundary(value)
        self.logger.info(f"Systemgrenze geändert: {value}")

        # Alle Ansichten aktualisieren
        if self.current_tab == 0:
            # Dashboard komplett neu laden
            self._show_dashboard()
        else:
            # Aktuelle Variante neu laden
            variant_index = self.current_tab - 1
            self._show_variant(variant_index)

    def _get_csv_info(self) -> str:
        """Gibt CSV-Info-String zurück"""
        metadata = self.orchestrator.get_csv_metadata()

        if metadata['path']:
            filename = Path(metadata['path']).name
            return f"📊 {filename} ({metadata['count']} Materialien)"

        return "Keine CSV geladen"

    def _refresh_ui(self) -> None:
        """Aktualisiert gesamte UI"""
        # Tabs neu bauen
        self._rebuild_tabs()

        # Undo/Redo-Buttons aktualisieren
        self._update_undo_redo_buttons()

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

    def _on_row_added(self, variant_index: int, row_id: str) -> None:
        """Callback: Zeile wurde hinzugefügt"""
        # Undo/Redo-Buttons aktualisieren
        self._update_undo_redo_buttons()

        # ProjectTree aktualisieren (Zeilenanzahl)
        if self.project_tree:
            self.project_tree.refresh()

        # View aktualisieren
        if self.current_tab == variant_index + 1:
            self._show_variant(variant_index)

        # Dashboard aktualisieren
        if self.dashboard_view:
            self.dashboard_view.refresh()

    def _on_row_updated(self, variant_index: int, row_id: str) -> None:
        """Callback: Zeile wurde aktualisiert"""
        # Undo/Redo-Buttons aktualisieren
        self._update_undo_redo_buttons()

        # ProjectTree aktualisieren (falls Zeilenanzahl sich ändert)
        if self.project_tree:
            self.project_tree.refresh()

        # View aktualisieren
        if self.current_tab == variant_index + 1:
            self._show_variant(variant_index)

        # Dashboard aktualisieren
        if self.dashboard_view:
            self.dashboard_view.refresh()

    def _on_row_deleted(self, variant_index: int, row_id: str) -> None:
        """Callback: Zeile wurde gelöscht"""
        # Undo/Redo-Buttons aktualisieren
        self._update_undo_redo_buttons()

        # ProjectTree aktualisieren (Zeilenanzahl)
        if self.project_tree:
            self.project_tree.refresh()

        # Aktuelle Varianten-View komplett neu laden
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
            "Projekt konnte nicht automatisch gespeichert werden"
        )

    def _on_variant_renamed(self, variant_index: int, new_name: str) -> None:
        """Callback: Variante wurde umbenannt"""
        # Undo/Redo-Buttons aktualisieren
        self._update_undo_redo_buttons()

        # Tabs neu bauen
        self._rebuild_tabs()

    def _on_variant_deleted(self, remaining_count: int) -> None:
        """Callback: Variante wurde gelöscht"""
        # Undo/Redo-Buttons aktualisieren
        self._update_undo_redo_buttons()

        # Tabs neu bauen
        self._rebuild_tabs()

        # Intelligentes Tab-Handling
        if remaining_count == 0:
            # Keine Varianten mehr: Zum Dashboard
            self._switch_tab(0)
        elif self.current_tab == 0:
            # Bereits im Dashboard: Dashboard neu laden
            self._show_dashboard()
        elif self.current_tab > remaining_count:
            # Aktueller Tab existiert nicht mehr: Zum Dashboard
            self._switch_tab(0)
        else:
            # Tab existiert noch: View neu laden für aktuellen Tab
            self._show_variant(self.current_tab - 1)

    def _on_variant_added(self, new_count: int) -> None:
        """Callback: Variante wurde hinzugefügt"""
        # Undo/Redo-Buttons aktualisieren
        self._update_undo_redo_buttons()

        # Tabs neu bauen
        self._rebuild_tabs()

        # Dashboard aktualisieren
        if self.dashboard_view:
            self.dashboard_view.refresh()

        # Zum neuen Tab wechseln
        self._switch_tab(new_count)

    def _on_project_renamed(self, new_name: str) -> None:
        """Callback: Projektname wurde geändert"""
        # Undo/Redo-Buttons aktualisieren
        self._update_undo_redo_buttons()

        # ProjectTree aktualisieren
        if self.project_tree:
            self.project_tree.refresh()

    def _on_visibility_changed(self) -> None:
        """Callback: Varianten-Sichtbarkeit wurde geändert"""
        # Undo/Redo-Buttons aktualisieren
        self._update_undo_redo_buttons()

        # Dashboard komplett neu laden, wenn wir im Dashboard sind
        if self.current_tab == 0:
            self._show_dashboard()

    # ========================================================================
    # UNDO / REDO
    # ========================================================================

    def _bind_keyboard_shortcuts(self) -> None:
        """Bindet Keyboard-Shortcuts für Undo/Redo"""
        # Cmd+Z (Mac) / Ctrl+Z (Windows/Linux) für Undo
        if sys.platform == "darwin":
            # Mac
            self.bind("<Command-z>", lambda e: self._on_undo())
            self.bind("<Command-Z>", lambda e: self._on_undo())
            # Cmd+Shift+Z für Redo
            self.bind("<Command-Shift-z>", lambda e: self._on_redo())
            self.bind("<Command-Shift-Z>", lambda e: self._on_redo())
        else:
            # Windows/Linux
            self.bind("<Control-z>", lambda e: self._on_undo())
            self.bind("<Control-Z>", lambda e: self._on_undo())
            # Ctrl+Y oder Ctrl+Shift+Z für Redo
            self.bind("<Control-y>", lambda e: self._on_redo())
            self.bind("<Control-Y>", lambda e: self._on_redo())
            self.bind("<Control-Shift-z>", lambda e: self._on_redo())
            self.bind("<Control-Shift-Z>", lambda e: self._on_redo())

        self.logger.info("Keyboard-Shortcuts für Undo/Redo gebunden")

    def _on_undo(self) -> None:
        """Handler für Undo-Action"""
        try:
            success = self.orchestrator.perform_undo()
            if success:
                self.logger.info("✓ Undo durchgeführt")
                self._update_undo_redo_buttons()
            else:
                self.logger.debug("Undo nicht möglich (keine History)")
        except Exception as e:
            self.logger.error(f"Fehler beim Undo: {e}", exc_info=True)
            messagebox.showerror("Undo-Fehler", f"Fehler beim Undo:\n{str(e)}")

    def _on_redo(self) -> None:
        """Handler für Redo-Action"""
        try:
            success = self.orchestrator.perform_redo()
            if success:
                self.logger.info("✓ Redo durchgeführt")
                self._update_undo_redo_buttons()
            else:
                self.logger.debug("Redo nicht möglich (keine Redo-History)")
        except Exception as e:
            self.logger.error(f"Fehler beim Redo: {e}", exc_info=True)
            messagebox.showerror("Redo-Fehler", f"Fehler beim Redo:\n{str(e)}")

    def _update_undo_redo_buttons(self) -> None:
        """Aktualisiert den State der Undo/Redo-Buttons"""
        if self.undo_btn:
            if self.orchestrator.can_undo():
                self.undo_btn.configure(state="normal")
            else:
                self.undo_btn.configure(state="disabled")

        if self.redo_btn:
            if self.orchestrator.can_redo():
                self.redo_btn.configure(state="normal")
            else:
                self.redo_btn.configure(state="disabled")

    def _on_undo_redo_performed(self, *args, **kwargs) -> None:
        """Callback: Undo oder Redo wurde durchgeführt"""
        # Button-States aktualisieren
        self._update_undo_redo_buttons()

        # Tabs neu bauen (falls Varianten hinzugefügt/gelöscht wurden)
        self._rebuild_tabs()

        # Aktuelle Ansicht neu laden
        if self.current_tab == 0:
            self._show_dashboard()
        else:
            self._show_variant(self.current_tab - 1)

    # ========================================================================
    # FENSTER SCHLIESSEN
    # ========================================================================

    def _on_closing(self) -> None:
        """Handler für Fenster schließen (X-Button)"""
        try:
            # Projekt speichern
            if self.orchestrator and self.orchestrator.state.current_project:
                self.orchestrator.save_project()
                self.logger.info("Projekt vor Beenden gespeichert")

            # Konfiguration speichern
            if self.orchestrator:
                self.orchestrator.save_config()

            # Alle geplanten Callbacks abbrechen
            try:
                after_ids = self.tk.call('after', 'info')
                for after_id in after_ids:
                    try:
                        self.after_cancel(after_id)
                    except:
                        pass
            except:
                pass

            self.logger.info("Fenster wird geschlossen")
        except Exception as e:
            self.logger.error(f"Fehler beim Schließen: {e}")
        finally:
            # Mainloop beenden
            self.quit()

            # Fenster zerstören (kann TclError werfen, aber ist harmlos)
            try:
                self.destroy()
            except:
                pass  # Ignoriere Tcl-Fehler beim Cleanup

            # Prozess explizit beenden
            sys.exit(0)
