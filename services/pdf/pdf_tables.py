"""
Tabellen-Erstellung für PDF-Export

Erstellt professionelle Tabellen im Excel-Stil:
- Dashboard-Zusammenfassungstabelle
- Varianten-Materialtabellen mit SUMMEN-Zeile
- Formatierung: graue Header, alternierende Zeilen, Grid

Alle Tabellen mit korrekter Formatierung gemäß Excel-Vorgabe.
"""

import logging
from typing import Optional, List

from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import cm

from models.project import Project
from models.variant import Variant
from services.pdf.pdf_styles import PDFColors

logger = logging.getLogger(__name__)


class PDFTableCreator:
    """Erstellt Tabellen für PDF-Export"""
    
    def __init__(self, project: Project):
        """
        Initialisiert Table-Creator
        
        Args:
            project: Projekt mit Varianten-Daten
        """
        self.project = project
        self.colors = PDFColors()
    
    def create_dashboard_table(self, variant_indices: List[int]) -> Optional[Table]:
        """
        Erstellt Dashboard-Zusammenfassungstabelle
        
        Args:
            variant_indices: Liste der Varianten-Indizes
            
        Returns:
            ReportLab Table oder None bei Fehler
        """
        try:
            variants = [
                self.project.variants[i]
                for i in variant_indices
                if i < len(self.project.variants)
            ]
            
            if not variants:
                logger.warning("Keine Varianten für Dashboard-Tabelle")
                return None
            
            # Header
            data = [['Variante', 'CO2-Gesamt [t]']]
            
            # Daten
            for variant in variants:
                value = self._get_variant_total(variant)
                data.append([
                    variant.name,
                    f"{value / 1000.0:.2f}"
                ])
            
            # Tabelle erstellen
            table = Table(data, colWidths=[12*cm, 4*cm])
            
            # Style
            table.setStyle(TableStyle([
                # ===== HEADER =====
                ('BACKGROUND', (0, 0), (-1, 0), self.colors.TABLE_HEADER_BG),
                ('TEXTCOLOR', (0, 0), (-1, 0), self.colors.TABLE_HEADER_TEXT),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                
                # ===== DATEN =====
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),      # Varianten-Namen links
                ('ALIGN', (1, 1), (1, -1), 'RIGHT'),     # CO₂-Werte rechts
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('LEFTPADDING', (0, 1), (-1, -1), 8),
                ('RIGHTPADDING', (0, 1), (-1, -1), 8),
                
                # Alternierende Zeilen
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.colors.TABLE_ROW_ALT_BG]),
                
                # ===== GRID =====
                ('GRID', (0, 0), (-1, -1), 1, self.colors.TABLE_GRID),
                ('BOX', (0, 0), (-1, -1), 1.5, self.colors.BORDER_BLACK),
            ]))
            
            return table
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Dashboard-Tabelle: {e}", exc_info=True)
            return None
    
    def create_variant_table(self, variant: Variant) -> Optional[Table]:
        """
        Erstellt Varianten-Materialtabelle
        
        Args:
            variant: Variante
            
        Returns:
            ReportLab Table oder None bei Fehler
        """
        try:
            if not variant.rows:
                logger.warning(f"Keine Materialien in Variante {variant.name}")
                return None
            
            # Header
            data = [['Pos', 'Material', 'Menge', 'Einheit', 'CO2 [t]']]
            
            MAX_NAME_LENGTH = 50  # Maximale Länge für Material-Namen in Tabelle
            
            # Daten
            for i, row in enumerate(variant.rows, 1):
                value = self._get_value_for_boundary(row)
                # Kürze zu lange Namen mit ...
                name = row.material_name
                if len(name) > MAX_NAME_LENGTH:
                    name = name[:MAX_NAME_LENGTH-3] + "..."
                
                data.append([
                    str(i),
                    name,
                    f"{row.quantity:.2f}",
                    row.material_unit,
                    f"{value / 1000.0:.2f}"
                ])
            
            # SUMMEN-Zeile
            total = self._get_variant_total(variant)
            data.append(['', 'SUMME', '', '', f"{total / 1000.0:.2f}"])
            
            # Tabelle erstellen
            table = Table(data, colWidths=[1.5*cm, 8*cm, 2.5*cm, 2*cm, 2*cm])
            
            # Style
            table.setStyle(TableStyle([
                # ===== HEADER =====
                ('BACKGROUND', (0, 0), (-1, 0), self.colors.TABLE_HEADER_BG),
                ('TEXTCOLOR', (0, 0), (-1, 0), self.colors.TABLE_HEADER_TEXT),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                
                # ===== DATEN =====
                ('ALIGN', (0, 1), (0, -2), 'CENTER'),    # Pos zentriert
                ('ALIGN', (1, 1), (1, -2), 'LEFT'),      # Material links
                ('ALIGN', (2, 1), (2, -2), 'RIGHT'),     # Menge rechts
                ('ALIGN', (3, 1), (3, -2), 'CENTER'),    # Einheit zentriert
                ('ALIGN', (4, 1), (4, -2), 'RIGHT'),     # CO₂ rechts
                ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -2), 9),
                ('TOPPADDING', (0, 1), (-1, -2), 4),
                ('BOTTOMPADDING', (0, 1), (-1, -2), 4),
                ('LEFTPADDING', (0, 1), (-1, -2), 6),
                ('RIGHTPADDING', (0, 1), (-1, -2), 6),
                
                # Alternierende Zeilen
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, self.colors.TABLE_ROW_ALT_BG]),
                
                # ===== SUMMEN-ZEILE =====
                ('BACKGROUND', (0, -1), (-1, -1), self.colors.TABLE_SUM_BG),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 10),
                ('ALIGN', (1, -1), (1, -1), 'RIGHT'),    # "SUMME" rechts
                ('ALIGN', (4, -1), (4, -1), 'RIGHT'),    # CO₂-Wert rechts
                ('TOPPADDING', (0, -1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, -1), (-1, -1), 8),
                ('LEFTPADDING', (0, -1), (-1, -1), 6),
                ('RIGHTPADDING', (0, -1), (-1, -1), 6),
                
                # ===== GRID =====
                ('GRID', (0, 0), (-1, -1), 1, self.colors.TABLE_GRID),
                ('BOX', (0, 0), (-1, -1), 1.5, self.colors.BORDER_BLACK),
                ('LINEBELOW', (0, -2), (-1, -2), 2, self.colors.BORDER_BLACK),  # Linie vor SUMME
            ]))
            
            return table
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Varianten-Tabelle: {e}", exc_info=True)
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
    
    def _get_variant_total(self, variant: Variant) -> float:
        """
        Holt Variantensumme basierend auf Systemgrenze
        
        Args:
            variant: Variante
            
        Returns:
            CO₂-Summe in kg
        """
        boundary = self.project.system_boundary
        
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
