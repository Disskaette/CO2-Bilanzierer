"""
Erweiterter Export-Dialog mit allen Optionen

Dialog für professionellen PDF-Export mit:
- Varianten-Auswahl (Checkboxen)
- Dashboard-Optionen (Chart, Table)
- Info-Blöcke (Methodik, Projektbeschreibung, etc.)
- Kommentar-Felder pro Variante
- Logo/Zusatzbild-Auswahl
- Excel-Export (unverändert)
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox, scrolledtext
import logging
from pathlib import Path

from services.pdf import PDFExporterPro, ExportConfig, InfoBlock, PREDEFINED_INFO_BLOCKS
from services.pdf.pdf_charts import PDFChartCreator
from services.excel_export import ExcelExporter
from models.project import Project

logger = logging.getLogger(__name__)


class ExportDialogPro(ctk.CTkToplevel):
    """Erweiterter Export-Dialog mit allen Optionen"""

    def __init__(self, parent, project: Project):
        super().__init__(parent)

        self.parent_window = parent  # Zugriff auf MainWindow
        self.project = project
        self.pdf_exporter = PDFExporterPro()
        self.excel_exporter = ExcelExporter()

        self.title("Export - Erweiterte Optionen")
        self.geometry("700x800")
        self.transient(parent)
        self.grab_set()

        # Variablen für Checkboxen und Eingabefelder
        self.variant_checkboxes = []
        # Speichert Kommentare als Strings (nicht Widgets!)
        self.variant_comments = {}
        self.info_block_checkboxes = {}

        self._build_ui()

    def _build_ui(self):
        """Erstellt UI"""

        # Scrollbarer Hauptcontainer
        main_frame = ctk.CTkScrollableFrame(self, width=660, height=760)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Titel
        title_label = ctk.CTkLabel(
            main_frame,
            text="Export-Optionen (Professionell)",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 20))

        # ====================================================================
        # PDF-OPTIONEN
        # ====================================================================

        pdf_frame = ctk.CTkFrame(main_frame)
        pdf_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            pdf_frame,
            text="PDF-Export",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=5, padx=10, anchor="w")

        # ===== DASHBOARD =====
        ctk.CTkLabel(
            pdf_frame,
            text="Dashboard:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(pady=(10, 5), padx=20, anchor="w")

        self.pdf_include_dashboard = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            pdf_frame,
            text="Dashboard einschließen",
            variable=self.pdf_include_dashboard
        ).pack(pady=2, padx=30, anchor="w")

        self.pdf_include_dashboard_chart = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            pdf_frame,
            text="Dashboard-Diagramm",
            variable=self.pdf_include_dashboard_chart
        ).pack(pady=2, padx=40, anchor="w")

        self.pdf_include_dashboard_table = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            pdf_frame,
            text="Dashboard-Tabelle",
            variable=self.pdf_include_dashboard_table
        ).pack(pady=2, padx=40, anchor="w")

        # ===== VARIANTEN =====
        ctk.CTkLabel(
            pdf_frame,
            text="Varianten einschließen:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(pady=(10, 5), padx=20, anchor="w")

        # Checkboxen für Varianten
        for i, variant in enumerate(self.project.variants):
            var = ctk.BooleanVar(value=True)
            cb = ctk.CTkCheckBox(
                pdf_frame,
                text=variant.name,
                variable=var
            )
            cb.pack(pady=2, padx=30, anchor="w")
            self.variant_checkboxes.append(var)

        # Diagramm/Tabelle-Optionen
        self.pdf_include_variant_charts = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            pdf_frame,
            text="Varianten-Diagramme",
            variable=self.pdf_include_variant_charts
        ).pack(pady=2, padx=40, anchor="w")

        self.pdf_include_variant_tables = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            pdf_frame,
            text="Varianten-Tabellen",
            variable=self.pdf_include_variant_tables
        ).pack(pady=2, padx=40, anchor="w")

        # ===== KOMMENTARE =====
        ctk.CTkLabel(
            pdf_frame,
            text="Kommentare (optional):",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(pady=(10, 5), padx=20, anchor="w")

        ctk.CTkLabel(
            pdf_frame,
            text="Kommentare werden unter der Varianten-Überschrift eingefügt:",
            font=ctk.CTkFont(size=9)
        ).pack(pady=2, padx=30, anchor="w")

        # Button zum Öffnen des Kommentar-Dialogs
        ctk.CTkButton(
            pdf_frame,
            text="Kommentare bearbeiten",
            command=self._show_comments_dialog,
            width=200
        ).pack(pady=5, padx=30, anchor="w")

        # ===== INFO-BLÖCKE =====
        ctk.CTkLabel(
            pdf_frame,
            text="Info-Blöcke:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(pady=(10, 5), padx=20, anchor="w")

        # Checkboxen für vordefinierte Info-Blöcke
        for block_id, info_block in PREDEFINED_INFO_BLOCKS.items():
            var = ctk.BooleanVar(value=False)
            cb = ctk.CTkCheckBox(
                pdf_frame,
                text=info_block.title,
                variable=var
            )
            cb.pack(pady=2, padx=30, anchor="w")
            self.info_block_checkboxes[block_id] = var

        # ===== LOGO & ZUSATZBILD =====
        ctk.CTkLabel(
            pdf_frame,
            text="Bilder:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(pady=(10, 5), padx=20, anchor="w")

        # Logo
        logo_frame = ctk.CTkFrame(pdf_frame)
        logo_frame.pack(fill="x", pady=5, padx=30)

        ctk.CTkLabel(
            logo_frame,
            text="Logo:",
            font=ctk.CTkFont(size=10)
        ).pack(side="left", padx=5)

        # Dropdown für Logo-Auswahl
        self.logo_options = [
            "Kein Logo",
            "Zimmerei Stark",
            "merz kley partner",
            "Hochschule Karlsruhe",
            "Eigenes Bild"
        ]
        self.logo_selection = ctk.StringVar(value="Kein Logo")
        self.logo_combo = ctk.CTkComboBox(
            logo_frame,
            variable=self.logo_selection,
            values=self.logo_options,
            width=300,
            command=self._on_logo_selection_changed
        )
        self.logo_combo.pack(side="left", padx=5)

        # Variable für den tatsächlichen Logo-Pfad
        self.logo_path_var = ctk.StringVar(value="")

        # Zusatzbild
        img_frame = ctk.CTkFrame(pdf_frame)
        img_frame.pack(fill="x", pady=5, padx=30)

        ctk.CTkLabel(
            img_frame,
            text="Zusatzbild:",
            font=ctk.CTkFont(size=10)
        ).pack(side="left", padx=5)

        self.image_path_var = ctk.StringVar(value="")
        self.image_entry = ctk.CTkEntry(
            img_frame,
            textvariable=self.image_path_var,
            width=300
        )
        self.image_entry.pack(side="left", padx=5)

        ctk.CTkButton(
            img_frame,
            text="...",
            width=40,
            command=self._select_image
        ).pack(side="left", padx=5)

        # PDF Export Button
        ctk.CTkButton(
            pdf_frame,
            text="Als PDF exportieren",
            command=self._export_pdf,
            fg_color="green",
            hover_color="darkgreen",
            height=40,
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(pady=15, padx=20, fill="x")

        # ====================================================================
        # EXCEL-OPTIONEN
        # ====================================================================

        excel_frame = ctk.CTkFrame(main_frame)
        excel_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            excel_frame,
            text="Excel-Export",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=5, padx=10, anchor="w")

        self.excel_include_charts = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            excel_frame,
            text="Diagramme einschließen (optional)",
            variable=self.excel_include_charts
        ).pack(pady=5, padx=20, anchor="w")

        ctk.CTkButton(
            excel_frame,
            text="Als Excel exportieren",
            command=self._export_excel,
            fg_color="green",
            hover_color="darkgreen",
            height=40,
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(pady=10, padx=20, fill="x")

        # ====================================================================
        # SCHLIESSEN
        # ====================================================================

        ctk.CTkButton(
            main_frame,
            text="Schließen",
            command=self.destroy
        ).pack(pady=20)

    def _show_comments_dialog(self):
        """Zeigt Dialog für Kommentare"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Kommentare bearbeiten")
        dialog.geometry("600x500")
        dialog.transient(self)
        dialog.grab_set()

        # Scrollbarer Container
        frame = ctk.CTkScrollableFrame(dialog, width=560, height=460)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            frame,
            text="Kommentare pro Variante",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(0, 10))

        # Temporäre Widget-Referenzen (nur für diesen Dialog)
        temp_text_widgets = {}

        # Kommentar-Felder für jede Variante
        for i, variant in enumerate(self.project.variants):
            var_frame = ctk.CTkFrame(frame)
            var_frame.pack(fill="x", pady=10)

            ctk.CTkLabel(
                var_frame,
                text=f"{variant.name}:",
                font=ctk.CTkFont(size=11, weight="bold")
            ).pack(anchor="w", padx=5, pady=2)

            # Textfeld
            text_widget = ctk.CTkTextbox(
                var_frame,
                height=60,
                width=520
            )
            text_widget.pack(padx=5, pady=2)

            # Vorhandenen Kommentar laden (aus String-Dictionary)
            if i in self.variant_comments:
                text_widget.insert("1.0", self.variant_comments[i])

            # Temporäre Referenz speichern
            temp_text_widgets[i] = text_widget

        # Funktion zum Speichern und Schließen
        def save_and_close():
            # Kommentare aus Widgets extrahieren und als Strings speichern
            for i, text_widget in temp_text_widgets.items():
                comment = text_widget.get("1.0", "end-1c").strip()
                if comment:
                    self.variant_comments[i] = comment
                elif i in self.variant_comments:
                    # Leeren Kommentar entfernen
                    del self.variant_comments[i]
            dialog.destroy()

        # Schließen-Button
        ctk.CTkButton(
            frame,
            text="Speichern & Schließen",
            command=save_and_close
        ).pack(pady=10)

    def _on_logo_selection_changed(self, selection):
        """Wird aufgerufen, wenn die Logo-Auswahl geändert wird"""
        if selection == "Eigenes Bild":
            self._select_custom_logo()
        elif selection == "Kein Logo":
            self.logo_path_var.set("")
        else:
            # Vordefiniertes Logo - Pfad setzen
            logo_dir = Path(__file__).parent.parent.parent / \
                "services" / "pdf" / "logos"
            if selection == "Zimmerei Stark":
                logo_path = logo_dir / "Zimmerei Stark.png"
            elif selection == "merz kley partner":
                logo_path = logo_dir / "merz kley partner.png"
            elif selection == "Hochschule Karlsruhe":
                logo_path = logo_dir / "Hochschule Karlsruhe.png"
            else:
                logo_path = None

            if logo_path and logo_path.exists():
                self.logo_path_var.set(str(logo_path))
            else:
                logger.warning(f"Logo-Datei nicht gefunden: {logo_path}")
                self.logo_path_var.set("")

    def _select_custom_logo(self):
        """Eigenes Logo-Datei auswählen"""
        filepath = filedialog.askopenfilename(
            title="Logo auswählen",
            filetypes=[
                ("Bilder", "*.png *.jpg *.jpeg *.gif *.svg"),
                ("Alle Dateien", "*.*")
            ]
        )
        if filepath:
            self.logo_path_var.set(filepath)
        else:
            # Wenn abgebrochen, zurück zu "Kein Logo"
            self.logo_selection.set("Kein Logo")
            self.logo_path_var.set("")

    def _select_image(self):
        """Zusatzbild auswählen"""
        filepath = filedialog.askopenfilename(
            title="Zusatzbild auswählen",
            filetypes=[
                ("Bilder", "*.png *.jpg *.jpeg *.gif"),
                ("Alle Dateien", "*.*")
            ]
        )
        if filepath:
            self.image_path_var.set(filepath)

    def _export_pdf(self):
        """PDF exportieren"""
        try:
            # Zieldatei wählen
            filepath = filedialog.asksaveasfilename(
                title="PDF speichern",
                defaultextension=".pdf",
                filetypes=[("PDF", "*.pdf")]
            )

            if not filepath:
                return

            # Konfiguration erstellen
            config = ExportConfig()

            # Logo
            config.logo_path = self.logo_path_var.get() if self.logo_path_var.get() else None
            if config.logo_path and not Path(config.logo_path).exists():
                config.logo_path = None

            # Dashboard
            config.include_dashboard = self.pdf_include_dashboard.get()
            config.include_dashboard_chart = self.pdf_include_dashboard_chart.get()
            config.include_dashboard_table = self.pdf_include_dashboard_table.get()

            # Varianten
            config.include_variants = [
                i for i, var in enumerate(self.variant_checkboxes) if var.get()
            ]
            config.include_variant_charts = self.pdf_include_variant_charts.get()
            config.include_variant_tables = self.pdf_include_variant_tables.get()

            # Kommentare (bereits als Strings gespeichert)
            config.comments = self.variant_comments.copy()

            # Info-Blöcke
            for block_id, var in self.info_block_checkboxes.items():
                if var.get():
                    info_block = PREDEFINED_INFO_BLOCKS[block_id].copy()
                    info_block.include = True
                    config.add_info_block(info_block)

            # Zusatzbild
            config.additional_image_path = self.image_path_var.get(
            ) if self.image_path_var.get() else None
            if config.additional_image_path and not Path(config.additional_image_path).exists():
                config.additional_image_path = None

            # Extrahiere bestehende Figuren aus Views (falls vorhanden)
            dashboard_figure = None
            variant_figures = {}

            logger.info("=== Starte Figure-Extraktion ===")
            logger.info(f"Parent-Window-Typ: {type(self.parent_window)}")
            logger.info(
                f"Hat dashboard_view: {hasattr(self.parent_window, 'dashboard_view')}")
            logger.info(
                f"Hat variant_views: {hasattr(self.parent_window, 'variant_views')}")

            try:
                # Dashboard-Figure holen
                if hasattr(self.parent_window, 'dashboard_view'):
                    dashboard_view = self.parent_window.dashboard_view
                    logger.info(f"Dashboard-View: {dashboard_view}")
                    if dashboard_view:
                        logger.info(
                            f"Dashboard-View hat figure: {hasattr(dashboard_view, 'figure')}")
                        if hasattr(dashboard_view, 'figure') and dashboard_view.figure:
                            dashboard_figure = dashboard_view.figure
                            logger.info(
                                "✓ Dashboard-Figure aus View extrahiert")
                        else:
                            logger.warning(
                                "Dashboard-View hat keine figure oder figure ist None")
                    else:
                        logger.warning("Dashboard-View ist None")

                # Varianten-Figures holen
                if hasattr(self.parent_window, 'variant_views'):
                    variant_views = self.parent_window.variant_views
                    logger.info(
                        f"Varianten-Views: {len(variant_views)} vorhanden")
                    logger.info(
                        f"Zu exportierende Varianten-Indizes: {config.include_variants}")

                    for idx in config.include_variants:
                        logger.info(
                            f"--- Versuche Variante {idx} zu extrahieren ---")
                        if idx < len(variant_views):
                            view = variant_views[idx]
                            logger.info(f"View {idx}: {view}")

                            # Falls View None ist, erstelle es jetzt (für Export)
                            if view is None and hasattr(self.parent_window, '_create_variant_view'):
                                logger.info(
                                    f"View {idx} ist None, erstelle es für Export...")
                                try:
                                    # Erstelle View temporär (wird beim nächsten Tab-Wechsel ersetzt)
                                    from ui.variants.variant_view import VariantView
                                    from core.orchestrator import AppOrchestrator

                                    # Hole Orchestrator
                                    orchestrator = self.parent_window.orchestrator

                                    # Erstelle temporäre View (nur für Export, wird nicht gespeichert)
                                    temp_view = VariantView(
                                        None, orchestrator, idx)

                                    # Hole Figure aus der temporären View
                                    if hasattr(temp_view, 'figure') and temp_view.figure:
                                        variant_figures[idx] = temp_view.figure
                                        logger.info(
                                            f"✓ Varianten-Figure {idx} ({self.project.variants[idx].name}) temporär erstellt")
                                    else:
                                        logger.warning(
                                            f"Temporäre View {idx} hat keine figure")

                                except Exception as e:
                                    logger.error(
                                        f"Fehler beim Erstellen der temporären View {idx}: {e}", exc_info=True)

                            elif view:
                                logger.info(
                                    f"View {idx} hat figure: {hasattr(view, 'figure')}")
                                if hasattr(view, 'figure') and view.figure:
                                    variant_figures[idx] = view.figure
                                    logger.info(
                                        f"✓ Varianten-Figure {idx} ({self.project.variants[idx].name}) aus View extrahiert")
                                else:
                                    logger.warning(
                                        f"View {idx} hat keine figure oder figure ist None")
                            else:
                                logger.warning(
                                    f"View {idx} ist None und konnte nicht erstellt werden")
                        else:
                            logger.warning(
                                f"Index {idx} außerhalb des View-Arrays ({len(variant_views)})")

                logger.info(
                    f"=== Extraktion abgeschlossen: Dashboard={dashboard_figure is not None}, Varianten={len(variant_figures)} ===")

            except Exception as e:
                logger.error(
                    f"Fehler beim Extrahieren der Figuren: {e}", exc_info=True)

            # Export mit bestehenden Figuren und Orchestrator
            orchestrator = self.parent_window.orchestrator if hasattr(self.parent_window, 'orchestrator') else None
            success = self.pdf_exporter.export(
                self.project,
                config,
                filepath,
                dashboard_figure=dashboard_figure,
                variant_figures=variant_figures,
                orchestrator=orchestrator
            )

            if success:
                # messagebox.showinfo(
                # "Erfolg", f"PDF erfolgreich exportiert:\n{filepath}")
                self.destroy()
            else:
                messagebox.showerror("Fehler", "Fehler beim PDF-Export")

        except Exception as e:
            logger.error(f"PDF-Export Fehler: {e}", exc_info=True)
            messagebox.showerror(
                "Fehler", f"Fehler beim PDF-Export:\n{str(e)}")

    def _export_excel(self):
        """Excel exportieren"""
        try:
            filepath = filedialog.asksaveasfilename(
                title="Excel speichern",
                defaultextension=".xlsx",
                filetypes=[("Excel", "*.xlsx")]
            )

            if not filepath:
                return

            success = self.excel_exporter.export(
                filepath=filepath,
                project=self.project,
                include_charts=self.excel_include_charts.get()
            )

            if success:
                messagebox.showinfo(
                    "Erfolg", f"Excel erfolgreich exportiert:\n{filepath}")
                self.destroy()
            else:
                messagebox.showerror("Fehler", "Fehler beim Excel-Export")

        except Exception as e:
            logger.error(f"Excel-Export Fehler: {e}", exc_info=True)
            messagebox.showerror(
                "Fehler", f"Fehler beim Excel-Export:\n{str(e)}")
