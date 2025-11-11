"""
Dashboard-View - Vergleichsansicht (Tab 1)
"""

import customtkinter as ctk
from tkinter import messagebox
from typing import Optional
import logging

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from tkinter import ttk

from core.orchestrator import AppOrchestrator

logger = logging.getLogger(__name__)


class DashboardView(ctk.CTkFrame):
    """
    Dashboard-Ansicht (Tab 1)

    Zeigt:
    - Projektüberschrift (editierbar)
    - Dropdown Systemgrenze
    - Gestapeltes Balkendiagramm (Variantenvergleich)
    - Checkboxen für Variantensichtbarkeit
    - CSV-Info
    """

    def __init__(self, parent, orchestrator: AppOrchestrator):
        super().__init__(parent)

        self.orchestrator = orchestrator
        self.logger = logger

        # Chart
        self.figure: Optional[Figure] = None
        self.canvas: Optional[FigureCanvasTkAgg] = None

        # Checkboxen
        self.visibility_vars: list[ctk.BooleanVar] = []

        self._build_ui()

    def _build_ui(self) -> None:
        """Erstellt UI"""

        # Header mit Projektname
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        # Label "Projektname:"
        project_label = ctk.CTkLabel(
            header_frame,
            text="Projektname:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        project_label.pack(side="left", padx=(10, 5), pady=5)

        project = self.orchestrator.get_current_project()
        project_name = project.name if project else "Kein Projekt"

        self.project_entry = ctk.CTkEntry(
            header_frame,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=40
        )
        self.project_entry.insert(0, project_name)
        self.project_entry.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=5)
        self.project_entry.bind("<FocusOut>", self._on_project_name_changed)
        self.project_entry.bind("<Return>", self._on_project_name_changed)
        self.project_entry.bind("<KeyRelease>", self._on_project_name_changed)

        # Unterer Bereich: Sichtbarkeits-Checkboxen
        vis_frame = ctk.CTkFrame(self)
        vis_frame.pack(side="bottom", fill="x", padx=10, pady=10)

        # Varianten-Label
        vis_label = ctk.CTkLabel(
            vis_frame,
            text="Angezeigte Varianten:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        vis_label.pack(side="left", padx=10)

        # Dynamische Checkboxen für vorhandene Varianten
        self._create_visibility_checkboxes(vis_frame)

        # Chart-Container (NACH Checkboxen erstellen, damit visibility_vars gesetzt sind)
        chart_frame = ctk.CTkFrame(self)
        chart_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self._create_chart(chart_frame)

    def _create_visibility_checkboxes(self, parent: ctk.CTkFrame) -> None:
        """Erstellt Checkboxen dynamisch für vorhandene Varianten"""
        # Alte Checkboxen entfernen
        self.visibility_vars.clear()
        for widget in parent.winfo_children():
            if isinstance(widget, ctk.CTkCheckBox):
                widget.destroy()

        # Neue Checkboxen für vorhandene Varianten erstellen
        project = self.orchestrator.get_current_project()
        if project:
            # Sicherstellen, dass visible_variants genug Einträge hat
            while len(project.visible_variants) < len(project.variants):
                project.visible_variants.append(True)

            for i, variant in enumerate(project.variants):
                # Wert aus project.visible_variants holen, nicht aus variant.visible
                is_visible = project.visible_variants[i] if i < len(
                    project.visible_variants) else True
                var = ctk.BooleanVar(value=is_visible)
                self.visibility_vars.append(var)

                cb = ctk.CTkCheckBox(
                    parent,
                    text=variant.name,
                    variable=var,
                    command=self._on_visibility_changed
                )
                cb.pack(side="left", padx=10)

    def _create_chart(self, parent: ctk.CTkFrame) -> None:
        """Erstellt Matplotlib-Chart mit Tabelle"""

        # Scrollable Container
        scrollable_frame = ctk.CTkScrollableFrame(parent)
        scrollable_frame.pack(fill="both", expand=True)

        # Container für Chart und Tabelle
        chart_container = ctk.CTkFrame(scrollable_frame)
        chart_container.pack(fill="both", expand=True)

        # Oberer Teil: Diagramm
        plot_frame = ctk.CTkFrame(chart_container)
        plot_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Figure erstellen mit Theme
        is_dark = ctk.get_appearance_mode() == "Dark"
        fig_color = '#2b2b2b' if is_dark else 'white'

        # Figure-Größe dynamisch anpassen (mehr Höhe bei vielen Materialien)
        project = self.orchestrator.get_current_project()
        num_materials = 0
        if project and project.variants:
            all_materials = set()
            for variant in project.variants:
                for row in variant.rows:
                    if row.material_name:
                        all_materials.add(row.material_name)
            num_materials = len(all_materials)

        # Höhe linear basierend auf Anzahl der Materialien
        # Formel: Basis + (Anzahl Materialien × Faktor)
        base_height = 4.0  # Basis-Höhe für wenige Materialien

        self.figure = Figure(figsize=(8, base_height),
                             dpi=100, facecolor=fig_color)
        ax = self.figure.add_subplot(111)

        if is_dark:
            ax.set_facecolor('#2b2b2b')

        # Daten holen
        project = self.orchestrator.get_current_project()

        if not project or not project.variants:
            text_color = 'lightgray' if is_dark else 'gray'
            ax.text(
                0.5, 0.5,
                "Keine Daten vorhanden\n\nErstellen Sie Varianten und fügen Sie Materialien hinzu.",
                ha='center', va='center',
                fontsize=14,
                color=text_color
            )
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
        else:
            self._plot_comparison(ax, project, is_dark)

            ax.set_ylabel('CO2-Äquivalent [t]', fontsize=14)
            ax.set_title('CO2-Bilanzierung - Variantenvergleich',
                         fontweight='bold', fontsize=15, pad=15)
        # Canvas erstellen
        self.canvas = FigureCanvasTkAgg(self.figure, plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Unterer Teil: Material-Tabelle
        if project and project.variants:
            self._create_material_table(chart_container, project)

    def _plot_comparison(self, ax, project, is_dark: bool = False) -> None:
        """
        Zeichnet Vergleichsdiagramm mit konsistenten Farben und Legende

        Args:
            ax: Matplotlib Axes
            project: Project-Objekt
            is_dark: Dark Mode aktiv
        """

        # 1. Sichtbare Varianten-Indices sammeln
        visible_indices = [
            i for i in range(len(project.variants))
            if i < len(self.visibility_vars) and self.visibility_vars[i].get()
        ]
        
        # 2. Zentrale Farbzuordnung aktualisieren
        self.orchestrator.update_material_colors(visible_indices)
        
        # 3. Alle Materialien über sichtbare Varianten sammeln (für num_materials)
        all_materials = set()
        for i in visible_indices:
            for row in project.variants[i].rows:
                if row.material_name:
                    all_materials.add(row.material_name)

        num_materials = len(all_materials)

        # 3. Varianten sammeln - nur tatsächlich vorhandene Materialien
        variant_names = []
        variant_data = []  # Liste von Dictionaries {material_name: value}

        for i, variant in enumerate(project.variants):
            # Nur sichtbare Varianten berücksichtigen
            if i < len(self.visibility_vars) and self.visibility_vars[i].get():
                variant_names.append(variant.name)
                # Materialwerte sammeln (nach Systemgrenze)
                material_values = {}
                for row in variant.rows:
                    if row.material_name:
                        val = self._get_value_for_boundary(
                            row, project.system_boundary)
                        # kg → t
                        # WICHTIG: Addiere Werte wenn Material mehrfach vorkommt
                        if row.material_name in material_values:
                            material_values[row.material_name] += val / 1000.0
                        else:
                            material_values[row.material_name] = val / 1000.0

                variant_data.append(material_values)

        if not variant_names:
            ax.text(
                0.5, 0.5,
                "Keine Varianten sichtbar",
                ha='center', va='center',
                fontsize=14,
                color='gray'
            )
            ax.axis('off')
            return

        # 4. Gestapeltes Balkendiagramm mit konsistenten Farben
        x_pos = range(len(variant_names))

        # Für jede Variante: Iteriere durch ALLE Materialien (sortiert) für Konsistenz
        for idx, (name, material_values) in enumerate(zip(variant_names, variant_data)):
            bottom_positive = 0  # Für positive Werte
            bottom_negative = 0  # Für negative Werte
            # WICHTIG: Iteriere durch ALLE Materialien in sortierter Reihenfolge
            for material_name in sorted(all_materials):
                # Hole Wert (0 wenn nicht vorhanden)
                value = material_values.get(material_name, 0.0)
                if value != 0:  # Zeichne positive UND negative Werte
                    color = self.orchestrator.get_material_color(material_name)
                    if value > 0:
                        # Positive Werte von unten nach oben stapeln
                        ax.bar(
                            idx,
                            value,
                            bottom=bottom_positive,
                            color=color,
                            edgecolor='white',
                            linewidth=0.5,
                            width=0.6
                        )
                        bottom_positive += value
                    else:
                        # Negative Werte von oben nach unten stapeln
                        ax.bar(
                            idx,
                            value,
                            bottom=bottom_negative,
                            color=color,
                            edgecolor='white',
                            linewidth=0.5,
                            width=0.6
                        )
                        bottom_negative += value

        # 5. Achsenbeschriftung mit dynamischer Rotation
        ax.set_xticks(x_pos)
        # Rotation abhängig von Anzahl und Länge der Labels
        max_label_length = max(len(name)
                               for name in variant_names) if variant_names else 0
        num_variants = len(variant_names)

        # Rotation nur wenn nötig (viele oder lange Namen)
        if num_variants > 3 or max_label_length > 12:
            rotation = 45
            ha = 'right'
        else:
            rotation = 0
            ha = 'center'

        ax.set_xticklabels(variant_names, fontsize=12,
                           rotation=rotation, ha=ha)
        ax.set_ylabel("CO2-Äquivalent [t]", fontsize=12, labelpad=8)
        ax.set_title(
            f"Variantenvergleich - {project.system_boundary}", fontsize=12, pad=25)

        # Y-Achse muss 0 enthalten und beide Bereiche (positiv/negativ) zeigen
        # Nulllinie prominent darstellen (Theme-bewusst)
        line_color = 'white' if is_dark else 'black'
        ax.axhline(y=0, color=line_color, linewidth=1.5, alpha=0.7, zorder=3)
        ax.grid(axis='y', alpha=0.3)

        # 6. Legende VERTIKAL rechts neben dem Diagramm (zentriert)
        if all_materials:
            from matplotlib.patches import Rectangle

            # Erstelle Patches für alle Materialien (sortiert)
            legend_handles = []
            legend_labels = []
            for material_name in sorted(all_materials):
                color = self.orchestrator.get_material_color(material_name)
                patch = Rectangle((0, 0), 1, 1, fc=color, edgecolor='white')
                legend_handles.append(patch)
                # Kürze zu lange Namen für bessere Lesbarkeit
                display_name = material_name if len(
                    material_name) <= 50 else material_name[:47] + "..."
                legend_labels.append(display_name)

            # Legende vertikal (ncol=1) rechts, vertikal zentriert
            legend = ax.legend(
                legend_handles,
                legend_labels,
                loc='center left',  # Legende links ausgerichtet an bbox_to_anchor
                # Rechts vom Diagramm, vertikal zentriert
                bbox_to_anchor=(1.05, 0.5),
                fontsize=9,
                framealpha=0.9,
                ncol=1,  # Immer vertikal (1 Spalte)
                bbox_transform=ax.transAxes
            )

        # 7. Theme anpassen
        is_dark = ctk.get_appearance_mode() == "Dark"
        if is_dark:
            ax.set_facecolor('#2b2b2b')
            self.figure.patch.set_facecolor('#2b2b2b')
            ax.tick_params(colors='white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
            ax.title.set_color('white')
            ax.spines['bottom'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            # Legende anpassen
            legend = ax.get_legend()
            if legend:
                legend.get_frame().set_facecolor('#2b2b2b')
                legend.get_frame().set_edgecolor('gray')
                for text in legend.get_texts():
                    text.set_color('white')
        else:
            ax.spines['bottom'].set_color('black')
            ax.spines['left'].set_color('black')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

        # 8. Layout anpassen: Achse + Legende möglichst mittig zentrieren

        # 8.1 Rechts Platz für die Legende
        right_margin = 0.6  # 0.60 wäre für die Achse sehr schmal

        # 8.2 Bottom-Margin: dynamisch basierend auf Rotation und Namenslänge
        rotated = max_label_length > 12  # or num_variants > 3

        if rotated:
            base_margin = 0.05        # Grundabstand
            char_factor = 0.013      # zusätzlicher Abstand pro Zeichen
            bottom_min = base_margin + (max_label_length * char_factor)
            bottom_min = min(max(bottom_min, 0.15), 0.35)
            height_per_material = 0.08
        else:
            bottom_min = 0.12
            height_per_material = 0.051

        # 8.3 Referenz-Diagrammhöhe (in "physisch" gedacht)
        base_fig_height = 5.5        # Referenz-Figurehöhe in Zoll
        base_axis_rel = 0.65         # 70 % der Figure für das Diagramm
        base_axis_height_inch = base_axis_rel * base_fig_height

        # 8.4 Figurehöhe dynamisch abhängig von Materialien (für lange Legende)
        threshold = 20               # ab hier typischerweise viele Legendeneinträge
        # Zusatzhöhe pro Material über threshold (Zoll)
        max_fig_height = 10.0        # harte Obergrenze

        extra_materials = max(0, num_materials - threshold)
        extra_height = extra_materials * height_per_material

        fig_height = min(base_fig_height + extra_height, max_fig_height)

        # Figure-Höhe setzen
        w_in, _ = self.figure.get_size_inches()
        self.figure.set_size_inches(w_in, fig_height, forward=True)

        # 8.5 relative Achsenhöhe so wählen, dass physische Höhe ~ konstant bleibt
        axis_rel = base_axis_height_inch / \
            fig_height  # (Zoll / Zoll) = Anteil 0..1

        # 8.6 Ideale Zentrierung: Achsenmitte bei 0.5 der Figure
        center = 0.5
        bottom = center - axis_rel / 2
        top = center + axis_rel / 2

        # 8.7 Unten genug Platz für Labels erzwingen
        if bottom < bottom_min:
            bottom = bottom_min
            top = bottom + axis_rel

        # 8.8 Oben nicht über den Rand hinaus
        if top > 0.98:
            top = 0.98
            axis_rel = top - bottom  # Achse wird dann minimal kleiner
            # neue Mitte ergibt sich automatisch aus (bottom + top) / 2

        # 8.9 Layout anwenden
        self.figure.subplots_adjust(
            left=0.10,
            right=right_margin,
            top=top,
            bottom=bottom
        )

    def _create_material_table(self, parent: ctk.CTkFrame, project) -> None:
        """Erstellt Material-Übersichtstabellen im Grid-Layout pro Variante"""

        # Titel
        title_label = ctk.CTkLabel(
            parent,
            text="Material-Übersicht pro Variante",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        title_label.pack(anchor="w", padx=5, pady=(5, 5))

        # Grid-Container (2 Spalten)
        grid_frame = ctk.CTkFrame(parent)
        grid_frame.pack(fill="x", padx=5, pady=(0, 5))

        # Nur sichtbare Varianten anzeigen
        visible_variants = []
        for i, variant in enumerate(project.variants):
            if i < len(self.visibility_vars) and self.visibility_vars[i].get():
                visible_variants.append(variant)

        if not visible_variants:
            return

        total_font = ctk.CTkFont(weight="bold")

        # Gruppe 0: Varianten 0 & 1, Gruppe 1: 2 & 3, ...
        group_count = (len(visible_variants) + 1) // 2
        group_max_rows = []
        for g in range(group_count):
            i0 = 2 * g
            i1 = 2 * g + 1

            len0 = len(visible_variants[i0].rows)
            if i1 < len(visible_variants):
                len1 = len(visible_variants[i1].rows)
                group_max_rows.append(max(len0, len1))
            else:
                # Letzte einzelne Variante
                group_max_rows.append(len0)
            # Style
            style = ttk.Style()
            current_mode = ctk.get_appearance_mode()

        if current_mode == "Dark":
            style.theme_use('default')
            style.configure("Treeview",
                            background="#2b2b2b",
                            fieldbackground="#2b2b2b",
                            foreground="white",
                            rowheight=20)
            style.configure("Treeview.Heading",
                            background="#1f1f1f",
                            foreground="white",
                            relief="flat")
        else:
            style.theme_use('default')
            style.configure("Treeview",
                            background="white",
                            fieldbackground="white",
                            foreground="black",
                            rowheight=20)
            style.configure("Treeview.Heading",
                            background="#d0d0d0",
                            foreground="black",
                            relief="flat")

        # Grid erstellen: 2 Spalten
        for idx, variant in enumerate(visible_variants):
            row_grid = idx // 2
            col_grid = idx % 2

            # Welche Gruppe
            group_index = row_grid
            pair_max_rows = group_max_rows[group_index]
            # Varianten-Frame
            variant_frame = ctk.CTkFrame(
                grid_frame, fg_color=("white", "#2b2b2b"))
            variant_frame.grid(row=row_grid, column=col_grid, padx=5,
                               pady=5, sticky="nsew")

            # Grid-Gewichte
            grid_frame.grid_columnconfigure(col_grid, weight=1)

            # Varianten-Titel (größere Schrift)
            var_title = ctk.CTkLabel(
                variant_frame,
                text=variant.name,
                font=ctk.CTkFont(size=13, weight="bold")
            )
            var_title.pack(anchor="w", padx=5, pady=(5, 2))

            # Mini-Treeview - dynamische Höhe basierend auf Materialanzahl
            columns = ("material", "co2")
            row_count = len(variant.rows)
            # Mindestens 3, maximal 20 Zeilen + 1 für Summe
            dynamic_height = min(max(row_count + 1, 3), 20)
            tree = ttk.Treeview(
                variant_frame,
                columns=columns,
                show="headings",
                height=dynamic_height
            )

            # Spalten - optimierte Breiten
            tree.heading("material", text="Material", anchor="w")
            tree.heading("co2", text="CO₂ [t]", anchor="center")
            tree.column("material", width=385, anchor="w")  # Breiter für Namen
            # Schmäler für Zahlen
            tree.column("co2", width=35, anchor="center")

            # Daten für diese Variante
            variant_total = 0
            for row in variant.rows:
                if row.material_name:
                    val = self._get_value_for_boundary(
                        row, project.system_boundary)
                    val_tons = val / 1000.0  # kg → t
                    tree.insert("", "end", values=(
                        row.material_name,  # Voller Name, kein Kürzen
                        f"{val_tons:.2f}"
                    ))
                    variant_total += val_tons
            padding_rows = pair_max_rows - row_count
            for _ in range(padding_rows):
                tree.insert("", "end", values=("", ""))

            # Summe
            tree.insert("", "end", values=(
                "SUMME",
                f"{variant_total:.2f}"
            ), tags=("total",))
            tree.tag_configure(
                "total", background="#4a4a4a" if current_mode == "Dark" else "#e0e0e0", font=total_font)

            tree.pack(fill="both", expand=True, padx=5, pady=(0, 5))

    def _get_value_for_boundary(self, row, boundary: str) -> float:
        """Gibt Wert für Systemgrenze zurück (Standard oder bio-korrigiert)"""
        # Standard-Deklaration (EN 15804+A2)
        if boundary == "A1-A3":
            return row.result_a
        elif boundary == "A1-A3 + C3 + C4":
            return row.result_ac
        elif boundary == "A1-A3 + C3 + C4 + D":
            return row.result_acd if row.result_acd is not None else row.result_ac
        # Bio-korrigierte Varianten
        elif boundary == "A1-A3 (bio)":
            return row.result_a_bio if row.result_a_bio is not None else row.result_a
        elif boundary == "A1-A3 + C3 + C4 (bio)":
            return row.result_ac_bio if row.result_ac_bio is not None else row.result_ac
        elif boundary == "A1-A3 + C3 + C4 + D (bio)":
            if row.result_acd_bio is not None:
                return row.result_acd_bio
            elif row.result_acd is not None:
                return row.result_acd
            else:
                return row.result_ac_bio if row.result_ac_bio is not None else row.result_ac
        # Fallback
        return row.result_a

    def refresh(self) -> None:
        """Aktualisiert Dashboard"""
        # Prüfen, ob Widget noch existiert
        try:
            if not self.winfo_exists():
                return
        except:
            return

        children = self.winfo_children()

        # Checkboxen aktualisieren (letztes Kind-Widget: vis_frame mit side=bottom)
        try:
            if len(children) > 1:
                vis_frame = children[-1]  # Letztes Element (side=bottom)
                self._create_visibility_checkboxes(vis_frame)
        except:
            pass

        # Chart neu zeichnen (vorletztes Kind-Widget: chart_frame)
        try:
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
                self.canvas = None
        except:
            pass

        try:
            if len(children) > 1:
                chart_frame = children[-2]  # Vorletztes Element
                self._create_chart(chart_frame)
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren des Dashboards: {e}")

    # ========================================================================
    # EVENT-HANDLER
    # ========================================================================

    def _on_project_name_changed(self, event=None) -> None:
        """Projektname wurde geändert"""
        new_name = self.project_entry.get().strip()
        if new_name:
            # Über Orchestrator umbenennen (mit Undo-Support)
            self.orchestrator.rename_project(new_name)

    def _on_visibility_changed(self) -> None:
        """Varianten-Sichtbarkeit wurde geändert"""
        for i, var in enumerate(self.visibility_vars):
            self.orchestrator.set_variant_visibility(i, var.get())

        # Dashboard wird über visibility_changed Event neu geladen
        # (kein self.refresh() mehr nötig)
