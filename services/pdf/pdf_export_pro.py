"""
Hauptklasse für professionellen PDF-Export

Orchestriert den gesamten Export-Prozess:
1. Initialisiert alle Sub-Module (Charts, Tables, Header/Footer, Styles)
2. Erstellt BaseDocTemplate mit PageTemplate
3. Baut Story aus Sektionen (Dashboard, Varianten, Info-Blöcke)
4. Generiert finales PDF

Verwendung:
    from services.pdf import PDFExporterPro, ExportConfig
    
    config = ExportConfig(...)
    exporter = PDFExporterPro()
    success = exporter.export(project, config, "output.pdf")
"""

import logging
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Spacer, PageBreak
)

from models.project import Project
from services.pdf.pdf_config import ExportConfig, InfoBlock
from services.pdf.pdf_styles import get_styles
from services.pdf.pdf_charts import PDFChartCreator
from services.pdf.pdf_tables import PDFTableCreator
from services.pdf.pdf_header_footer import PDFHeaderFooter

logger = logging.getLogger(__name__)


class PDFExporterPro:
    """
    Professioneller PDF-Exporter
    
    Erstellt hochwertige PDF-Reports im Stil des Excel-Tools.
    """
    
    def __init__(self):
        """Initialisiert den Exporter"""
        self.project = None
        self.config = None
        self.styles = None
        self.chart_creator = None
        self.table_creator = None
        self.header_footer = None
    
    def export(
        self,
        project: Project,
        config: ExportConfig,
        output_path: str,
        dashboard_figure=None,
        variant_figures: dict = None
    ) -> bool:
        """
        Exportiert Projekt als PDF
        
        Args:
            project: Projekt-Daten
            config: Export-Konfiguration
            output_path: Zieldatei-Pfad
            dashboard_figure: Bestehende Dashboard-Figure (optional)
            variant_figures: Dict {variant_idx: Figure} (optional)
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        if variant_figures is None:
            variant_figures = {}
        try:
            logger.info(f"Starte professionellen PDF-Export: {output_path}")
            
            # Initialisierung
            self.project = project
            self.config = config
            self.dashboard_figure = dashboard_figure
            self.variant_figures = variant_figures
            self.styles = get_styles()
            self.chart_creator = PDFChartCreator(project)
            self.table_creator = PDFTableCreator(project)
            self.header_footer = PDFHeaderFooter(project, config)
            
            # BaseDocTemplate erstellen
            doc = BaseDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=4*cm,      # Mehr Platz für Header
                bottomMargin=2.5*cm  # Mehr Platz für Footer
            )
            
            # Frame für Inhalt
            frame = Frame(
                doc.leftMargin,
                doc.bottomMargin,
                doc.width,
                doc.height,
                id='normal'
            )
            
            # PageTemplate mit Header/Footer-Callback
            template = PageTemplate(
                id='MainTemplate',
                frames=[frame],
                onPage=self.header_footer.draw_header_footer
            )
            
            doc.addPageTemplates([template])
            
            # Story erstellen
            story = self._build_story()
            
            # PDF bauen
            doc.build(story)
            
            logger.info(f"PDF erfolgreich erstellt: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"PDF-Export Fehler: {e}", exc_info=True)
            return False
    
    def _build_story(self) -> list:
        """
        Erstellt die Story (Inhalt) des PDFs
        
        Returns:
            Liste von Flowables
        """
        story = []
        
        # ===== UNTERTITEL =====
        story.append(Paragraph(
            "CO2-Bilanzierung Variantenvergleich",
            self.styles.section_heading
        ))
        story.append(Spacer(1, 0.5*cm))
        
        # ===== INFO-BLÖCKE AM ANFANG =====
        # Nur Methodik kommt am Anfang
        for info_block in self.config.info_blocks:
            if info_block.include and info_block.id == "methodik":
                story.extend(self._build_info_block(info_block))
        
        # ===== DASHBOARD =====
        if self.config.include_dashboard:
            story.extend(self._build_dashboard_section())
        
        # ===== VARIANTEN =====
        for variant_idx in self.config.include_variants:
            if variant_idx < len(self.project.variants):
                story.extend(self._build_variant_section(variant_idx))
        
        # ===== INFO-BLÖCKE AM ENDE =====
        # Alle außer Methodik kommen ans Ende
        for info_block in self.config.info_blocks:
            if info_block.include and info_block.id != "methodik":
                story.extend(self._build_info_block(info_block))
        
        # ===== ZUSATZBILD =====
        if self.config.additional_image_path:
            if Path(self.config.additional_image_path).exists():
                story.extend(self._build_additional_image())
        
        return story
    
    def _build_dashboard_section(self) -> list:
        """Erstellt Dashboard-Sektion"""
        elements = []
        
        # Überschrift
        elements.append(Paragraph("Variantenvergleich", self.styles.section_heading))
        elements.append(Spacer(1, 0.3*cm))
        
        # Diagramm
        if self.config.include_dashboard_chart:
            # Verwende bestehende Figure wenn vorhanden, sonst neu erstellen
            if self.dashboard_figure:
                chart = self.chart_creator.figure_to_image(self.dashboard_figure, width_cm=16, height_cm=11)
                logger.info("Verwende bestehende Dashboard-Figure")
            else:
                chart = self.chart_creator.create_dashboard_chart(
                    self.config.include_variants
                )
                logger.info("Erstelle neue Dashboard-Figure")
            
            if chart:
                elements.append(chart)
                elements.append(Spacer(1, 0.5*cm))
        
        # Tabelle
        if self.config.include_dashboard_table:
            table = self.table_creator.create_dashboard_table(
                self.config.include_variants
            )
            if table:
                elements.append(table)
                elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _build_variant_section(self, variant_idx: int) -> list:
        """Erstellt Varianten-Sektion"""
        elements = []
        variant = self.project.variants[variant_idx]
        
        # Seitenumbruch vor jeder Variante
        elements.append(PageBreak())
        
        # Überschrift
        elements.append(Paragraph(variant.name, self.styles.section_heading))
        elements.append(Spacer(1, 0.3*cm))
        
        # Kommentar (falls vorhanden)
        if variant_idx in self.config.comments and self.config.comments[variant_idx]:
            comment_text = f"<b>Kommentar:</b><br/>{self.config.comments[variant_idx]}"
            comment = Paragraph(comment_text, self.styles.comment)
            elements.append(comment)
            elements.append(Spacer(1, 0.3*cm))
        
        # Diagramm (ALLE müssen exakt gleiche Größe haben)
        if self.config.include_variant_charts:
            # Verwende bestehende Figure wenn vorhanden, sonst neu erstellen
            # WICHTIG: Beide Pfade müssen exakt gleiche Größe verwenden!
            CHART_WIDTH = 14
            CHART_HEIGHT = 9
            
            if variant_idx in self.variant_figures:
                chart = self.chart_creator.figure_to_image(
                    self.variant_figures[variant_idx], 
                    width_cm=CHART_WIDTH, 
                    height_cm=CHART_HEIGHT
                )
                logger.info(f"Verwende bestehende Figure für Variante {variant_idx}")
            else:
                chart = self.chart_creator.create_variant_chart(
                    variant, 
                    width_cm=CHART_WIDTH, 
                    height_cm=CHART_HEIGHT
                )
                logger.info(f"Erstelle neue Figure für Variante {variant_idx}")
            
            if chart:
                elements.append(chart)
                elements.append(Spacer(1, 0.5*cm))
        
        # Tabelle
        if self.config.include_variant_tables:
            table = self.table_creator.create_variant_table(variant)
            if table:
                elements.append(table)
                elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _build_info_block(self, info_block: InfoBlock) -> list:
        """Erstellt Info-Block"""
        elements = []
        
        elements.append(PageBreak())
        
        # Überschrift
        elements.append(Paragraph(info_block.title, self.styles.section_heading))
        elements.append(Spacer(1, 0.3*cm))
        
        # Text
        if info_block.text:
            # Paragraph unterstützt <br/> für Zeilenumbrüche
            text = info_block.text.replace('\n', '<br/>')
            elements.append(Paragraph(text, self.styles.body_text))
            elements.append(Spacer(1, 0.3*cm))
        
        # Bild
        if info_block.image_path and Path(info_block.image_path).exists():
            try:
                from reportlab.platypus import Image as RLImage
                img = RLImage(info_block.image_path, width=12*cm, height=8*cm)
                elements.append(img)
                elements.append(Spacer(1, 0.3*cm))
            except Exception as e:
                logger.warning(f"Info-Block Bild konnte nicht geladen werden: {e}")
        
        return elements
    
    def _build_additional_image(self) -> list:
        """Erstellt Zusatzbild-Sektion"""
        elements = []
        
        elements.append(PageBreak())
        elements.append(Paragraph("Weitere Informationen", self.styles.section_heading))
        elements.append(Spacer(1, 0.3*cm))
        
        try:
            from reportlab.platypus import Image as RLImage
            img = RLImage(self.config.additional_image_path, width=15*cm, height=10*cm)
            elements.append(img)
        except Exception as e:
            logger.warning(f"Zusatzbild konnte nicht geladen werden: {e}")
        
        return elements
