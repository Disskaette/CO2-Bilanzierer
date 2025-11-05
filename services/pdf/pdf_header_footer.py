"""
Header und Footer für PDF-Export

Zeichnet professionellen Header und Footer auf jeder Seite:

HEADER:
- Logo (oben links)
- Projektname (oben rechts, blau)
- Metadaten: Datum, Systemgrenze (rechts)
- Trennlinie

FOOTER:
- Seitenzahl (rechts)
- Disclaimer (links, mehrzeilig)
- Trennlinie
"""

import logging
from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth

from models.project import Project
from services.pdf.pdf_config import ExportConfig

logger = logging.getLogger(__name__)


class PDFHeaderFooter:
    """Zeichnet Header und Footer auf PDF-Seiten"""
    
    def __init__(self, project: Project, config: ExportConfig):
        """
        Initialisiert Header/Footer-Renderer
        
        Args:
            project: Projekt-Daten
            config: Export-Konfiguration
        """
        self.project = project
        self.config = config
        
        # Layout-Konstanten
        self.page_width = A4[0]
        self.page_height = A4[1]
        self.left_margin = 2*cm
        self.right_margin = 2*cm
        self.top_margin = 4*cm
        self.bottom_margin = 2.5*cm
    
    def draw_header_footer(self, canvas, doc):
        """
        Callback-Funktion für PageTemplate
        
        Args:
            canvas: ReportLab Canvas
            doc: Document
        """
        canvas.saveState()
        
        try:
            self._draw_header(canvas, doc)
            self._draw_footer(canvas, doc)
        except Exception as e:
            logger.error(f"Fehler beim Zeichnen von Header/Footer: {e}", exc_info=True)
        finally:
            canvas.restoreState()
    
    def _draw_header(self, canvas, doc):
        """Zeichnet Header"""
        # ===== LOGO =====
        if self.config.logo_path and Path(self.config.logo_path).exists():
            try:
                canvas.drawImage(
                    self.config.logo_path,
                    self.left_margin,
                    self.page_height - 3.5*cm,  # Von oben
                    width=4*cm,
                    height=2*cm,
                    preserveAspectRatio=True,
                    mask='auto'
                )
            except Exception as e:
                logger.warning(f"Logo konnte nicht gezeichnet werden: {e}")
        
        # ===== PROJEKTNAME =====
        # Rechts oben, blau, fett
        canvas.setFont('Helvetica-Bold', 16)
        canvas.setFillColor(colors.HexColor('#1f6aa5'))
        canvas.drawRightString(
            self.page_width - self.right_margin,
            self.page_height - 2*cm,
            self.project.name
        )
        
        # ===== METADATEN =====
        # Datum und Systemgrenze rechts
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.grey)
        
        y_pos = self.page_height - 2.7*cm
        canvas.drawRightString(
            self.page_width - self.right_margin,
            y_pos,
            f"Datum: {datetime.now().strftime('%d.%m.%Y')}"
        )
        
        y_pos -= 0.4*cm
        canvas.drawRightString(
            self.page_width - self.right_margin,
            y_pos,
            f"Systemgrenze: {self.project.system_boundary}"
        )
        
        # ===== TRENNLINIE =====
        canvas.setStrokeColor(colors.HexColor('#1f6aa5'))
        canvas.setLineWidth(1)
        canvas.line(
            self.left_margin,
            self.page_height - 3.7*cm,
            self.page_width - self.right_margin,
            self.page_height - 3.7*cm
        )
    
    def _draw_footer(self, canvas, doc):
        """Zeichnet Footer"""
        # ===== TRENNLINIE =====
        canvas.setStrokeColor(colors.grey)
        canvas.setLineWidth(0.5)
        canvas.line(
            self.left_margin,
            2.3*cm,
            self.page_width - self.right_margin,
            2.3*cm
        )
        
        # ===== SEITENZAHL =====
        # Rechts
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.black)
        page_num = canvas.getPageNumber()
        canvas.drawRightString(
            self.page_width - self.right_margin,
            1.8*cm,
            f"Seite {page_num}"
        )
        
        # ===== DISCLAIMER =====
        # Links, klein, mehrzeilig
        if self.config.disclaimer:
            canvas.setFont('Helvetica', 7)
            canvas.setFillColor(colors.grey)
            
            # Text umbrechen (max. 12 cm breit)
            max_width = 12*cm
            lines = self._wrap_text(
                self.config.disclaimer,
                'Helvetica',
                7,
                max_width
            )
            
            # Zeichne Zeilen von unten nach oben
            y_start = 1.8*cm
            for line in lines:
                canvas.drawString(self.left_margin, y_start, line)
                y_start -= 0.3*cm
    
    def _wrap_text(self, text: str, font_name: str, font_size: int, max_width: float) -> list:
        """
        Umbrechen von Text in mehrere Zeilen
        
        Args:
            text: Text
            font_name: Font-Name
            font_size: Font-Größe
            max_width: Maximale Breite in Punkten
            
        Returns:
            Liste von Zeilen
        """
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if stringWidth(test_line, font_name, font_size) <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
