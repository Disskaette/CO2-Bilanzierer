"""
Variant-View - Ansicht für eine einzelne Bauwerksvariante (Tabs 2-6)
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
from typing import Optional
import logging

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from core.orchestrator import AppOrchestrator
from ui.dialogs.material_picker import MaterialPickerDialog

logger = logging.getLogger(__name__)


class VariantView(ctk.CTkFrame):
    """
    Varianten-Ansicht (Tabs 2-6)

    Zeigt:
    - Diagramm für diese Variante
    - Tabelle mit Materialzeilen
    - Buttons: Zeile hinzufügen/löschen, verschieben
    - Summenzeilen
    """

    def __init__(self, parent, orchestrator: AppOrchestrator, variant_index: int):
        super().__init__(parent)

        self.orchestrator = orchestrator
        self.variant_index = variant_index
        self.logger = logger

        # Chart
        self.figure: Optional[Figure] = None
        self.canvas: Optional[FigureCanvasTkAgg] = None

        self._build_ui()

    def _build_ui(self) -> None:
        """Erstellt UI"""

        variant = self.orchestrator.get_variant(self.variant_index)

        if not variant:
            no_data_label = ctk.CTkLabel(
                self,
                text="Variante nicht gefunden",
                font=ctk.CTkFont(size=14)
            )
            no_data_label.pack(pady=50)
            return

        # Header: Varianten-Name
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(
            header_frame,
            text="Varianten-Name:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=5)

        self.name_entry = ctk.CTkEntry(
            header_frame,
            font=ctk.CTkFont(size=14),
            width=300
        )
        self.name_entry.insert(0, variant.name)
        self.name_entry.pack(side="left", padx=5)
        self.name_entry.bind("<FocusOut>", self._on_name_changed)
        self.name_entry.bind("<Return>", self._on_name_changed)

        # Oberer Bereich: Diagramm
        chart_frame = ctk.CTkFrame(self, height=350)
        chart_frame.pack(fill="x", padx=10, pady=10)
        chart_frame.pack_propagate(False)

        self._create_chart(chart_frame, variant)

        # Mittlerer Bereich: Tabelle
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self._create_table(table_frame, variant)

        # Unterer Bereich: Buttons + Summen
        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.pack(fill="x", padx=10, pady=10)

        self._create_buttons(bottom_frame, variant)
        self._create_sums(bottom_frame, variant)

    def _create_chart(self, parent: ctk.CTkFrame, variant) -> None:
        """Erstellt kleines Diagramm für diese Variante"""

        # Theme-Farben
        is_dark = ctk.get_appearance_mode() == "Dark"
        fig_color = '#2b2b2b' if is_dark else 'white'

        # Kleineres, vertikales Diagramm
        self.figure = Figure(figsize=(8, 3.5), dpi=80, facecolor=fig_color)
        ax = self.figure.add_subplot(111)

        if is_dark:
            ax.set_facecolor('#2b2b2b')

        # Systemgrenze aus Projekt
        project = self.orchestrator.get_current_project()
        boundary = project.system_boundary if project else "A1-A3"

        # Daten sammeln
        labels = []
        values = []

        for row in variant.rows:
            if row.material_name:
                labels.append(row.material_name[:25])  # Kürzere Labels

                if boundary == "A1-A3":
                    values.append(row.result_a)
                elif boundary == "A1-A3+C3+C4":
                    values.append(row.result_ac)
                elif boundary == "A1-A3+C3+C4+D":
                    val = row.result_acd if row.result_acd is not None else row.result_ac
                    values.append(val)
                else:
                    values.append(row.result_a)

        if not values:
            text_color = 'lightgray' if is_dark else 'gray'
            ax.text(0.5, 0.5, "Keine Daten - Fügen Sie Materialien hinzu",
                    ha='center', va='center', color=text_color)
            ax.axis('off')
        else:
            # Gestapeltes Balkendiagramm (VERTIKAL - Balken nach oben)
            colors = plt.cm.tab20.colors

            bottom = 0
            for i, (label, value) in enumerate(zip(labels, values)):
                color = colors[i % len(colors)]
                ax.bar(
                    0,  # X-Position (eine Säule)
                    value,
                    bottom=bottom,
                    width=0.6,
                    color=color,
                    edgecolor='white',
                    label=label
                )
                bottom += value

            ax.set_ylabel("kg CO₂-Äq.", fontsize=10)
            ax.set_title(f"{variant.name} - {boundary}", fontsize=11, pad=10)
            ax.set_xticks([])
            ax.set_xlim(-0.5, 0.5)

            # Legende rechts neben dem Diagramm
            ax.legend(
                loc='center left',
                bbox_to_anchor=(1.02, 0.5),
                fontsize=12,
                framealpha=0.9
            )

            # Theme-Anpassung
            if is_dark:
                ax.tick_params(colors='white')
                ax.yaxis.label.set_color('white')
                ax.title.set_color('white')
                ax.spines['bottom'].set_color('white')
                ax.spines['left'].set_color('white')
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                legend = ax.get_legend()
                if legend:
                    legend.get_frame().set_facecolor('#2b2b2b')
                    legend.get_frame().set_edgecolor('gray')
                    for text in legend.get_texts():
                        text.set_color('white')

        # Mehr Platz für Legende
        self.figure.tight_layout(rect=[0, 0, 0.75, 1])

        self.canvas = FigureCanvasTkAgg(self.figure, parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def _create_table(self, parent: ctk.CTkFrame, variant) -> None:
        """Erstellt Tabelle mit Materialzeilen"""

        # Hinweis über Tabelle
        hint_label = ctk.CTkLabel(
            parent,
            text="Mengen bitte in der Einheit der CSV/EPD eingeben",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        hint_label.pack(anchor="w", padx=5, pady=(0, 5))

        # Treeview (Tabelle)
        columns = (
            "pos", "bezeichnung", "menge", "einheit",
            "gwp_a", "gwp_c3", "gwp_c4",
            "result_a", "result_ac"
        )

        self.tree = ttk.Treeview(
            parent,
            columns=columns,
            show="headings",
            height=10  # Weniger Zeilen
        )

        # Kleinere Zeilenhöhe
        style = ttk.Style()
        style.configure("Treeview", rowheight=20)

        # Spaltenüberschriften
        self.tree.heading("pos", text="Pos")
        self.tree.heading("bezeichnung", text="Bezeichnung")
        self.tree.heading("menge", text="Menge")
        self.tree.heading("einheit", text="Einheit")
        self.tree.heading("gwp_a", text="GWP A1-A3")
        self.tree.heading("gwp_c3", text="GWP C3")
        self.tree.heading("gwp_c4", text="GWP C4")
        self.tree.heading("result_a", text="Ergebnis A")
        self.tree.heading("result_ac", text="Ergebnis AC")

        # Spaltenbreiten
        self.tree.column("pos", width=50)
        self.tree.column("bezeichnung", width=250)
        self.tree.column("menge", width=80)
        self.tree.column("einheit", width=60)
        self.tree.column("gwp_a", width=90)
        self.tree.column("gwp_c3", width=80)
        self.tree.column("gwp_c4", width=80)
        self.tree.column("result_a", width=100)
        self.tree.column("result_ac", width=100)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Daten füllen
        self._populate_table(variant)

        # Doppelklick für Bearbeitung
        self.tree.bind("<Double-Button-1>", self._on_row_double_click)

    def _populate_table(self, variant) -> None:
        """Füllt Tabelle mit Daten"""

        # Alte Daten löschen
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Zeilen einfügen
        for row in variant.rows:
            values = (
                row.position + 1,
                row.material_name[:40] if row.material_name else "Nicht ausgewählt",
                f"{row.quantity:.2f}",
                row.material_unit,
                f"{row.material_gwp_a1a3:.3f}",
                f"{row.material_gwp_c3:.3f}",
                f"{row.material_gwp_c4:.3f}",
                f"{row.result_a:.2f}",
                f"{row.result_ac:.2f}"
            )

            item_id = self.tree.insert(
                "", "end", values=values, tags=(row.id,))

            # Warnung bei fehlenden Modulen
            if row.c_modules_missing:
                self.tree.item(item_id, tags=(row.id, "missing"))

    def _create_buttons(self, parent: ctk.CTkFrame, variant) -> None:
        """Erstellt Buttons"""

        btn_frame = ctk.CTkFrame(parent)
        btn_frame.pack(side="left", padx=10, pady=5)

        add_btn = ctk.CTkButton(
            btn_frame,
            text="+ Zeile hinzufügen",
            command=self._add_row
        )
        add_btn.pack(side="left", padx=2)

        del_btn = ctk.CTkButton(
            btn_frame,
            text="- Zeile löschen",
            command=self._delete_row,
            fg_color="darkred"
        )
        del_btn.pack(side="left", padx=2)

        up_btn = ctk.CTkButton(
            btn_frame,
            text="↑",
            width=40,
            command=self._move_row_up
        )
        up_btn.pack(side="left", padx=2)

        down_btn = ctk.CTkButton(
            btn_frame,
            text="↓",
            width=40,
            command=self._move_row_down
        )
        down_btn.pack(side="left", padx=2)

    def _create_sums(self, parent: ctk.CTkFrame, variant) -> None:
        """Erstellt Summenzeilen"""

        sum_frame = ctk.CTkFrame(parent)
        sum_frame.pack(side="right", padx=10, pady=5)

        sum_a_label = ctk.CTkLabel(
            sum_frame,
            text=f"Σ A1-A3: {variant.sum_a:.2f} kg CO₂-Äq.",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        sum_a_label.pack(side="left", padx=10)

        sum_ac_label = ctk.CTkLabel(
            sum_frame,
            text=f"Σ A1-A3+C3+C4: {variant.sum_ac:.2f} kg CO₂-Äq.",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        sum_ac_label.pack(side="left", padx=10)

    def refresh_chart(self) -> None:
        """Aktualisiert nur das Diagramm"""
        # Prüfen, ob Widget noch existiert
        try:
            if not self.winfo_exists():
                return
        except:
            return

        variant = self.orchestrator.get_variant(self.variant_index)
        if not variant:
            return

        try:
            if self.canvas and self.canvas.get_tk_widget().winfo_exists():
                self.canvas.get_tk_widget().destroy()
        except:
            pass

        try:
            if len(self.winfo_children()) > 0:
                chart_frame = self.winfo_children()[0]
                if chart_frame.winfo_exists():
                    self._create_chart(chart_frame, variant)
        except:
            pass

    # ========================================================================
    # EVENT-HANDLER
    # ========================================================================

    def _add_row(self) -> None:
        """Fügt neue Zeile hinzu"""
        row = self.orchestrator.add_material_row(self.variant_index)
        if row:
            # Material-Picker öffnen
            self._open_material_picker(row.id)

    def _delete_row(self) -> None:
        """Löscht ausgewählte Zeile"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning(
                "Keine Auswahl", "Bitte wählen Sie eine Zeile aus")
            return

        item = selection[0]
        tags = self.tree.item(item, "tags")
        if tags:
            row_id = tags[0]

            if messagebox.askyesno("Bestätigen", "Zeile wirklich löschen?"):
                self.orchestrator.delete_material_row(
                    self.variant_index, row_id)
                self._refresh_view()

    def _move_row_up(self) -> None:
        """Verschiebt Zeile nach oben"""
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        tags = self.tree.item(item, "tags")
        if tags:
            row_id = tags[0]
            self.orchestrator.move_row_up(self.variant_index, row_id)
            self._refresh_view()

    def _move_row_down(self) -> None:
        """Verschiebt Zeile nach unten"""
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        tags = self.tree.item(item, "tags")
        if tags:
            row_id = tags[0]
            self.orchestrator.move_row_down(self.variant_index, row_id)
            self._refresh_view()

    def _on_row_double_click(self, event) -> None:
        """Handler für Doppelklick auf Zeile"""
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        tags = self.tree.item(item, "tags")
        if tags:
            row_id = tags[0]

            # Welche Spalte wurde geklickt?
            region = self.tree.identify_region(event.x, event.y)
            if region == "cell":
                column = self.tree.identify_column(event.x)

                if column == "#3":  # Menge
                    self._edit_quantity(row_id)
                else:
                    # Material-Picker öffnen
                    self._open_material_picker(row_id)

    def _on_name_changed(self, event=None) -> None:
        """Varianten-Name wurde geändert"""
        variant = self.orchestrator.get_variant(self.variant_index)
        if variant and hasattr(self, 'name_entry'):
            new_name = self.name_entry.get().strip()
            if new_name and new_name != variant.name:
                variant.name = new_name
                self.orchestrator.notify_change()

                # Trigger Tab-Rebuild in MainWindow
                self.orchestrator.state.trigger(
                    'variant_renamed', self.variant_index)

    def _edit_quantity(self, row_id: str) -> None:
        """Inline-Bearbeitung der Menge (kein Dialog mehr)"""
        variant = self.orchestrator.get_variant(self.variant_index)
        if not variant:
            return

        row = next((r for r in variant.rows if r.id == row_id), None)
        if not row:
            return

        # Finde die Tree-Item-Zeile
        for item in self.tree.get_children():
            if self.tree.item(item, "tags")[0] == row_id:
                # Hole aktuelle Menge
                current_value = self.tree.item(item, "values")[2]

                # Erstelle Entry-Widget direkt in der Zelle
                bbox = self.tree.bbox(item, column="#3")
                if not bbox:
                    return

                x, y, width, height = bbox

                # Entry-Widget erstellen
                entry = ctk.CTkEntry(self.tree, width=width)
                entry.insert(0, current_value)
                entry.select_range(0, 'end')
                entry.focus()

                def save_quantity(event=None):
                    new_value = entry.get()
                    entry.destroy()

                    try:
                        quantity = float(new_value.replace(',', '.'))
                        self.orchestrator.update_material_row(
                            self.variant_index,
                            row_id,
                            quantity=quantity
                        )
                        self._refresh_view()
                    except ValueError:
                        messagebox.showerror("Fehler", "Ungültige Zahl")

                def cancel_edit(event=None):
                    entry.destroy()

                entry.bind("<Return>", save_quantity)
                entry.bind("<FocusOut>", save_quantity)
                entry.bind("<Escape>", cancel_edit)

                # Entry positionieren
                entry.place(x=x, y=y, width=width, height=height)
                break

    def _open_material_picker(self, row_id: str) -> None:
        """Öffnet Material-Picker-Dialog"""

        def on_material_selected(material):
            self.orchestrator.update_material_row(
                self.variant_index,
                row_id,
                material=material
            )
            self._refresh_view()

        MaterialPickerDialog(
            self,
            self.orchestrator,
            on_material_selected
        )

    def _refresh_view(self) -> None:
        """Aktualisiert komplette View"""
        # Prüfen, ob Widget noch existiert
        try:
            if not self.winfo_exists():
                return
        except:
            return

        variant = self.orchestrator.get_variant(self.variant_index)
        if not variant:
            return

        variant.calculate_sums()

        # Tabelle aktualisieren (nur wenn Tree noch existiert)
        try:
            if hasattr(self, 'tree') and self.tree.winfo_exists():
                self._populate_table(variant)
        except:
            pass

        # Chart aktualisieren
        try:
            self.refresh_chart()
        except:
            pass

        # Summen aktualisieren
        try:
            if len(self.winfo_children()) > 2:
                bottom_frame = self.winfo_children()[2]
                if bottom_frame.winfo_exists() and len(bottom_frame.winfo_children()) > 1:
                    sum_frame = bottom_frame.winfo_children()[1]
                    for widget in sum_frame.winfo_children():
                        widget.destroy()
                    self._create_sums(bottom_frame, variant)
        except:
            pass
