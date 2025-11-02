"""
Projekt-Datenmodell - Hauptcontainer für Bauwerksvarianten
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from .variant import Variant


@dataclass
class Project:
    """
    Hauptprojekt mit mehreren Bauwerksvarianten
    Speichert auch Metadaten zur verwendeten CSV und UI-Zustand
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Neues Projekt"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Varianten (max. 5 für Tabs 2-6)
    variants: List[Variant] = field(default_factory=list)
    
    # CSV-Metadaten
    last_csv_path: Optional[str] = None
    csv_loaded_at: Optional[str] = None
    csv_separator: str = ";"
    csv_decimal: str = ","
    
    # UI-Zustand
    last_open_tabs: List[int] = field(default_factory=lambda: [0])  # Tab-Indices
    active_tab: int = 0
    system_boundary: str = "A1-A3"  # Systemgrenze: siehe BOUNDARY_OPTIONS
    use_biogenic: bool = False  # True = mit biogener Speicherung, False = EN 15804+A2
    visible_variants: List[bool] = field(default_factory=lambda: [True] * 5)
    
    # Dateibaum-Struktur (optional, für spätere Erweiterung)
    file_tree: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialisierung für JSON-Speicherung"""
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'variants': [v.to_dict() for v in self.variants],
            'last_csv_path': self.last_csv_path,
            'csv_loaded_at': self.csv_loaded_at,
            'csv_separator': self.csv_separator,
            'csv_decimal': self.csv_decimal,
            'last_open_tabs': self.last_open_tabs,
            'active_tab': self.active_tab,
            'system_boundary': self.system_boundary,
            'use_biogenic': self.use_biogenic,
            'visible_variants': self.visible_variants,
            'file_tree': self.file_tree
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Deserialisierung aus JSON"""
        variants_data = data.pop('variants', [])
        project = cls(**data)
        project.variants = [Variant.from_dict(v) for v in variants_data]
        return project
    
    def add_variant(self, variant: Variant) -> bool:
        """Fügt Variante hinzu, max. 5"""
        if len(self.variants) >= 5:
            return False
        self.variants.append(variant)
        self.updated_at = datetime.now().isoformat()
        return True
    
    def remove_variant(self, variant_id: str) -> None:
        """Entfernt Variante"""
        self.variants = [v for v in self.variants if v.id != variant_id]
        self.updated_at = datetime.now().isoformat()
    
    def get_variant(self, index: int) -> Optional[Variant]:
        """Holt Variante nach Index"""
        if 0 <= index < len(self.variants):
            return self.variants[index]
        return None
    
    def update_timestamp(self) -> None:
        """Aktualisiert Zeitstempel"""
        self.updated_at = datetime.now().isoformat()
