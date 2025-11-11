"""
Konfigurationsklassen für PDF-Export

Definiert die Datenstrukturen für:
- Info-Blöcke (Methodik, Projektbeschreibung, etc.)
- Export-Konfiguration (was soll exportiert werden)
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class InfoBlock:
    """
    Info-Block für das PDF (z.B. Methodik, Projektbeschreibung)

    Attributes:
        id: Eindeutige ID des Blocks (z.B. "methodik", "projektbeschreibung")
        title: Überschrift des Blocks
        text: Fließtext-Inhalt
        image_path: Optionaler Pfad zu einem Bild
        include: Ob dieser Block exportiert werden soll
    """
    id: str
    title: str
    text: str
    image_path: Optional[str] = None
    include: bool = True

    def copy(self) -> 'InfoBlock':
        """Erstellt eine Kopie des Info-Blocks"""
        return InfoBlock(
            id=self.id,
            title=self.title,
            text=self.text,
            image_path=self.image_path,
            include=self.include
        )


@dataclass
class ExportConfig:
    """
    Konfiguration für den PDF-Export

    Definiert alle Optionen, die im Export-Dialog ausgewählt werden können.
    """

    # ===== LOGO =====
    logo_path: Optional[str] = None

    # ===== DASHBOARD =====
    include_dashboard: bool = True
    include_dashboard_chart: bool = True
    include_dashboard_table: bool = True

    # ===== VARIANTEN =====
    # Liste der Varianten-Indizes, die exportiert werden sollen
    include_variants: List[int] = field(default_factory=list)
    include_variant_charts: bool = True
    include_variant_tables: bool = True

    # ===== KOMMENTARE =====
    # Dictionary: variant_index -> Kommentar-Text
    # Kommentare werden als Text-Block unter der Varianten-Überschrift eingefügt
    comments: Dict[int, str] = field(default_factory=dict)

    # ===== INFO-BLÖCKE =====
    # Liste von Info-Blöcken (Methodik, Projektbeschreibung, etc.)
    # Diese werden am Anfang oder Ende des PDFs eingefügt
    info_blocks: List[InfoBlock] = field(default_factory=list)

    # ===== ZUSATZBILD =====
    # Optionales Bild am Ende des PDFs
    additional_image_path: Optional[str] = None

    # ===== FOOTER-TEXT =====
    # Disclaimer/Hinweis in der Fußzeile
    disclaimer: str = "Berechnungen auf Basis von DIN EN 15804+A2 und ISO 14025. Ergebnisse dienen als grobe Einschätzung."

    def get_selected_variant_count(self) -> int:
        """Gibt Anzahl der ausgewählten Varianten zurück"""
        return len(self.include_variants)

    def is_variant_selected(self, index: int) -> bool:
        """Prüft, ob eine Variante ausgewählt ist"""
        return index in self.include_variants

    def add_info_block(self, info_block: InfoBlock):
        """Fügt einen Info-Block hinzu"""
        # Prüfe, ob Block mit dieser ID bereits existiert
        existing = next(
            (ib for ib in self.info_blocks if ib.id == info_block.id), None)
        if existing:
            # Ersetze bestehenden Block
            idx = self.info_blocks.index(existing)
            self.info_blocks[idx] = info_block
        else:
            # Füge neuen Block hinzu
            self.info_blocks.append(info_block)

    def remove_info_block(self, block_id: str):
        """Entfernt einen Info-Block"""
        self.info_blocks = [ib for ib in self.info_blocks if ib.id != block_id]

    def get_info_block(self, block_id: str) -> Optional[InfoBlock]:
        """Holt einen Info-Block nach ID"""
        return next((ib for ib in self.info_blocks if ib.id == block_id), None)


# ===== VORDEFINIERTE INFO-BLÖCKE =====
# Diese können in der Anwendung verwendet werden

PREDEFINED_INFO_BLOCKS = {
    "methodik": InfoBlock(
        id="methodik",
        title="Methodik",
        text=(
            "Die CO2-Bilanzierung erfolgt nach DIN EN 15804+A2 und ISO 14025. "
            "Es werden die Phasen A1-A3 (Herstellung), C3-C4 (Entsorgung) und D (Gutschriften) berücksichtigt. "
            "Die Berechnung basiert auf den GWP-Werten (Global Warming Potential) der verwendeten Materialien. "
            "Datengrundlage ist die ÖKOBAUDAT-Datenbank sowie eigene EPDs."
        ),
        image_path=None,
        include=False  # Standardmäßig nicht inkludiert
    ),

    "projektbeschreibung": InfoBlock(
        id="projektbeschreibung",
        title="Projektbeschreibung",
        text=(
            "Dieses Dokument enthaelt die CO2-Bilanzierung fuer das Projekt. "
            "Es werden verschiedene Bauwerksvarianten oder Bauwerke verglichen und die Materialzusammensetzung analysiert. "
            "Ziel ist es, eine grobe Einschätzung der umweltfreundlichsten Variante zu identifizieren."
        ),
        image_path=None,
        include=False
    ),

    "ergebnisse": InfoBlock(
        id="ergebnisse",
        title="Zusammenfassung der Ergebnisse",
        text=(
            "Die Ergebnisse zeigen die CO2-Emissionen der verschiedenen Bauwerksvarianten oder Bauwerke. "
            "Die Variante mit den geringsten Emissionen sollte bevorzugt werden, "
            "sofern keine anderen Faktoren dagegen sprechen."
            "Jedoch sollte ebenfalls auf Ausführbarkeit und Kosten geachtet werden."
        ),
        image_path=None,
        include=False
    )
}


def create_default_config() -> ExportConfig:
    """
    Erstellt eine Standard-Konfiguration

    Returns:
        ExportConfig mit sinnvollen Defaults
    """
    config = ExportConfig(
        include_dashboard=True,
        include_dashboard_chart=True,
        include_dashboard_table=True,
        include_variant_charts=True,
        include_variant_tables=True
    )

    return config
