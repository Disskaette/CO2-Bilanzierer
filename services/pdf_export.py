"""
PDF Export Service für CO₂-Bilanzierung
"""

import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime
import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    Image as RLImage, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from models.project import Project
from models.variant import Variant

logger = logging.getLogger(__name__)


class PDFExporter:
    """PDF Export für CO₂-Bilanzierung"""

    def export(
        self,
        filepath: str,
        project: Project,
        include_dashboard: bool = True,
        include_variants: List[int] = None,
        logo_path: Optional[str] = None,
        additional_image_path: Optional[str] = None
    ) -> bool:
        """Exportiert PDF mit Diagrammen und Tabellen"""
        try:
            logger.info(f"Starte PDF-Export: {filepath}")

            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2.5*cm,
                bottomMargin=2*cm
            )

            story = []
            styles = getSampleStyleSheet()

            # Custom Styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                textColor=colors.HexColor('#1f6aa5'),
                spaceAfter=12,
                alignment=TA_LEFT,
                fontName='Helvetica-Bold'
            )

            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.black,
                spaceBefore=12,
                spaceAfter=6,
                fontName='Helvetica-Bold',
                borderWidth=2,
                borderColor=colors.HexColor('#FFD700'),
                borderPadding=5,
                backColor=colors.HexColor('#FFFFCC')
            )

            # Logo einfügen
            if logo_path and Path(logo_path).exists():
                try:
                    logo = RLImage(logo_path, width=4*cm, height=2*cm)
                    story.append(logo)
                    story.append(Spacer(1, 0.3*cm))
                except Exception as e:
                    logger.warning(f"Logo konnte nicht geladen werden: {e}")

            # Titel
            story.append(Paragraph(project.name, title_style))
            story.append(Spacer(1, 0.2*cm))

            # Metadaten
            meta_data = [
                ['Datum:', datetime.now().strftime('%d.%m.%Y')],
                ['Systemgrenze:', project.system_boundary]
            ]
            meta_table = Table(meta_data, colWidths=[3*cm, 12*cm])
            meta_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ]))
            story.append(meta_table)
            story.append(Spacer(1, 0.5*cm))

            # Dashboard
            if include_dashboard:
                story.append(Paragraph("Variantenvergleich", heading_style))
                story.append(Spacer(1, 0.3*cm))

                chart_img = self._create_dashboard_chart(project)
                if chart_img:
                    story.append(chart_img)
                    story.append(Spacer(1, 0.3*cm))

                dashboard_table = self._create_dashboard_summary_table(project)
                if dashboard_table:
                    story.append(dashboard_table)

            # Varianten
            if include_variants is None:
                include_variants = list(range(len(project.variants)))

            for idx in include_variants:
                if idx < len(project.variants):
                    variant = project.variants[idx]
                    story.append(PageBreak())
                    story.append(Paragraph(f"{variant.name}", heading_style))
                    story.append(Spacer(1, 0.3*cm))

                    variant_chart = self._create_variant_chart(variant)
                    if variant_chart:
                        story.append(variant_chart)
                        story.append(Spacer(1, 0.3*cm))

                    variant_table = self._create_variant_table(variant, project.system_boundary)
                    if variant_table:
                        story.append(variant_table)

            # Zusatzbild
            if additional_image_path and Path(additional_image_path).exists():
                try:
                    story.append(PageBreak())
                    story.append(Paragraph("Weitere Informationen", heading_style))
                    story.append(Spacer(1, 0.3*cm))
                    add_img = RLImage(additional_image_path, width=15*cm, height=10*cm)
                    story.append(add_img)
                except Exception as e:
                    logger.warning(f"Zusatzbild konnte nicht geladen werden: {e}")

            # PDF bauen
            def add_page_number(canvas_obj, doc_obj):
                canvas_obj.saveState()
                canvas_obj.setFont('Helvetica', 9)
                page_num = canvas_obj.getPageNumber()
                canvas_obj.drawRightString(A4[0] - 2*cm, 1.5*cm, f"Seite {page_num}")
                canvas_obj.restoreState()

            doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
            logger.info("PDF erfolgreich erstellt")
            return True

        except Exception as e:
            logger.error(f"PDF-Export Fehler: {e}", exc_info=True)
            return False

    def _create_dashboard_chart(self, project: Project) -> Optional[RLImage]:
        """Erstellt Dashboard-Diagramm"""
        try:
            visible_variants = [
                v for i, v in enumerate(project.variants)
                if i < len(project.visible_variants) and project.visible_variants[i]
            ]

            if not visible_variants:
                return None

            variant_names = [v.name for v in visible_variants]
            all_materials = {}
            
            for variant in visible_variants:
                for row in variant.rows:
                    if row.material_name not in all_materials:
                        all_materials[row.material_name] = []
            
            for material_name in all_materials.keys():
                for variant in visible_variants:
                    row = next((r for r in variant.rows if r.material_name == material_name), None)
                    if row:
                        value = self._get_value_for_boundary(row, project.system_boundary)
                        all_materials[material_name].append(value / 1000.0)
                    else:
                        all_materials[material_name].append(0.0)

            fig, ax = plt.subplots(figsize=(6, 4))
            x_pos = range(len(variant_names))
            bottom = [0] * len(variant_names)
            colors_list = plt.cm.tab20.colors
            
            for i, (material, values) in enumerate(all_materials.items()):
                ax.bar(x_pos, values, bottom=bottom, label=material, 
                       color=colors_list[i % len(colors_list)])
                bottom = [b + v for b, v in zip(bottom, values)]

            ax.set_ylabel('CO₂ [t]')
            ax.set_title('Variantenvergleich')
            ax.set_xticks(x_pos)
            ax.set_xticklabels(variant_names, rotation=45, ha='right')
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=7)
            ax.grid(axis='y', alpha=0.3)
            plt.tight_layout()

            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close(fig)

            return RLImage(img_buffer, width=15*cm, height=10*cm)

        except Exception as e:
            logger.error(f"Dashboard-Chart Fehler: {e}", exc_info=True)
            return None

    def _create_variant_chart(self, variant: Variant) -> Optional[RLImage]:
        """Erstellt Varianten-Diagramm"""
        try:
            if not variant.rows:
                return None

            materials = [row.material_name for row in variant.rows]
            values = [row.result_a / 1000.0 for row in variant.rows]

            fig, ax = plt.subplots(figsize=(6, 3))
            colors_list = plt.cm.tab20.colors
            ax.barh(materials, values, color=colors_list[:len(materials)])
            ax.set_xlabel('CO₂ [t]')
            ax.set_title(f'{variant.name}')
            ax.grid(axis='x', alpha=0.3)
            plt.tight_layout()

            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close(fig)

            return RLImage(img_buffer, width=12*cm, height=8*cm)

        except Exception as e:
            logger.error(f"Varianten-Chart Fehler: {e}", exc_info=True)
            return None

    def _create_dashboard_summary_table(self, project: Project) -> Optional[Table]:
        """Dashboard-Tabelle"""
        try:
            visible_variants = [
                v for i, v in enumerate(project.variants)
                if i < len(project.visible_variants) and project.visible_variants[i]
            ]

            if not visible_variants:
                return None

            data = [['Variante', 'CO₂-Gesamt [t]']]

            for variant in visible_variants:
                value = self._get_variant_total(variant, project.system_boundary)
                data.append([variant.name, f"{value / 1000.0:.2f}"])

            table = Table(data, colWidths=[10*cm, 5*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f6aa5')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))

            return table

        except Exception as e:
            logger.error(f"Dashboard-Tabelle Fehler: {e}", exc_info=True)
            return None

    def _create_variant_table(self, variant: Variant, system_boundary: str) -> Optional[Table]:
        """Varianten-Materialtabelle"""
        try:
            if not variant.rows:
                return None

            data = [['Pos', 'Material', 'Menge', 'Einheit', 'CO₂ [t]']]

            for i, row in enumerate(variant.rows, 1):
                value = self._get_value_for_boundary(row, system_boundary)
                data.append([
                    str(i),
                    row.material_name,
                    f"{row.quantity:.2f}",
                    row.material_unit,
                    f"{value / 1000.0:.2f}"
                ])

            total = self._get_variant_total(variant, system_boundary)
            data.append(['', 'SUMME', '', '', f"{total / 1000.0:.2f}"])

            table = Table(data, colWidths=[1.5*cm, 7*cm, 2*cm, 2*cm, 2.5*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f6aa5')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (2, 1), (-1, -2), 'RIGHT'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f0f0f0')]),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FFFFCC')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('ALIGN', (0, -1), (-1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))

            return table

        except Exception as e:
            logger.error(f"Varianten-Tabelle Fehler: {e}", exc_info=True)
            return None

    def _get_value_for_boundary(self, row, boundary: str) -> float:
        """Holt korrekten Wert basierend auf Systemgrenze"""
        if 'bio' in boundary.lower():
            if 'D' in boundary:
                return row.result_acd_bio or row.result_acd or 0.0
            elif 'C3' in boundary or 'C4' in boundary:
                return row.result_ac_bio or row.result_ac
            else:
                return row.result_a_bio or row.result_a
        else:
            if 'D' in boundary:
                return row.result_acd or 0.0
            elif 'C3' in boundary or 'C4' in boundary:
                return row.result_ac
            else:
                return row.result_a

    def _get_variant_total(self, variant: Variant, boundary: str) -> float:
        """Holt Variantensumme basierend auf Systemgrenze"""
        if 'bio' in boundary.lower():
            if 'D' in boundary:
                return variant.sum_acd_bio or variant.sum_acd or 0.0
            elif 'C3' in boundary or 'C4' in boundary:
                return variant.sum_ac_bio or variant.sum_ac
            else:
                return variant.sum_a_bio or variant.sum_a
        else:
            if 'D' in boundary:
                return variant.sum_acd or 0.0
            elif 'C3' in boundary or 'C4' in boundary:
                return variant.sum_ac
            else:
                return variant.sum_a
