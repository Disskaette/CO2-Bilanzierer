"""
Material-Datenmodell - repräsentiert eine CSV-Zeile / EPD
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class Material:
    """
    Repräsentiert ein Material aus der CSV/ÖKOBAUDAT-Datenbank
    Orientiert an DIN EN 15804+A2 und ÖKOBAUDAT-Struktur
    """
    
    # Identifikation
    id: str  # Eindeutige ID aus CSV
    name: str  # Materialbezeichnung
    
    # Klassifikation
    dataset_type: str = "generisch"  # generisch, spezifisch, durchschnitt, repräsentativ
    source: str = ""  # Hersteller/Quelle
    conformity: str = ""  # Konformität (z.B. 'DIN EN 15804+A2' / 'ISO 14025')
    
    # Einheit
    unit: str = "kg"  # Bezugseinheit aus CSV
    
    # Umweltindikatoren (GWP = Global Warming Potential)
    # Werte in kg CO₂-Äq. pro Einheit
    gwp_a1a3: float = 0.0  # Herstellung (A1-A3)
    gwp_c3: float = 0.0    # Entsorgung (C3)
    gwp_c4: float = 0.0    # Deponie/Recycling (C4)
    gwp_d: Optional[float] = None  # Gutschriften (D) - kann fehlen
    
    # Biogener Kohlenstoff (für Holz/Biobasierte Materialien)
    biogenic_carbon: Optional[float] = None  # Biogene CO2-Speicherung in kg CO₂/Einheit
    
    # Erweiterbar für weitere Indikatoren (EN 15804+A2)
    additional_indicators: Dict[str, float] = field(default_factory=dict)
    
    # Metadaten
    csv_row_index: int = -1  # Zeilenindex in CSV
    raw_data: Dict[str, Any] = field(default_factory=dict)  # Vollständige CSV-Zeile
    is_custom: bool = False  # True = eigenes Material, False = ÖKOBAUDAT
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialisierung für JSON-Speicherung"""
        return {
            'id': self.id,
            'name': self.name,
            'dataset_type': self.dataset_type,
            'source': self.source,
            'conformity': self.conformity,
            'unit': self.unit,
            'gwp_a1a3': self.gwp_a1a3,
            'gwp_c3': self.gwp_c3,
            'gwp_c4': self.gwp_c4,
            'gwp_d': self.gwp_d,
            'biogenic_carbon': self.biogenic_carbon,
            'additional_indicators': self.additional_indicators,
            'csv_row_index': self.csv_row_index,
            'raw_data': self.raw_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Material':
        """Deserialisierung aus JSON"""
        return cls(**data)
    
    def has_c_modules(self) -> bool:
        """Prüft ob C3/C4 Module vorhanden sind"""
        return self.gwp_c3 != 0.0 or self.gwp_c4 != 0.0
    
    def has_d_module(self) -> bool:
        """Prüft ob D-Modul vorhanden ist"""
        return self.gwp_d is not None and self.gwp_d != 0.0
    
    def has_biogenic_carbon(self) -> bool:
        """Prüft ob biogene Speicherung vorhanden ist"""
        return self.biogenic_carbon is not None and self.biogenic_carbon != 0.0
    
    def is_en15804_a2(self) -> bool:
        """Prüft ob Material nach EN 15804+A2 deklariert ist"""
        if not self.conformity:
            return False
        return "15804+A2" in self.conformity
