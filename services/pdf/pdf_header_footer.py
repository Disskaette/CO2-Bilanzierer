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
        self.bottom_margin = 2.5*cm

        # Linienposition vorausberechnen (bevor Header gezeichnet wird)
        self.header_line_y = self._precalculate_line_position()
        
        # Top-Margin dynamisch berechnen basierend auf Linienposition
        self.top_margin = self._calculate_top_margin()

    def _precalculate_line_position(self) -> float:
        """
        Berechnet die Y-Position der horizontalen Trennlinie BEVOR der Header gezeichnet wird
        Verwendet die EXAKT GLEICHE Logik wie _draw_header
        
        Returns:
            Y-Position der Linie in Punkten
        """
        top_start = self.page_height - 1.5*cm
        
        # Logo-Höhe berechnen (falls vorhanden)
        logo_height = 0
        if self.config.logo_path and Path(self.config.logo_path).exists():
            try:
                if self.config.logo_path.lower().endswith('.svg'):
                    from svglib.svglib import svg2rlg
                    drawing = svg2rlg(self.config.logo_path)
                    if drawing:
                        orig_width = drawing.width
                        orig_height = drawing.height
                        max_width = 4*cm
                        max_height = 2.5*cm
                        width_scale = max_width / orig_width
                        height_scale = max_height / orig_height
                        scale = min(width_scale, height_scale)
                        actual_height = orig_height * scale
                        logo_height = actual_height
                else:
                    from PIL import Image
                    img = Image.open(self.config.logo_path)
                    orig_width, orig_height = img.size
                    max_width = 4*cm
                    max_height = 2.5*cm
                    width_scale = max_width / orig_width
                    height_scale = max_height / orig_height
                    scale = min(width_scale, height_scale)
                    actual_height = orig_height * scale
                    logo_height = actual_height
            except Exception as e:
                logger.warning(f"Fehler beim Berechnen der Logo-Höhe: {e}")
                logo_height = 0
        
        # Y-Position für Metadaten - GLEICHE Logik wie in _draw_header
        min_y_pos = top_start - 1.3*cm  # Mindestabstand zum Projektnamen
        logo_bottom = top_start - logo_height if logo_height > 0 else top_start
        y_pos = min(min_y_pos, logo_bottom - 0.3*cm)
        
        # Nach der zweiten Metadaten-Zeile (Systemgrenze)
        y_pos -= 0.4*cm
        
        # Linie 0.5cm unter der letzten Metadaten-Zeile
        line_y_pos = y_pos - 0.5*cm
        
        return line_y_pos
    
    def _calculate_top_margin(self) -> float:
        """
        Berechnet den benötigten Top-Margin basierend auf der Logo-Höhe

        Returns:
            Top-Margin in Punkten
        """
        # Basis-Elemente
        top_start = 1.5*cm  # Abstand vom oberen Rand
        min_header_height = 2.5*cm  # Minimale Header-Höhe (ohne Logo)

        # Logo-Höhe berechnen
        logo_height = 0
        if self.config.logo_path and Path(self.config.logo_path).exists():
            try:
                logo_path = Path(self.config.logo_path)
                
                if logo_path.suffix.lower() == '.svg':
                    # SVG
                    from svglib.svglib import svg2rlg
                    drawing = svg2rlg(str(logo_path))
                    if drawing:
                        orig_width = drawing.width
                        orig_height = drawing.height
                        
                        # Berechne skalierte Höhe
                        max_width = 4*cm
                        max_height = 2.5*cm
                        width_scale = max_width / orig_width
                        height_scale = max_height / orig_height
                        scale = min(width_scale, height_scale)
                        logo_height = orig_height * scale
                else:
                    # Raster-Bild
                    from PIL import Image
                    img = Image.open(self.config.logo_path)
                    orig_width, orig_height = img.size
                    
                    # Berechne skalierte Höhe
                    max_width = 4*cm
                    max_height = 2.5*cm
                    width_scale = max_width / orig_width
                    height_scale = max_height / orig_height
                    scale = min(width_scale, height_scale)
                    logo_height = orig_height * scale
            except Exception as e:
                logger.warning(f"Fehler beim Berechnen der Logo-Höhe: {e}")
                logo_height = 0

        # Header-Höhe berechnen
        # Projektname + Metadaten (2 Zeilen) + Abstände
        metadata_height = 1.3*cm + 0.4*cm  # Datum + Systemgrenze

        # Gesamthöhe = top_start + max(logo_height, min_content_height) + Linie + Abstand
        if logo_height > 0:
            header_content = max(logo_height, metadata_height + 0.3*cm)
        else:
            header_content = min_header_height

        total_header = top_start + header_content + \
            0.6*cm  # Reduzierter Abstand zwischen Linie und Content

        return total_header

    def get_heading_position_from_top(self, fixed_distance_below_line: float = 0.5*cm) -> float:
        """
        Berechnet die Y-Position für Überschriften relativ zum oberen Seitenrand
        
        Args:
            fixed_distance_below_line: Fester Abstand unter der Linie (default: 0.5cm)
            
        Returns:
            Abstand vom oberen Seitenrand bis zur Überschrift in Punkten
        """
        # Berechne: page_height - line_y + fixed_distance
        # Das ergibt den Abstand vom oberen Rand bis zur Überschrift
        return self.page_height - self.header_line_y + fixed_distance_below_line

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
            logger.error(
                f"Fehler beim Zeichnen von Header/Footer: {e}", exc_info=True)
        finally:
            canvas.restoreState()

    def _draw_header(self, canvas, doc):
        """Zeichnet Header"""
        # Startposition oben (für Logo und Projektname gleich)
        top_start = self.page_height - 1.5*cm

        # ===== LOGO =====
        logo_height = 0
        if self.config.logo_path and Path(self.config.logo_path).exists():
            try:
                logo_path = Path(self.config.logo_path)
                
                # Prüfe ob SVG
                if logo_path.suffix.lower() == '.svg':
                    # SVG mit svglib/reportlab
                    from svglib.svglib import svg2rlg
                    from reportlab.graphics import renderPDF
                    
                    # Lade SVG
                    drawing = svg2rlg(str(logo_path))
                    if drawing:
                        # Originalgröße
                        orig_width = drawing.width
                        orig_height = drawing.height
                        
                        # Skalierung berechnen
                        max_width = 4*cm
                        max_height = 2.5*cm
                        width_scale = max_width / orig_width
                        height_scale = max_height / orig_height
                        scale = min(width_scale, height_scale)
                        
                        # Skalieren
                        actual_width = orig_width * scale
                        actual_height = orig_height * scale
                        logo_height = actual_height
                        
                        # Zeichne SVG
                        drawing.width = actual_width
                        drawing.height = actual_height
                        drawing.scale(scale, scale)
                        
                        renderPDF.draw(
                            drawing,
                            canvas,
                            self.left_margin,
                            top_start - actual_height
                        )
                    else:
                        logger.warning(f"SVG konnte nicht geladen werden: {logo_path}")
                        logo_height = 0
                else:
                    # Raster-Bild (PNG, JPG, etc.)
                    from PIL import Image
                    
                    # Lade das Bild, um die Originalabmessungen zu ermitteln
                    img = Image.open(self.config.logo_path)
                    orig_width, orig_height = img.size
                    
                    # Berechne die Zielabmessungen unter Beibehaltung des Seitenverhältnisses
                    max_width = 4*cm
                    max_height = 2.5*cm  # Maximal erlaubte Höhe
                    
                    # Berechne Skalierungsfaktor
                    width_scale = max_width / orig_width
                    height_scale = max_height / orig_height
                    scale = min(width_scale, height_scale)
                    
                    # Tatsächliche Dimensionen
                    actual_width = orig_width * scale
                    actual_height = orig_height * scale
                    logo_height = actual_height
                    
                    # Zeichne das Logo - Ankerpunkt oben links
                    # y-Position: von top_start nach unten
                    canvas.drawImage(
                        self.config.logo_path,
                        self.left_margin,
                        top_start - actual_height,  # Logo wächst nach unten
                        width=actual_width,
                        height=actual_height,
                        preserveAspectRatio=True,
                        mask='auto'
                    )
            except Exception as e:
                logger.warning(f"Logo konnte nicht gezeichnet werden: {e}")
                logger.exception(e)
                logo_height = 0

        # ===== PROJEKTNAME =====
        # Rechts oben, blau, fett - Ankerpunkt oben rechts
        canvas.setFont('Helvetica-Bold', 16)
        canvas.setFillColor(colors.black)
        canvas.drawRightString(
            self.page_width - self.right_margin,
            top_start - 0.3*cm,  # Leicht nach unten versetzt für optische Ausrichtung
            self.project.name
        )

        # ===== METADATEN =====
        # Datum und Systemgrenze rechts
        # Position abhängig von Logo-Höhe oder mindestens 1.5cm unter Projektname
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.grey)

        # Berechne Start-Position für Metadaten
        # Entweder unter dem Logo oder mindestens 1.0cm unter dem Projektnamen
        min_y_pos = top_start - 1.3*cm  # Mindestabstand zum Projektnamen
        logo_bottom = top_start - logo_height if logo_height > 0 else top_start
        y_pos = min(min_y_pos, logo_bottom - 0.3*cm)

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
        # Positioniere die Linie unter den Metadaten mit ausreichend Abstand
        line_y_pos = y_pos - 0.5*cm  # 0.5cm Abstand unter der letzten Metadaten-Zeile
        
        # Speichere Position für spätere Verwendung
        self.header_line_y = line_y_pos

        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(1)
        canvas.line(
            self.left_margin,
            line_y_pos,
            self.page_width - self.right_margin,
            line_y_pos
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
