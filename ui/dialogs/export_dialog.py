"""
Export-Dialog für PDF und Excel Export
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import logging
from typing import Optional
from pathlib import Path

from services.pdf_export import PDFExporter
from services.excel_export import ExcelExporter
from models.project import Project

logger = logging.getLogger(__name__)


class ExportDialog(ctk.CTkToplevel):
    """Dialog für Export-Optionen"""

    def __init__(self, parent, project: Project):
        super().__init__(parent)

        self.project = project
        self.pdf_exporter = PDFExporter()
        self.excel_exporter = ExcelExporter()

        self.title("Export")
        self.geometry("500x600")
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        """Erstellt UI"""

        # Hauptcontainer
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Titel
        title_label = ctk.CTkLabel(
            main_frame,
            text="Export-Optionen",
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

        # Dashboard einschließen
        self.pdf_include_dashboard = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            pdf_frame,
            text="Dashboard-Vergleich einschließen",
            variable=self.pdf_include_dashboard
        ).pack(pady=5, padx=20, anchor="w")

        # Varianten auswählen
        ctk.CTkLabel(
            pdf_frame,
            text="Varianten einschließen:",
            font=ctk.CTkFont(size=11)
        ).pack(pady=(10, 5), padx=20, anchor="w")

        self.variant_checkboxes = []
        for i, variant in enumerate(self.project.variants):
            var = ctk.BooleanVar(value=True)
            cb = ctk.CTkCheckBox(
                pdf_frame,
                text=variant.name,
                variable=var
            )
            cb.pack(pady=2, padx=30, anchor="w")
            self.variant_checkboxes.append(var)

        # Logo auswählen
        logo_select_frame = ctk.CTkFrame(pdf_frame)
        logo_select_frame.pack(fill="x", pady=5, padx=20)

        ctk.CTkLabel(
            logo_select_frame,
            text="Logo (optional):",
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=5)

        self.logo_path_var = ctk.StringVar(value="")
        self.logo_entry = ctk.CTkEntry(
            logo_select_frame,
            textvariable=self.logo_path_var,
            width=200
        )
        self.logo_entry.pack(side="left", padx=5)

        ctk.CTkButton(
            logo_select_frame,
            text="Durchsuchen",
            width=100,
            command=self._select_logo
        ).pack(side="left", padx=5)

        # Zusatzbild auswählen
        img_select_frame = ctk.CTkFrame(pdf_frame)
        img_select_frame.pack(fill="x", pady=5, padx=20)

        ctk.CTkLabel(
            img_select_frame,
            text="Zusatzbild (optional):",
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=5)

        self.image_path_var = ctk.StringVar(value="")
        self.image_entry = ctk.CTkEntry(
            img_select_frame,
            textvariable=self.image_path_var,
            width=200
        )
        self.image_entry.pack(side="left", padx=5)

        ctk.CTkButton(
            img_select_frame,
            text="Durchsuchen",
            width=100,
            command=self._select_image
        ).pack(side="left", padx=5)

        # PDF Export Button
        ctk.CTkButton(
            pdf_frame,
            text="Als PDF exportieren",
            command=self._export_pdf,
            fg_color="green",
            hover_color="darkgreen"
        ).pack(pady=10, padx=20, fill="x")

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

        # Diagramme einschließen
        self.excel_include_charts = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            excel_frame,
            text="Diagramme einschließen (optional)",
            variable=self.excel_include_charts
        ).pack(pady=5, padx=20, anchor="w")

        # Excel Export Button
        ctk.CTkButton(
            excel_frame,
            text="Als Excel exportieren",
            command=self._export_excel,
            fg_color="green",
            hover_color="darkgreen"
        ).pack(pady=10, padx=20, fill="x")

        # ====================================================================
        # SCHLIESSEN
        # ====================================================================

        ctk.CTkButton(
            main_frame,
            text="Schließen",
            command=self.destroy
        ).pack(pady=20)

    def _select_logo(self):
        """Logo-Datei auswählen"""
        filepath = filedialog.askopenfilename(
            title="Logo auswählen",
            filetypes=[
                ("Bilder", "*.png *.jpg *.jpeg *.gif"),
                ("Alle Dateien", "*.*")
            ]
        )
        if filepath:
            self.logo_path_var.set(filepath)

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

            # Varianten sammeln
            include_variants = []
            for i, var in enumerate(self.variant_checkboxes):
                if var.get():
                    include_variants.append(i)

            # Logo-Pfad
            logo_path = self.logo_path_var.get() if self.logo_path_var.get() else None
            if logo_path and not Path(logo_path).exists():
                logo_path = None

            # Bild-Pfad
            image_path = self.image_path_var.get() if self.image_path_var.get() else None
            if image_path and not Path(image_path).exists():
                image_path = None

            # Export
            success = self.pdf_exporter.export(
                filepath=filepath,
                project=self.project,
                include_dashboard=self.pdf_include_dashboard.get(),
                include_variants=include_variants if include_variants else None,
                logo_path=logo_path,
                additional_image_path=image_path
            )

            if success:
                messagebox.showinfo("Erfolg", f"PDF erfolgreich exportiert:\n{filepath}")
                self.destroy()
            else:
                messagebox.showerror("Fehler", "Fehler beim PDF-Export")

        except Exception as e:
            logger.error(f"PDF-Export Fehler: {e}", exc_info=True)
            messagebox.showerror("Fehler", f"Fehler beim PDF-Export:\n{str(e)}")

    def _export_excel(self):
        """Excel exportieren"""
        try:
            # Zieldatei wählen
            filepath = filedialog.asksaveasfilename(
                title="Excel speichern",
                defaultextension=".xlsx",
                filetypes=[("Excel", "*.xlsx")]
            )

            if not filepath:
                return

            # Export
            success = self.excel_exporter.export(
                filepath=filepath,
                project=self.project,
                include_charts=self.excel_include_charts.get()
            )

            if success:
                messagebox.showinfo("Erfolg", f"Excel erfolgreich exportiert:\n{filepath}")
                self.destroy()
            else:
                messagebox.showerror("Fehler", "Fehler beim Excel-Export")

        except Exception as e:
            logger.error(f"Excel-Export Fehler: {e}", exc_info=True)
            messagebox.showerror("Fehler", f"Fehler beim Excel-Export:\n{str(e)}")
