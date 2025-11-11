"""
Chart-Erstellung für PDF-Export

Erstellt Matplotlib-Diagramme und konvertiert sie in ReportLab-Images:
- Dashboard-Variantenvergleich (gestapeltes Balkendiagramm)
- Einzelne Varianten-Diagramme (horizontales Balkendiagramm)

Alle Diagramme werden mit hoher DPI-Qualität und sauberer Formatierung erstellt.
"""

from models.variant import Variant
from models.project import Project
from reportlab.lib.units import cm
from reportlab.platypus import Image as RLImage
import matplotlib.pyplot as plt
import logging
import io
from typing import Optional, List

import matplotlib
matplotlib.use('Agg')  # Headless backend


logger = logging.getLogger(__name__)


class PDFChartCreator:
    """Erstellt Diagramme für PDF-Export"""

    def __init__(self, project: Project, orchestrator=None):
        """
        Initialisiert Chart-Creator

        Args:
            project: Projekt mit Varianten-Daten
            orchestrator: AppOrchestrator für zentrale Materialfarben
        """
        self.project = project
        self.orchestrator = orchestrator

        # Matplotlib-Konfiguration
        plt.rcParams['font.size'] = 11
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['xtick.labelsize'] = 10
        plt.rcParams['ytick.labelsize'] = 10
        plt.rcParams['legend.fontsize'] = 9
        plt.rcParams['figure.titlesize'] = 14
        # plt.rcParams['axes.labelweight'] = 'bold'
        plt.rcParams['axes.titleweight'] = 'bold'

    @staticmethod
    def figure_to_image(figure, width_cm: float = 16, height_cm: float = 11) -> Optional[RLImage]:
        """
        Konvertiert eine bestehende Matplotlib Figure in ein ReportLab Image

        Args:
            figure: Matplotlib Figure
            width_cm: Breite in cm
            height_cm: Höhe in cm

        Returns:
            ReportLab Image oder None bei Fehler
        """
        try:
            # Figure in BytesIO speichern
            img_buffer = io.BytesIO()

            # Setze Hintergrund auf weiß für PDF
            figure.patch.set_facecolor('white')
            for ax in figure.get_axes():
                ax.set_facecolor('white')
                # Textfarben auf schwarz setzen
                ax.tick_params(colors='black')
                if ax.xaxis.label:
                    ax.xaxis.label.set_color('black')
                if ax.yaxis.label:
                    ax.yaxis.label.set_color('black')
                if ax.title:
                    ax.title.set_color('black')
                # Spines auf schwarz
                for spine in ax.spines.values():
                    if spine.get_visible():
                        spine.set_color('black')
                # Legende anpassen
                legend = ax.get_legend()
                if legend:
                    legend.get_frame().set_facecolor('white')
                    legend.get_frame().set_edgecolor('gray')
                    for text in legend.get_texts():
                        text.set_color('black')

            # WICHTIG: Kein bbox_inches='tight', damit alle Varianten gleich groß sind!
            figure.savefig(
                img_buffer,
                format='png',
                dpi=200,
                facecolor='white',
                edgecolor='none'
            )
            img_buffer.seek(0)

            return RLImage(img_buffer, width=width_cm*cm, height=height_cm*cm)

        except Exception as e:
            logger.error(
                f"Fehler beim Konvertieren der Figure: {e}", exc_info=True)
            return None

    def create_dashboard_chart(
        self,
        variant_indices: List[int],
        width_cm: float = 15.5,
        height_cm: float = 11
    ) -> Optional[RLImage]:
        """
        Erstellt Dashboard-Variantenvergleich (gestapeltes Balkendiagramm)
        Basiert auf der exakten Logik aus dashboard_view.py

        Args:
            variant_indices: Liste der Varianten-Indizes
            width_cm: Breite in cm
            height_cm: Höhe in cm

        Returns:
            ReportLab Image oder None bei Fehler
        """
        try:
            # Nur ausgewählte Varianten
            variants = [self.project.variants[i]
                        for i in variant_indices if i < len(self.project.variants)]

            if not variants:
                logger.warning("Keine Varianten für Dashboard-Chart")
                return None

            # 1. Alle Materialien über ausgewählte Varianten sammeln
            all_materials = set()
            for variant in variants:
                for row in variant.rows:
                    if row.material_name:
                        all_materials.add(row.material_name)

            num_materials = len(all_materials)

            # 2. Zentrale Farbverwaltung aktualisieren (falls Orchestrator vorhanden)
            if self.orchestrator:
                # Aktualisiere mit allen Varianten des Projekts
                self.orchestrator.update_material_colors()

            # 3. Varianten sammeln - nur tatsächlich vorhandene Materialien
            variant_names = [v.name for v in variants]
            variant_data = []  # Liste von Dictionaries {material_name: value}

            for variant in variants:
                # Materialwerte sammeln (nach Systemgrenze)
                material_values = {}
                for row in variant.rows:
                    if row.material_name:
                        val = self._get_value_for_boundary(row)
                        # kg → t
                        # WICHTIG: Addiere Werte wenn Material mehrfach vorkommt
                        if row.material_name in material_values:
                            material_values[row.material_name] += val / 1000.0
                        else:
                            material_values[row.material_name] = val / 1000.0
                variant_data.append(material_values)

            # Figure erstellen - noch größer ohne Legende
            fig, ax = plt.subplots(figsize=(12, 7))

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
                        # Verwende zentrale Farbzuordnung falls vorhanden
                        if self.orchestrator:
                            color = self.orchestrator.get_material_color(material_name)
                        else:
                            # Fallback: Lokale Farbzuweisung
                            colors_list = plt.cm.tab20.colors
                            mat_list = sorted(all_materials)
                            color = colors_list[mat_list.index(material_name) % len(colors_list)]
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

            # X-Achsen-Labels (Variantennamen) ABER kein xlabel
            ax.set_xticklabels(variant_names, fontsize=15,
                               rotation=rotation, ha=ha, fontweight='bold')
            ax.set_ylabel('CO2-Äquivalent [t]',
                          fontweight='bold', fontsize=16, labelpad=15)
            # Y-Achsen-Ticks nicht zu groß
            ax.tick_params(axis='y', labelsize=14)
            
            # Nulllinie prominent darstellen (wichtig für pos/neg Werte)
            ax.axhline(y=0, color='black', linewidth=1.5, alpha=0.8, zorder=3)
            ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5)
            ax.set_axisbelow(True)

            # 6. KEINE Legende im PDF Dashboard

            # 7. Spines für PDF (schwarz)
            ax.spines['bottom'].set_color('black')
            ax.spines['left'].set_color('black')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

            # 8. Layout anpassen - zentriert ohne Legende
            fig.subplots_adjust(left=0.12, right=0.90, top=0.95, bottom=0.10)

            # In BytesIO speichern
            img_buffer = io.BytesIO()
            plt.savefig(
                img_buffer,
                format='png',
                dpi=200,
                bbox_inches='tight',
                facecolor='white',
                edgecolor='none'
            )
            img_buffer.seek(0)
            plt.close(fig)

            return RLImage(img_buffer, width=width_cm*cm, height=height_cm*cm)

        except Exception as e:
            logger.error(
                f"Fehler beim Erstellen des Dashboard-Charts: {e}", exc_info=True)
            return None

    def create_variant_chart(
        self,
        variant: Variant,
        width_cm: float = 15.5,
        height_cm: float = 9
    ) -> Optional[RLImage]:
        """
        Erstellt Varianten-Diagramm (gestapelter vertikaler Balken mit Legende rechts)

        EXAKTE KOPIE der GUI-Logik aus variant_view.py!

        Args:
            variant: Variante
            width_cm: Breite in cm
            height_cm: Höhe in cm

        Returns:
            ReportLab Image oder None bei Fehler
        """
        try:
            if not variant.rows:
                logger.warning(f"Keine Materialien in Variante {variant.name}")
                return None

            # WICHTIG: Farben NICHT neu setzen, wenn bereits gesetzt!
            # Die Farben sollten bereits vom Dashboard/GUI gesetzt sein
            if self.orchestrator and not self.orchestrator.state.material_colors:
                # Nur wenn noch keine Farben gesetzt sind, setze sie jetzt
                variant_index = self.project.variants.index(variant) if variant in self.project.variants else 0
                self.orchestrator.update_material_colors([variant_index])
            
            # Daten sammeln - aggregiere doppelte Materialien
            material_values = {}
            MAX_NAME_LENGTH = 50  # Maximale Länge für Material-Namen

            for row in variant.rows:
                if row.material_name:
                    value = self._get_value_for_boundary(
                        row) / 1000.0  # kg → t
                    # Addiere Werte wenn Material mehrfach vorkommt
                    if row.material_name in material_values:
                        material_values[row.material_name] += value
                    else:
                        material_values[row.material_name] = value

            # Erstelle Listen mit gekürzten Namen (ALPHABETISCH SORTIERT für konsistente Farben)
            labels = []
            values = []
            original_names = []  # Original-Namen für Farbzuordnung
            for material_name, value in sorted(material_values.items(), key=lambda x: x[0]):
                # Kürze zu lange Namen mit ...
                name = material_name
                if len(name) > MAX_NAME_LENGTH:
                    name = name[:MAX_NAME_LENGTH-3] + "..."
                labels.append(name)
                values.append(value)
                original_names.append(material_name)  # Original-Namen speichern

            if not values:
                return None

            # Figure erstellen - Größe an PDF-Export angepasst
            # width_cm/height_cm definieren das Zielbild, figsize sollte proportional sein
            fig_width_inch = width_cm / 2.54  # cm zu inch
            fig_height_inch = height_cm / 2.54
            fig, ax = plt.subplots(
                figsize=(fig_width_inch, fig_height_inch), dpi=100, facecolor='white')
            ax.set_facecolor('white')

            # Gestapeltes VERTIKALES Balkendiagramm - positive oben, negative unten
            bottom_positive = 0  # Für positive Werte (nach oben)
            bottom_negative = 0  # Für negative Werte (nach unten)
            
            for i, (label, value) in enumerate(zip(labels, values)):
                if value == 0:
                    continue  # Überspringe Nullwerte
                
                # Verwende zentrale Farbzuordnung falls vorhanden
                original_name = original_names[i]
                if self.orchestrator:
                    color = self.orchestrator.get_material_color(original_name)
                else:
                    # Fallback: Lokale Farbzuweisung
                    colors_list = plt.cm.tab20.colors
                    color = colors_list[i % len(colors_list)]
                
                if value > 0:
                    # Positive Werte von 0 nach oben stapeln
                    ax.bar(
                        0,  # X-Position (eine Säule)
                        value,
                        bottom=bottom_positive,
                        width=0.7,
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
                        width=0.7,
                        color=color,
                        edgecolor='white'
                    )
                    bottom_negative += value

            # Achsen - KEIN Titel mehr
            ax.set_ylabel(
                "CO2-Äquivalent [t]", fontsize=9, labelpad=10, fontweight='bold')
            ax.tick_params(axis='y', labelsize=8)
            ax.set_xticks([])
            ax.set_xlim(-0.5, 0.5)
            
            # Nulllinie prominent darstellen (wichtig für pos/neg Trennung)
            ax.axhline(y=0, color='black', linewidth=1.5, alpha=0.8, zorder=3)
            ax.grid(axis='y', alpha=0.3)

            # Legende manuell erstellen (alphabetisch sortiert für Konsistenz)
            from matplotlib.patches import Rectangle
            legend_handles = []
            legend_labels_list = []
            for material_name in sorted(original_names):
                if self.orchestrator:
                    color = self.orchestrator.get_material_color(material_name)
                else:
                    colors_list = plt.cm.tab20.colors
                    sorted_names = sorted(original_names)
                    color = colors_list[sorted_names.index(material_name) % len(colors_list)]
                patch = Rectangle((0, 0), 1, 1, fc=color, edgecolor='white')
                legend_handles.append(patch)
                # Kürze Namen wenn nötig
                display_name = material_name if len(material_name) <= MAX_NAME_LENGTH else material_name[:MAX_NAME_LENGTH-3] + "..."
                legend_labels_list.append(display_name)
            
            # Legende rechts neben dem Diagramm - OHNE Rahmen
            ax.legend(
                legend_handles,
                legend_labels_list,
                loc='center left',
                bbox_to_anchor=(1.3, 0.5),
                fontsize=9,
                framealpha=0.9,
                ncol=1,  # Eine Spalte
                frameon=False
            )

            # Spines - kein Rahmen um reines Diagramm (Rahmen kommt von ReportLab Table)
            ax.spines['bottom'].set_color('black')
            ax.spines['left'].set_color('black')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.tick_params(colors='black')
            ax.yaxis.label.set_color('black')

            # Layout anpassen - mehr Canvas wie beim Dashboard
            # Links mehr Platz für Y-Achse, rechts weniger für Legende (kompakter)
            fig.subplots_adjust(left=0.12, right=0.30, top=0.95, bottom=0.10)

            # In BytesIO speichern
            # WICHTIG: Kein bbox_inches='tight', damit alle Varianten gleich groß sind!
            img_buffer = io.BytesIO()
            fig.savefig(
                img_buffer,
                format='png',
                dpi=200,
                facecolor='white',
                edgecolor='none'
            )
            img_buffer.seek(0)
            plt.close(fig)

            return RLImage(img_buffer, width=width_cm*cm, height=height_cm*cm)

        except Exception as e:
            logger.error(
                f"Fehler beim Erstellen des Varianten-Charts: {e}", exc_info=True)
            return None

    def _get_value_for_boundary(self, row) -> float:
        """
        Holt korrekten CO₂-Wert basierend auf Systemgrenze
        WICHTIG: Muss identisch mit dashboard_view.py sein!

        Args:
            row: MaterialRow

        Returns:
            CO₂-Wert in kg
        """
        boundary = self.project.system_boundary
        
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
