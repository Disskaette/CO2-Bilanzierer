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
        
        project = self.orchestrator.get_current_project()
        project_name = project.name if project else "Kein Projekt"
        
        self.project_entry = ctk.CTkEntry(
            header_frame,
            font=ctk.CTkFont(size=18, weight="bold"),
            height=40
        )
        self.project_entry.insert(0, project_name)
        self.project_entry.pack(fill="x", padx=5, pady=5)
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
                is_visible = project.visible_variants[i] if i < len(project.visible_variants) else True
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
        
        # Kleinere Figure für Platz für Legenden
        self.figure = Figure(figsize=(10, 4), dpi=100, facecolor=fig_color)
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
            self._plot_comparison(ax, project)
        
        # Canvas erstellen
        self.canvas = FigureCanvasTkAgg(self.figure, plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Unterer Teil: Material-Tabelle
        if project and project.variants:
            self._create_material_table(chart_container, project)
    
    def _plot_comparison(self, ax, project) -> None:
        """
        Zeichnet Vergleichsdiagramm mit konsistenten Farben und Legende
        
        Args:
            ax: Matplotlib Axes
            project: Project-Objekt
        """
        
        # 1. Alle Materialien über alle Varianten sammeln
        all_materials = set()
        for variant in project.variants:
            for row in variant.rows:
                if row.material_name:
                    all_materials.add(row.material_name)
        
        # 2. Farben zuweisen (konsistent über alle Varianten)
        material_colors = {}
        colors = plt.cm.tab20.colors
        for idx, material in enumerate(sorted(all_materials)):
            material_colors[material] = colors[idx % len(colors)]
        
        # 3. Varianten sammeln
        variant_names = []
        variant_data = []  # Liste von Dictionaries {material_name: value}
        
        for i, variant in enumerate(project.variants):
            if i < len(self.visibility_vars) and self.visibility_vars[i].get():
                variant_names.append(variant.name)
                
                # Materialwerte sammeln (nach Systemgrenze)
                material_values = {}
                for row in variant.rows:
                    if row.material_name:
                        val = self._get_value_for_boundary(row, project.system_boundary)
                        material_values[row.material_name] = val / 1000.0  # kg → t
                
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
        
        # Für jede Variante (OHNE Labels, werden manuell hinzugefügt)
        for idx, (name, material_values) in enumerate(zip(variant_names, variant_data)):
            bottom = 0
            for material_name in sorted(material_values.keys()):
                value = material_values[material_name]
                color = material_colors[material_name]
                ax.bar(
                    idx,
                    value,
                    bottom=bottom,
                    color=color,
                    edgecolor='white',
                    linewidth=0.5
                )
                bottom += value
        
        # 5. Achsenbeschriftung
        ax.set_xticks(x_pos)
        ax.set_xticklabels(variant_names, fontsize=10)
        ax.set_ylabel("t CO₂-Äq.")
        ax.set_title(f"Variantenvergleich - {project.system_boundary}")
        ax.grid(axis='y', alpha=0.3)
        
        # 6. Legende MANUELL erstellen für ALLE Materialien
        if all_materials:
            from matplotlib.patches import Rectangle
            
            # Erstelle Patches für alle Materialien (sortiert)
            legend_handles = []
            legend_labels = []
            for material_name in sorted(all_materials):
                color = material_colors[material_name]
                patch = Rectangle((0, 0), 1, 1, fc=color, edgecolor='white')
                legend_handles.append(patch)
                legend_labels.append(material_name)
            
            # Legende horizontal und vertikal zentriert
            # Diagramm endet bei right=0.35, Fenster bei 1.0
            # Mitte: (0.35 + 1.0) / 2 = 0.675 in Figure-Koordinaten
            ncol = 1 if len(legend_handles) <= 10 else 2
            legend = ax.legend(
                legend_handles,
                legend_labels,
                loc='center',
                bbox_to_anchor=(1.92, 0.5),  # 1.92 = (0.675 - 0.35) / 0.27 * 2 offset
                fontsize=9,
                framealpha=0.9,
                ncol=ncol,
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
        
        # 8. Festes Layout für vollständige Legende (Diagramm schmäler)
        self.figure.subplots_adjust(left=0.08, right=0.35, top=0.92, bottom=0.12)
    
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
        
        # Grid erstellen: 2 Spalten
        for idx, variant in enumerate(visible_variants):
            row = idx // 2
            col = idx % 2
            
            # Varianten-Frame
            variant_frame = ctk.CTkFrame(grid_frame, fg_color=("white", "#2b2b2b"))
            variant_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            # Grid-Gewichte
            grid_frame.grid_columnconfigure(col, weight=1)
            
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
            # Mindestens 3, maximal 10 Zeilen + 1 für Summe
            dynamic_height = min(max(row_count + 1, 3), 10)
            tree = ttk.Treeview(
                variant_frame,
                columns=columns,
                show="headings",
                height=dynamic_height
            )
            
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
            
            # Spalten - optimierte Breiten
            tree.heading("material", text="Material")
            tree.heading("co2", text="CO₂ [t]")
            tree.column("material", width=350)  # Breiter für Namen
            tree.column("co2", width=70)  # Schmäler für Zahlen
            
            # Daten für diese Variante
            variant_total = 0
            for row in variant.rows:
                if row.material_name:
                    val = self._get_value_for_boundary(row, project.system_boundary)
                    val_tons = val / 1000.0  # kg → t
                    tree.insert("", "end", values=(
                        row.material_name,  # Voller Name, kein Kürzen
                        f"{val_tons:.2f}"
                    ))
                    variant_total += val_tons
            
            # Summe
            tree.insert("", "end", values=(
                "SUMME",
                f"{variant_total:.2f}"
            ), tags=("total",))
            tree.tag_configure("total", background="#4a4a4a" if current_mode == "Dark" else "#e0e0e0")
            
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
        project = self.orchestrator.get_current_project()
        if project:
            new_name = self.project_entry.get().strip()
            if new_name and new_name != project.name:
                project.name = new_name
                self.orchestrator.notify_change()
                self.logger.info(f"Projektname geändert: {new_name}")
                
                # Trigger Event für ProjectTree und MainWindow
                self.orchestrator.state.trigger('project_renamed', new_name)
    
    def _on_visibility_changed(self) -> None:
        """Varianten-Sichtbarkeit wurde geändert"""
        for i, var in enumerate(self.visibility_vars):
            self.orchestrator.set_variant_visibility(i, var.get())
        
        # Dashboard wird über visibility_changed Event neu geladen
        # (kein self.refresh() mehr nötig)
