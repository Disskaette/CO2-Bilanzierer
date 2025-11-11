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

        # Oberer Bereich: Diagramm (Ausgewogene Höhe)
        chart_frame = ctk.CTkFrame(self, height=350)
        chart_frame.pack(fill="x", padx=10, pady=10)
        chart_frame.pack_propagate(False)

        self._create_chart(chart_frame, variant)

        # Mittlerer Bereich: Tabelle (Theme-bewusst)
        # fg_color Format: (Light Mode Farbe, Dark Mode Farbe)
        table_frame = ctk.CTkFrame(self, fg_color=("white", "#2b2b2b"))
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

        # Ausgewogene Diagrammgröße
        self.figure = Figure(figsize=(8, 3.5), dpi=100, facecolor=fig_color)
        ax = self.figure.add_subplot(111)

        if is_dark:
            ax.set_facecolor('#2b2b2b')

        # Systemgrenze aus Projekt
        project = self.orchestrator.get_current_project()
        boundary = project.system_boundary if project else "A1-A3"
        
        # WICHTIG: Farben NICHT neu setzen, wenn bereits vom Dashboard gesetzt!
        # Das Dashboard setzt die Farben für ALLE sichtbaren Varianten.
        # Wenn wir hier neu setzen würden, würden wir nur die Materialien DIESER Variante verwenden
        # und damit andere Farben bekommen als im Dashboard!
        if not self.orchestrator.state.material_colors:
            # Nur wenn noch keine Farben gesetzt sind, setze sie jetzt
            self.orchestrator.update_material_colors([self.variant_index])

        # Daten sammeln - aggregiere doppelte Materialien
        material_values = {}

        for row in variant.rows:
            if row.material_name:
                # Wert abhängig von boundary bestimmen
                if boundary == "A1-A3":
                    value = row.result_a / 1000.0  # kg → t
                elif boundary == "A1-A3 + C3 + C4":
                    value = row.result_ac / 1000.0  # kg → t
                elif boundary == "A1-A3 + C3 + C4 + D":
                    val = row.result_acd if row.result_acd is not None else row.result_ac
                    value = val / 1000.0  # kg → t
                # Bio-korrigierte Varianten
                elif boundary == "A1-A3 (bio)":
                    val = row.result_a_bio if row.result_a_bio is not None else row.result_a
                    value = val / 1000.0  # kg → t
                elif boundary == "A1-A3 + C3 + C4 (bio)":
                    val = row.result_ac_bio if row.result_ac_bio is not None else row.result_ac
                    value = val / 1000.0  # kg → t
                elif boundary == "A1-A3 + C3 + C4 + D (bio)":
                    if row.result_acd_bio is not None:
                        val = row.result_acd_bio
                    elif row.result_acd is not None:
                        val = row.result_acd
                    else:
                        val = row.result_ac_bio if row.result_ac_bio is not None else row.result_ac
                    value = val / 1000.0  # kg → t
                else:
                    value = row.result_a / 1000.0  # kg → t

                # Addiere Werte wenn Material mehrfach vorkommt
                if row.material_name in material_values:
                    material_values[row.material_name] += value
                else:
                    material_values[row.material_name] = value

        # Erstelle Listen aus aggregierten Werten (ALPHABETISCH SORTIERT für konsistente Farben)
        sorted_items = sorted(material_values.items(), key=lambda x: x[0])
        labels = [item[0] for item in sorted_items]
        values = [item[1] for item in sorted_items]

        if not values:
            text_color = 'lightgray' if is_dark else 'gray'
            ax.text(0.5, 0.5, "Keine Daten - Fügen Sie Materialien hinzu",
                    ha='center', va='center', color=text_color)
            ax.axis('off')
        else:
            # Gestapeltes Balkendiagramm (VERTIKAL - positive oben, negative unten)
            bottom_positive = 0  # Für positive Werte (nach oben)
            bottom_negative = 0  # Für negative Werte (nach unten)

            for label, value in zip(labels, values):
                if value == 0:
                    continue  # Überspringe Nullwerte

                # Verwende zentrale Farbzuordnung
                color = self.orchestrator.get_material_color(label)

                if value > 0:
                    # Positive Werte von 0 nach oben stapeln
                    ax.bar(
                        0,  # X-Position (eine Säule)
                        value,
                        bottom=bottom_positive,
                        width=0.6,
                        color=color,
                        edgecolor='white'
                    )
                    bottom_positive += value
                else:
                    # Negative Werte von 0 nach unten stapeln
                    ax.bar(
                        0,  # X-Position (eine Säule)
                        value,
                        bottom=bottom_negative,
                        width=0.6,
                        color=color,
                        edgecolor='white'
                    )
                    bottom_negative += value

            # Tonnen statt kg
            ax.set_ylabel("CO2-Äquivalent [t]", fontsize=12, labelpad=10)
            ax.set_title(f"{variant.name} - {boundary}", fontsize=12, pad=15)
            ax.set_xticks([])
            ax.set_xlim(-0.5, 0.5)

            # Nulllinie prominent darstellen (wichtig für pos/neg Trennung)
            line_color = 'white' if is_dark else 'black'
            ax.axhline(y=0, color=line_color,
                       linewidth=1.5, alpha=0.7, zorder=3)
            ax.grid(axis='y', alpha=0.3)

            # Legende manuell erstellen (alphabetisch sortiert für Konsistenz)
            from matplotlib.patches import Rectangle
            legend_handles = []
            legend_labels = []
            for material_name in sorted(labels):
                color = self.orchestrator.get_material_color(material_name)
                patch = Rectangle((0, 0), 1, 1, fc=color, edgecolor='white')
                legend_handles.append(patch)
                legend_labels.append(material_name)
            
            # Legende rechts neben dem Diagramm - mit voller Breite
            legend = ax.legend(
                legend_handles,
                legend_labels,
                loc='center left',
                bbox_to_anchor=(1.02, 0.5),
                fontsize=10,
                framealpha=0.9,
                ncol=1  # Eine Spalte für volle Namen
            )

            # Theme-Anpassung
            if is_dark:
                ax.tick_params(colors='white')
                ax.yaxis.label.set_color('white')
                ax.title.set_color('white')
                # Nur X und Y Achsen anzeigen (schwarz/weiß je nach Theme)
                ax.spines['bottom'].set_color('white')
                ax.spines['left'].set_color('white')
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                if legend:
                    legend.get_frame().set_facecolor('#2b2b2b')
                    legend.get_frame().set_edgecolor('gray')
                    for text in legend.get_texts():
                        text.set_color('white')
            else:
                # Light Mode: Schwarze Achsen
                ax.tick_params(colors='black')
                ax.yaxis.label.set_color('black')
                ax.title.set_color('black')
                ax.spines['bottom'].set_color('black')
                ax.spines['left'].set_color('black')
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)

        # Festes Layout für konsistente Größe - Diagramm schmäler
        self.figure.subplots_adjust(
            left=0.1, right=0.35, top=0.88, bottom=0.05)

        self.canvas = FigureCanvasTkAgg(self.figure, parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def _create_table(self, parent: ctk.CTkFrame, variant) -> None:
        """Erstellt Tabelle mit Materialzeilen"""

        # Hinweis über Tabelle (Theme-bewusst)
        current_mode = ctk.get_appearance_mode()
        hint_label = ctk.CTkLabel(
            parent,
            text="Mengen bitte in der Einheit der CSV/EPD eingeben",
            font=ctk.CTkFont(size=11),
            text_color=("black", "white")  # Schwarz in Light, Weiß in Dark
        )
        hint_label.pack(anchor="w", padx=5, pady=(5, 5))

        # Treeview (Tabelle)
        columns = (
            "pos", "bezeichnung", "menge", "einheit",
            "gwp_a", "gwp_c3", "gwp_c4", "gwp_d",
            "result_a", "result_ac", "result_acd"
        )

        self.tree = ttk.Treeview(
            parent,
            columns=columns,
            show="headings",
            height=8  # Kompaktere Tabelle (scrollbar)
        )

        # Style konfigurieren (Theme-bewusst)
        style = ttk.Style()

        # Theme-Farben anpassen
        if current_mode == "Dark":
            # Dark Mode: Dunkle Tabelle
            style.theme_use('default')  # Wichtig: Theme zurücksetzen
            style.configure("Treeview",
                            background="#2b2b2b",
                            fieldbackground="#2b2b2b",
                            foreground="white",
                            rowheight=20,
                            borderwidth=0)
            style.configure("Treeview.Heading",
                            background="#1f1f1f",
                            foreground="white",
                            borderwidth=1,
                            relief="flat")
            style.map('Treeview',
                      background=[('selected', '#1f6aa5')],
                      foreground=[('selected', 'white')])
            style.map('Treeview.Heading',
                      background=[('active', '#2b2b2b')])
        else:
            # Light Mode: Helle Tabelle
            style.theme_use('default')
            style.configure("Treeview",
                            background="white",
                            fieldbackground="white",
                            foreground="black",
                            rowheight=20,
                            borderwidth=0)
            style.configure("Treeview.Heading",
                            background="#d0d0d0",
                            foreground="black",
                            borderwidth=1,
                            relief="flat")
            style.map('Treeview',
                      background=[('selected', '#3b8ed0')],
                      foreground=[('selected', 'white')])
            style.map('Treeview.Heading',
                      background=[('active', '#e0e0e0')])

        # Spaltenüberschriften
        self.tree.heading("pos", text="Pos")
        self.tree.heading("bezeichnung", text="Bezeichnung")
        self.tree.heading("menge", text="Menge")
        self.tree.heading("einheit", text="Einheit")
        self.tree.heading("gwp_a", text="GWP A1-A3")
        self.tree.heading("gwp_c3", text="GWP C3")
        self.tree.heading("gwp_c4", text="GWP C4")
        self.tree.heading("gwp_d", text="GWP D")
        self.tree.heading("result_a", text="Ergebnis A")
        self.tree.heading("result_ac", text="Ergebnis A+C")
        self.tree.heading("result_acd", text="Ergebnis A+C+D")

        # Spaltenbreiten (angepasst für GWP_D)
        self.tree.column("pos", width=10)        # Kleiner: 50→40
        self.tree.column("bezeichnung", width=250)
        self.tree.column("menge", width=60)
        self.tree.column("einheit", width=30)   # Kleiner: 60→50
        self.tree.column("gwp_a", width=60)     # Kleiner: 90→75
        self.tree.column("gwp_c3", width=60)    # Kleiner: 80→70
        self.tree.column("gwp_c4", width=60)    # Kleiner: 80→70
        self.tree.column("gwp_d", width=60)
        self.tree.column("result_a", width=60)
        self.tree.column("result_ac", width=60)
        self.tree.column("result_acd", width=60)

        # Scrollbar (Theme-bewusst)
        scrollbar = ttk.Scrollbar(
            parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Scrollbar-Style anpassen
        if current_mode == "Dark":
            style.configure("Vertical.TScrollbar",
                            background="#2b2b2b",
                            troughcolor="#1f1f1f",
                            bordercolor="#1f1f1f",
                            arrowcolor="white")
        else:
            style.configure("Vertical.TScrollbar",
                            background="#e0e0e0",
                            troughcolor="white",
                            bordercolor="#d0d0d0",
                            arrowcolor="black")

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
            # GWP_D und result_acd können None sein, dann "N/A" anzeigen
            gwp_d_display = f"{row.material_gwp_d:.2f}" if row.material_gwp_d is not None else "N/A"
            result_acd_display = f"{row.result_acd:.2f}" if row.result_acd is not None else "N/A"

            values = (
                row.position + 1,
                row.material_name[:40] if row.material_name else "Nicht ausgewählt",
                f"{row.quantity:.1f}",
                row.material_unit,
                f"{row.material_gwp_a1a3:.2f}",  # 2 Nachkommastellen
                f"{row.material_gwp_c3:.2f}",    # 2 Nachkommastellen
                f"{row.material_gwp_c4:.2f}",    # 2 Nachkommastellen
                gwp_d_display,                   # GWP_D mit 2 Nachkommastellen oder "N/A"
                f"{row.result_a:.2f}",
                f"{row.result_ac:.2f}",
                result_acd_display                # Result ACD mit 2 Nachkommastellen oder "N/A"
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
        """Erstellt Summenzeilen (Standard und bio-korrigiert)"""

        sum_frame = ctk.CTkFrame(parent)
        sum_frame.pack(side="right", padx=10, pady=5)

        # Standard-Deklaration (EN 15804+A2) - Schlanke Beschriftung
        sum_a_label = ctk.CTkLabel(
            sum_frame,
            text=f"Σ A: {variant.sum_a / 1000.0:.2f} t",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        sum_a_label.pack(side="left", padx=8)

        sum_ac_label = ctk.CTkLabel(
            sum_frame,
            text=f"Σ A+C: {variant.sum_ac / 1000.0:.2f} t",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        sum_ac_label.pack(side="left", padx=8)

        # ACD-Summe (falls vorhanden)
        if variant.sum_acd is not None:
            sum_acd_label = ctk.CTkLabel(
                sum_frame,
                text=f"Σ A+C+D: {variant.sum_acd / 1000.0:.2f} t",
                font=ctk.CTkFont(size=12, weight="bold")
            )
            sum_acd_label.pack(side="left", padx=8)

        # Bio-korrigierte Werte (falls vorhanden)
        if variant.sum_a_bio is not None:
            sum_a_bio_label = ctk.CTkLabel(
                sum_frame,
                text=f"Σ A (bio): {variant.sum_a_bio / 1000.0:.2f} t",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="lightgreen"
            )
            sum_a_bio_label.pack(side="left", padx=8)

        if variant.sum_ac_bio is not None:
            sum_ac_bio_label = ctk.CTkLabel(
                sum_frame,
                text=f"Σ A+C (bio): {variant.sum_ac_bio / 1000.0:.2f} t",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="lightgreen"
            )
            sum_ac_bio_label.pack(side="left", padx=8)

        if variant.sum_acd_bio is not None:
            sum_acd_bio_label = ctk.CTkLabel(
                sum_frame,
                text=f"Σ A+C+D (bio): {variant.sum_acd_bio / 1000.0:.2f} t",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="lightgreen"
            )
            sum_acd_bio_label.pack(side="left", padx=8)

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
            # Komplette Tabelle neu aufbauen
            variant = self.orchestrator.get_variant(self.variant_index)
            if variant:
                self._populate_table(variant)

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
            # Komplette Tabelle neu aufbauen
            variant = self.orchestrator.get_variant(self.variant_index)
            if variant:
                self._populate_table(variant)

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

                # Entry-Widget erstellen (width/height im Constructor!)
                entry = ctk.CTkEntry(self.tree, width=width, height=height)
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

                # Entry positionieren (OHNE width/height)
                entry.place(x=x, y=y)
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
