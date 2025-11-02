"""
Varianten-Datenmodell - repräsentiert eine Bauwerksvariante mit Materialzeilen
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


@dataclass
class MaterialRow:
    """
    Eine Zeile in einer Bauwerksvariante
    Verknüpft Material mit Menge und berechneten Werten
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    position: int = 0  # Sortierungsposition
    
    # Material-Referenz
    material_id: Optional[str] = None
    material_name: str = "Nicht ausgewählt"
    
    # Materialdaten (Kopie zur Sicherheit bei CSV-Wechsel)
    material_unit: str = ""
    material_gwp_a1a3: float = 0.0
    material_gwp_c3: float = 0.0
    material_gwp_c4: float = 0.0
    material_gwp_d: Optional[float] = None
    material_source: str = ""
    material_dataset_type: str = ""
    
    # Mengenangabe
    quantity: float = 0.0
    
    # Berechnete Werte (werden bei Änderung neu berechnet)
    result_a: float = 0.0      # quantity × gwp_a1a3
    result_ac: float = 0.0     # quantity × (gwp_a1a3 + gwp_c3 + gwp_c4)
    result_acd: Optional[float] = None  # result_ac + quantity × gwp_d
    
    # Bio-korrigierte Werte (mit biogener Speicherung)
    result_a_bio: Optional[float] = None
    result_ac_bio: Optional[float] = None
    result_acd_bio: Optional[float] = None
    
    # Flags
    c_modules_missing: bool = False
    d_module_missing: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialisierung"""
        return {
            'id': self.id,
            'position': self.position,
            'material_id': self.material_id,
            'material_name': self.material_name,
            'material_unit': self.material_unit,
            'material_gwp_a1a3': self.material_gwp_a1a3,
            'material_gwp_c3': self.material_gwp_c3,
            'material_gwp_c4': self.material_gwp_c4,
            'material_gwp_d': self.material_gwp_d,
            'material_source': self.material_source,
            'material_dataset_type': self.material_dataset_type,
            'quantity': self.quantity,
            'result_a': self.result_a,
            'result_ac': self.result_ac,
            'result_acd': self.result_acd,
            'result_a_bio': self.result_a_bio,
            'result_ac_bio': self.result_ac_bio,
            'result_acd_bio': self.result_acd_bio,
            'c_modules_missing': self.c_modules_missing,
            'd_module_missing': self.d_module_missing
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MaterialRow':
        """Deserialisierung"""
        return cls(**data)


@dataclass
class Variant:
    """
    Eine Bauwerksvariante mit Materialzeilen
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Variante"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Materialzeilen
    rows: List[MaterialRow] = field(default_factory=list)
    
    # Summen (werden berechnet)
    sum_a: float = 0.0
    sum_ac: float = 0.0
    sum_acd: Optional[float] = None
    
    # Bio-korrigierte Summen
    sum_a_bio: Optional[float] = None
    sum_ac_bio: Optional[float] = None
    sum_acd_bio: Optional[float] = None
    
    # UI-Einstellungen
    visible: bool = True  # Sichtbarkeit im Dashboard
    column_widths: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialisierung"""
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'rows': [row.to_dict() for row in self.rows],
            'sum_a': self.sum_a,
            'sum_ac': self.sum_ac,
            'sum_acd': self.sum_acd,
            'sum_a_bio': self.sum_a_bio,
            'sum_ac_bio': self.sum_ac_bio,
            'sum_acd_bio': self.sum_acd_bio,
            'visible': self.visible,
            'column_widths': self.column_widths
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Variant':
        """Deserialisierung"""
        rows_data = data.pop('rows', [])
        variant = cls(**data)
        variant.rows = [MaterialRow.from_dict(row) for row in rows_data]
        return variant
    
    def add_row(self, row: MaterialRow) -> None:
        """Fügt eine Zeile hinzu"""
        row.position = len(self.rows)
        self.rows.append(row)
        self.updated_at = datetime.now().isoformat()
    
    def remove_row(self, row_id: str) -> None:
        """Entfernt eine Zeile"""
        self.rows = [r for r in self.rows if r.id != row_id]
        self._reindex_positions()
        self.updated_at = datetime.now().isoformat()
    
    def move_row_up(self, row_id: str) -> None:
        """Verschiebt Zeile nach oben"""
        idx = next((i for i, r in enumerate(self.rows) if r.id == row_id), None)
        if idx is not None and idx > 0:
            self.rows[idx], self.rows[idx - 1] = self.rows[idx - 1], self.rows[idx]
            self._reindex_positions()
            self.updated_at = datetime.now().isoformat()
    
    def move_row_down(self, row_id: str) -> None:
        """Verschiebt Zeile nach unten"""
        idx = next((i for i, r in enumerate(self.rows) if r.id == row_id), None)
        if idx is not None and idx < len(self.rows) - 1:
            self.rows[idx], self.rows[idx + 1] = self.rows[idx + 1], self.rows[idx]
            self._reindex_positions()
            self.updated_at = datetime.now().isoformat()
    
    def _reindex_positions(self) -> None:
        """Aktualisiert die Position-Indizes"""
        for i, row in enumerate(self.rows):
            row.position = i
    
    def calculate_sums(self) -> None:
        """Berechnet Gesamtsummen (Standard und bio-korrigiert)"""
        # Standard-Summen
        self.sum_a = sum(row.result_a for row in self.rows)
        self.sum_ac = sum(row.result_ac for row in self.rows)
        
        # sum_acd nur wenn alle Zeilen D haben
        if all(row.result_acd is not None for row in self.rows if row.material_id):
            self.sum_acd = sum(row.result_acd or 0.0 for row in self.rows)
        else:
            self.sum_acd = None
        
        # Bio-korrigierte Summen (nur wenn mindestens eine Zeile bio-Werte hat)
        bio_rows = [r for r in self.rows if r.result_a_bio is not None]
        if bio_rows:
            self.sum_a_bio = sum(row.result_a_bio or row.result_a for row in self.rows)
            self.sum_ac_bio = sum(row.result_ac_bio or row.result_ac for row in self.rows)
            
            # sum_acd_bio nur wenn alle Zeilen D haben
            if all(row.result_acd is not None for row in self.rows if row.material_id):
                self.sum_acd_bio = sum(row.result_acd_bio or row.result_acd or 0.0 for row in self.rows)
            else:
                self.sum_acd_bio = None
        else:
            self.sum_a_bio = None
            self.sum_ac_bio = None
            self.sum_acd_bio = None
