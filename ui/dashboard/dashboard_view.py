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
        
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        # Projektname
        project = self.orchestrator.get_current_project()
        project_name = project.name if project else "Kein Projekt"
        
        self.project_entry = ctk.CTkEntry(
            header_frame,
            font=ctk.CTkFont(size=18, weight="bold"),
            height=40
        )
        self.project_entry.insert(0, project_name)
        self.project_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.project_entry.bind("<FocusOut>", self._on_project_name_changed)
        
        # Chart-Container
        chart_frame = ctk.CTkFrame(self)
        chart_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self._create_chart(chart_frame)
        
        # Sichtbarkeits-Checkboxen
        vis_frame = ctk.CTkFrame(self)
        vis_frame.pack(fill="x", padx=10, pady=10)
        
        vis_label = ctk.CTkLabel(
            vis_frame,
            text="Angezeigte Varianten:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        vis_label.pack(side="left", padx=10)
        
        # Dynamische Checkboxen für vorhandene Varianten
        self._create_visibility_checkboxes(vis_frame)
    
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
            for i, variant in enumerate(project.variants):
                var = ctk.BooleanVar(value=variant.visible)
                self.visibility_vars.append(var)
                
                cb = ctk.CTkCheckBox(
                    parent,
                    text=variant.name,
                    variable=var,
                    command=self._on_visibility_changed
                )
                cb.pack(side="left", padx=10)
    
    def _create_chart(self, parent: ctk.CTkFrame) -> None:
        """Erstellt Matplotlib-Chart"""
        
        # Figure erstellen mit Theme
        is_dark = ctk.get_appearance_mode() == "Dark"
        fig_color = '#2b2b2b' if is_dark else 'white'
        
        self.figure = Figure(figsize=(8, 4.5), dpi=100, facecolor=fig_color)
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
        self.canvas = FigureCanvasTkAgg(self.figure, parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def _plot_comparison(self, ax, project) -> None:
        """
        Zeichnet Vergleichsdiagramm
        
        Args:
            ax: Matplotlib Axes
            project: Project-Objekt
        """
        
        # Varianten sammeln
        variant_names = []
        variant_data = []  # Liste von Listen (Materialien pro Variante)
        
        for i, variant in enumerate(project.variants):
            if i < len(self.visibility_vars) and self.visibility_vars[i].get():
                variant_names.append(variant.name)
                
                # Materialwerte sammeln (nach Systemgrenze)
                values = []
                for row in variant.rows:
                    val = self._get_value_for_boundary(row, project.system_boundary)
                    values.append(val)
                
                variant_data.append(values)
        
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
        
        # Gestapeltes Balkendiagramm
        x_pos = range(len(variant_names))
        
        # Farbpalette
        colors = plt.cm.tab20.colors
        
        # Für jede Variante
        for idx, (name, values) in enumerate(zip(variant_names, variant_data)):
            bottom = 0
            for mat_idx, value in enumerate(values):
                color = colors[mat_idx % len(colors)]
                ax.bar(
                    idx,
                    value,
                    bottom=bottom,
                    color=color,
                    edgecolor='white',
                    linewidth=0.5
                )
                bottom += value
        
        # Achsenbeschriftung
        ax.set_xticks(x_pos)
        ax.set_xticklabels(variant_names)
        ax.set_ylabel("kg CO₂-Äq.")
        ax.set_title(f"Variantenvergleich - {project.system_boundary}")
        ax.grid(axis='y', alpha=0.3)
        
        # Theme anpassen
        if ctk.get_appearance_mode() == "Dark":
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
    
    def _get_value_for_boundary(self, row, boundary: str) -> float:
        """Gibt Wert für Systemgrenze zurück"""
        if boundary == "A1-A3":
            return row.result_a
        elif boundary == "A1-A3+C3+C4":
            return row.result_ac
        elif boundary == "A1-A3+C3+C4+D":
            return row.result_acd if row.result_acd is not None else row.result_ac
        return row.result_a
    
    def refresh(self) -> None:
        """Aktualisiert Dashboard"""
        # Prüfen, ob Widget noch existiert
        try:
            if not self.winfo_exists():
                return
        except:
            return
        
        # Checkboxen aktualisieren (erstes Kind-Widget)
        try:
            children = self.winfo_children()
            if len(children) > 0:
                vis_frame = children[0]
                self._create_visibility_checkboxes(vis_frame)
        except:
            pass
        
        # Chart neu zeichnen
        try:
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
                self.canvas = None
        except:
            pass
        
        try:
            # Finde Chart-Frame (zweites Kind-Widget)
            children = self.winfo_children()
            if len(children) > 1:
                chart_frame = children[1]
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
            new_name = self.project_entry.get()
            project.name = new_name
            self.orchestrator.notify_change()
            self.logger.info(f"Projektname geändert: {new_name}")
    
    def _on_visibility_changed(self) -> None:
        """Varianten-Sichtbarkeit wurde geändert"""
        for i, var in enumerate(self.visibility_vars):
            self.orchestrator.set_variant_visibility(i, var.get())
        
        self.refresh()
