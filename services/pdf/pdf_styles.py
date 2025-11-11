"""
Style-Definitionen für PDF-Export

Definiert alle Text-Styles für das PDF (Überschriften, Fließtext, Tabellen, etc.)
im Stil des Excel-Tools mit gelben Section-Headings und professioneller Formatierung.
"""

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY


class PDFStyles:
    """Container für alle PDF-Styles"""

    def __init__(self):
        """Initialisiert alle Styles"""
        # Basis-Styles von ReportLab
        self.base_styles = getSampleStyleSheet()
        self.base_styles['Heading1'].textColor = colors.black
        self.base_styles['Heading1'].fontName = 'Helvetica-Bold'

        # Custom Styles hinzufügen
        self._create_custom_styles()

    def _create_custom_styles(self):
        """Erstellt alle Custom-Styles"""

        # Hilfsfunktion: Style nur hinzufügen, wenn er nicht existiert
        def add_style_if_not_exists(style):
            if style.name not in self.base_styles:
                self.base_styles.add(style)

        # ===== PROJEKT-TITEL =====
        # Großer Titel für den Projektnamen (blau, fett)
        add_style_if_not_exists(ParagraphStyle(
            name='ProjectTitle',
            parent=self.base_styles['Heading1'],
            fontSize=20,
            textColor=colors.black,
            spaceAfter=6,
            spaceBefore=0,
            fontName='Helvetica-Bold',
            alignment=TA_LEFT
        ))

        # ===== SEKTIONS-ÜBERSCHRIFT =====
        # Gelber Balken wie im Excel-Tool
        add_style_if_not_exists(ParagraphStyle(
            name='SectionHeading',
            parent=self.base_styles['Heading2'],
            fontSize=14,
            textColor=colors.black,
            fontName='Helvetica-Bold',
            spaceBefore=12,
            spaceAfter=6,
            # backColor=colors.HexColor('#FFFFCC'),  # Hellgelb
            # borderWidth=2,
            # borderColor=colors.HexColor('#FFD700'),  # Gold
            # borderPadding=5,
            leftIndent=0,
            rightIndent=0
        ))

        # ===== UNTER-ÜBERSCHRIFT =====
        # Für Unter-Sektionen (kleiner, kein gelber Balken)
        add_style_if_not_exists(ParagraphStyle(
            name='SubHeading',
            parent=self.base_styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#1f6aa5'),
            fontName='Helvetica-Bold',
            spaceBefore=8,
            spaceAfter=4,
            alignment=TA_LEFT
        ))

        # ===== NORMALER TEXT =====
        # Fließtext für Beschreibungen
        add_style_if_not_exists(ParagraphStyle(
            name='BodyText',
            parent=self.base_styles['Normal'],
            fontSize=10,
            fontName='Helvetica',
            spaceBefore=3,
            spaceAfter=3,
            alignment=TA_JUSTIFY,
            leading=14  # Zeilenabstand
        ))

        # ===== KOMMENTAR =====
        # Spezial-Box für Kommentare (kursiv, grau hinterlegt, Rahmen)
        add_style_if_not_exists(ParagraphStyle(
            name='Comment',
            parent=self.base_styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Oblique',
            textColor=colors.HexColor('#666666'),
            spaceBefore=6,
            spaceAfter=6,
            leftIndent=10,
            rightIndent=10,
            borderWidth=0.5,
            borderColor=colors.HexColor('#CCCCCC'),
            borderPadding=8,
            backColor=colors.HexColor('#F5F5F5'),  # Hellgrau
            leading=12
        ))

        # ===== METADATEN =====
        # Kleine graue Schrift für Datum, Systemgrenze, etc.
        add_style_if_not_exists(ParagraphStyle(
            name='Metadata',
            parent=self.base_styles['Normal'],
            fontSize=9,
            fontName='Helvetica',
            textColor=colors.grey,
            spaceBefore=2,
            spaceAfter=2
        ))

        # ===== DISCLAIMER =====
        # Sehr kleine Schrift für Footer-Disclaimer
        add_style_if_not_exists(ParagraphStyle(
            name='Disclaimer',
            parent=self.base_styles['Normal'],
            fontSize=7,
            fontName='Helvetica',
            textColor=colors.grey,
            alignment=TA_LEFT,
            leading=9
        ))

        # ===== AUFZÄHLUNG =====
        # Für Listen
        add_style_if_not_exists(ParagraphStyle(
            name='BulletList',
            parent=self.base_styles['Normal'],
            fontSize=10,
            fontName='Helvetica',
            leftIndent=20,
            spaceBefore=2,
            spaceAfter=2,
            bulletIndent=10
        ))

    def get(self, style_name: str) -> ParagraphStyle:
        """
        Holt einen Style nach Namen

        Args:
            style_name: Name des Styles

        Returns:
            ParagraphStyle
        """
        return self.base_styles[style_name]

    @property
    def project_title(self) -> ParagraphStyle:
        """Projekt-Titel Style"""
        return self.get('ProjectTitle')

    @property
    def section_heading(self) -> ParagraphStyle:
        """Sektions-Überschrift Style (gelber Balken)"""
        return self.get('SectionHeading')

    @property
    def sub_heading(self) -> ParagraphStyle:
        """Unter-Überschrift Style"""
        return self.get('SubHeading')

    @property
    def body_text(self) -> ParagraphStyle:
        """Fließtext Style"""
        return self.get('BodyText')

    @property
    def comment(self) -> ParagraphStyle:
        """Kommentar Style"""
        return self.get('Comment')

    @property
    def metadata(self) -> ParagraphStyle:
        """Metadaten Style"""
        return self.get('Metadata')

    @property
    def disclaimer(self) -> ParagraphStyle:
        """Disclaimer Style"""
        return self.get('Disclaimer')

    @property
    def bullet_list(self) -> ParagraphStyle:
        """Aufzählungs-Liste Style"""
        return self.get('BulletList')


# ===== FARB-DEFINITIONEN =====
# Zentrale Farb-Palette für konsistentes Design

class PDFColors:
    """Zentrale Farb-Definitionen"""

    # Primärfarben
    PRIMARY_BLUE = colors.HexColor('#1f6aa5')
    PRIMARY_YELLOW = colors.HexColor('#FFD700')

    # Hintergrundfarben
    BG_LIGHT_YELLOW = colors.HexColor('#FFFFCC')
    BG_LIGHT_GRAY = colors.HexColor('#F5F5F5')
    BG_GRAY = colors.HexColor('#E0E0E0')
    BG_DARK_GRAY = colors.HexColor('#D9D9D9')

    # Textfarben
    TEXT_BLACK = colors.black
    TEXT_WHITE = colors.whitesmoke
    TEXT_GRAY = colors.grey
    TEXT_DARK_GRAY = colors.HexColor('#666666')

    # Rahmen/Linien
    BORDER_GRAY = colors.HexColor('#CCCCCC')
    BORDER_BLACK = colors.black

    # Tabellen-Farben
    TABLE_HEADER_BG = colors.HexColor('#D9D9D9')  # Grau
    TABLE_HEADER_TEXT = colors.black
    TABLE_ROW_ALT_BG = colors.HexColor('#F5F5F5')  # Hellgrau (alternierend)
    TABLE_SUM_BG = colors.HexColor('#E0E0E0')  # Grau für SUMMEN-Zeile
    TABLE_GRID = colors.black


def get_styles() -> PDFStyles:
    """
    Factory-Funktion: Erstellt und gibt PDFStyles-Instanz zurück

    Returns:
        PDFStyles-Instanz mit allen Styles
    """
    return PDFStyles()
