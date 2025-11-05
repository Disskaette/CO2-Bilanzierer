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

    def __init__(self, project: Project):
        """
        Initialisiert Chart-Creator

        Args:
            project: Projekt mit Varianten-Daten
        """
        self.project = project

        # Matplotlib-Konfiguration
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.labelsize'] = 10
        plt.rcParams['axes.titlesize'] = 12
        plt.rcParams['xtick.labelsize'] = 9
        plt.rcParams['ytick.labelsize'] = 9
        plt.rcParams['legend.fontsize'] = 8
        plt.rcParams['figure.titlesize'] = 12

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
        width_cm: float = 16,
        height_cm: float = 11
    ) -> Optional[RLImage]:
        """
        Erstellt Dashboard-Variantenvergleich (gestapeltes Balkendiagramm)

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

            variant_names = [v.name for v in variants]

            # Materialien sammeln
            all_materials = {}
            for variant in variants:
                for row in variant.rows:
                    if row.material_name not in all_materials:
                        all_materials[row.material_name] = []

            # Werte pro Material und Variante
            for material_name in all_materials.keys():
                for variant in variants:
                    row = next(
                        (r for r in variant.rows if r.material_name == material_name), None)
                    if row:
                        value = self._get_value_for_boundary(row)
                        all_materials[material_name].append(
                            value / 1000.0)  # in Tonnen
                    else:
                        all_materials[material_name].append(0.0)

            # Figure erstellen
            fig, ax = plt.subplots(figsize=(7, 5))

            # Gestapeltes Balkendiagramm
            x_pos = range(len(variant_names))
            bottom = [0] * len(variant_names)
            colors_list = plt.cm.tab20.colors

            for i, (material, values) in enumerate(all_materials.items()):
                ax.bar(
                    x_pos,
                    values,
                    bottom=bottom,
                    label=material,
                    color=colors_list[i % len(colors_list)],
                    edgecolor='white',
                    linewidth=0.5
                )
                bottom = [b + v for b, v in zip(bottom, values)]

            # Achsen und Titel
            ax.set_ylabel('CO2-Aequivalent [t]', fontweight='bold')
            ax.set_xlabel('Varianten', fontweight='bold')
            ax.set_title('CO2-Bilanzierung - Variantenvergleich',
                         fontweight='bold', pad=15)
            ax.set_xticks(x_pos)

            # X-Achsen-Labels: Rotation nur bei vielen Varianten
            if len(variant_names) <= 3:
                ax.set_xticklabels(variant_names, rotation=0, ha='center')
            else:
                ax.set_xticklabels(variant_names, rotation=45, ha='right')

            # Legende rechts vom Diagramm
            ax.legend(
                bbox_to_anchor=(1.02, 1),
                loc='upper left',
                frameon=True,
                edgecolor='gray',
                fancybox=False,
                shadow=False
            )

            # Grid
            ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5)
            ax.set_axisbelow(True)

            # Spines
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_linewidth(0.8)
            ax.spines['bottom'].set_linewidth(0.8)

            plt.tight_layout()

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
        width_cm: float = 14,
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

            # Daten sammeln (wie in GUI)
            labels = []
            values = []
            MAX_NAME_LENGTH = 63  # Maximale Länge für Material-Namen (1,8x Dashboard)
            
            for row in variant.rows:
                if row.material_name:
                    # Kürze zu lange Namen mit ...
                    name = row.material_name
                    if len(name) > MAX_NAME_LENGTH:
                        name = name[:MAX_NAME_LENGTH-3] + "..."
                    labels.append(name)
                    value = self._get_value_for_boundary(row) / 1000.0  # kg → t
                    values.append(value)

            if not values:
                return None

            # Figure erstellen (breiter als GUI für längere Namen in Legende)
            fig, ax = plt.subplots(
                figsize=(9, 3.5), dpi=100, facecolor='white')
            ax.set_facecolor('white')

            # Gestapeltes VERTIKALES Balkendiagramm (wie in GUI)
            colors_list = plt.cm.tab20.colors

            bottom = 0
            for i, (label, value) in enumerate(zip(labels, values)):
                color = colors_list[i % len(colors_list)]
                ax.bar(
                    0,  # X-Position (eine Säule)
                    value,
                    bottom=bottom,
                    width=0.6,
                    color=color,
                    edgecolor='white',
                    label=label  # Voller Name in Legende
                )
                bottom += value

            # Achsen und Titel (wie in GUI)
            ax.set_ylabel("t CO2-Aeq.", fontsize=10)
            ax.set_title(
                f"{variant.name} - {self.project.system_boundary}", fontsize=11, pad=10)
            ax.set_xticks([])
            ax.set_xlim(-0.5, 0.5)

            # Legende rechts neben dem Diagramm (wie in GUI)
            ax.legend(
                loc='center left',
                bbox_to_anchor=(1.02, 0.5),
                fontsize=10,
                framealpha=0.9,
                ncol=1,  # Eine Spalte
                frameon=True,
                edgecolor='gray'
            )

            # Spines (wie in GUI)
            ax.spines['bottom'].set_color('black')
            ax.spines['left'].set_color('black')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.tick_params(colors='black')
            ax.yaxis.label.set_color('black')
            ax.title.set_color('black')
            
            # Layout anpassen (wie in GUI: left=0.1, right=0.35)
            fig.subplots_adjust(left=0.1, right=0.35, top=0.88, bottom=0.05)
            
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
            logger.error(f"Fehler beim Erstellen des Varianten-Charts: {e}", exc_info=True)
            return None

    def _get_value_for_boundary(self, row) -> float:
        """
        Holt korrekten CO₂-Wert basierend auf Systemgrenze

        Args:
            row: MaterialRow

        Returns:
            CO₂-Wert in kg
        """
        boundary = self.project.system_boundary

        if 'bio' in boundary.lower():
            # Biogene Speicherung berücksichtigen
            if 'D' in boundary:
                return row.result_acd_bio or row.result_acd or 0.0
            elif 'C3' in boundary or 'C4' in boundary:
                return row.result_ac_bio or row.result_ac
            else:
                return row.result_a_bio or row.result_a
        else:
            # Standard (ohne biogene Speicherung)
            if 'D' in boundary:
                return row.result_acd or 0.0
            elif 'C3' in boundary or 'C4' in boundary:
                return row.result_ac
            else:
                return row.result_a
