"""
Berechnungs-Service für CO₂-Bilanzierung
Implementiert die Berechnung nach DIN EN 15804+A2 und ABC-Entwurfstafeln
"""

from typing import Optional, Tuple
from models.variant import MaterialRow
from models.material import Material
import logging

logger = logging.getLogger(__name__)


class CalculationService:
    """
    Zentraler Service für alle Berechnungen der CO₂-Äquivalente
    """
    
    def __init__(self):
        self.logger = logger
    
    def calc_gwp(
        self,
        material: Material,
        quantity: float,
        system_boundary: str = "A1-A3",
        use_biogenic: bool = False
    ) -> Tuple[float, float, Optional[float], Optional[float], Optional[float], Optional[float]]:
        """
        Berechnet GWP (Global Warming Potential) für ein Material
        
        Args:
            material: Material-Objekt mit GWP-Werten
            quantity: Menge in der Einheit des Materials
            system_boundary: "A1-A3", "A1-A3+C3+C4", "A1-A3+C3+C4+D"
            use_biogenic: True = mit biogener Speicherung
        
        Returns:
            (gwp_a, gwp_ac, gwp_acd, gwp_a_bio, gwp_ac_bio, gwp_acd_bio)
            - gwp_a: Menge × GWP_A1-A3 (Standard)
            - gwp_ac: Menge × (GWP_A1-A3 + GWP_C3 + GWP_C4) (Standard)
            - gwp_acd: gwp_ac + Menge × GWP_D (Standard)
            - gwp_a_bio: gwp_a + biogenic_carbon (bio-korrigiert)
            - gwp_ac_bio: gwp_ac + biogenic_carbon (bio-korrigiert)
            - gwp_acd_bio: gwp_acd + biogenic_carbon (bio-korrigiert)
        """
        
        # Standard-Berechnung (EN 15804+A2)
        # A1-A3 (Herstellung)
        gwp_a = quantity * material.gwp_a1a3
        
        # A1-A3 + C3 + C4 (Herstellung + Entsorgung)
        gwp_ac = quantity * (
            material.gwp_a1a3 +
            material.gwp_c3 +
            material.gwp_c4
        )
        
        # Optional: + D (Gutschriften)
        gwp_acd = None
        if material.gwp_d is not None:
            gwp_acd = gwp_ac + (quantity * material.gwp_d)
        
        # Bio-korrigierte Berechnung (mit biogener Speicherung)
        gwp_a_bio = None
        gwp_ac_bio = None
        gwp_acd_bio = None
        
        if use_biogenic and material.biogenic_carbon is not None:
            bio_storage = quantity * material.biogenic_carbon
            gwp_a_bio = gwp_a + bio_storage
            gwp_ac_bio = gwp_ac + bio_storage
            if gwp_acd is not None:
                gwp_acd_bio = gwp_acd + bio_storage
        
        self.logger.debug(
            f"Berechnung: {material.name}, Menge={quantity} {material.unit}, "
            f"A={gwp_a:.2f}, AC={gwp_ac:.2f}, ACD={gwp_acd}, "
            f"A_bio={gwp_a_bio}, AC_bio={gwp_ac_bio}, ACD_bio={gwp_acd_bio}"
        )
        
        return gwp_a, gwp_ac, gwp_acd, gwp_a_bio, gwp_ac_bio, gwp_acd_bio
    
    def update_material_row(
        self,
        row: MaterialRow,
        material: Material,
        quantity: Optional[float] = None
    ) -> MaterialRow:
        """
        Aktualisiert eine MaterialRow mit neuen Berechnungen
        
        Args:
            row: Zu aktualisierende MaterialRow
            material: Material-Objekt
            quantity: Optional neue Menge (sonst aus row übernehmen)
        
        Returns:
            Aktualisierte MaterialRow
        """
        
        if quantity is not None:
            row.quantity = quantity
        
        # Material-Daten kopieren
        row.material_id = material.id
        row.material_name = material.name
        row.material_unit = material.unit
        row.material_gwp_a1a3 = material.gwp_a1a3
        row.material_gwp_c3 = material.gwp_c3
        row.material_gwp_c4 = material.gwp_c4
        row.material_gwp_d = material.gwp_d
        row.material_source = material.source
        row.material_dataset_type = material.dataset_type
        
        # Flags setzen
        row.c_modules_missing = not material.has_c_modules()
        row.d_module_missing = not material.has_d_module()
        
        # Berechnung durchführen (sowohl Standard als auch bio-korrigiert)
        gwp_a, gwp_ac, gwp_acd, gwp_a_bio, gwp_ac_bio, gwp_acd_bio = self.calc_gwp(
            material, row.quantity, use_biogenic=True
        )
        
        row.result_a = gwp_a
        row.result_ac = gwp_ac
        row.result_acd = gwp_acd
        
        # Bio-korrigierte Werte speichern (neue Felder in MaterialRow benötigt)
        if hasattr(row, 'result_a_bio'):
            row.result_a_bio = gwp_a_bio
            row.result_ac_bio = gwp_ac_bio
            row.result_acd_bio = gwp_acd_bio
        
        return row
    
    def recalculate_row(self, row: MaterialRow) -> MaterialRow:
        """
        Berechnet eine bestehende MaterialRow neu (z.B. nach Mengenänderung)
        
        Args:
            row: Zeile mit gespeicherten Material-Daten
        
        Returns:
            Aktualisierte MaterialRow
        """
        
        # Material aus gespeicherten Daten rekonstruieren
        material = Material(
            id=row.material_id or "",
            name=row.material_name,
            unit=row.material_unit,
            gwp_a1a3=row.material_gwp_a1a3,
            gwp_c3=row.material_gwp_c3,
            gwp_c4=row.material_gwp_c4,
            gwp_d=row.material_gwp_d,
            source=row.material_source,
            dataset_type=row.material_dataset_type
        )
        
        # Neu berechnen (beide Varianten)
        gwp_a, gwp_ac, gwp_acd, gwp_a_bio, gwp_ac_bio, gwp_acd_bio = self.calc_gwp(
            material, row.quantity, use_biogenic=True
        )
        
        row.result_a = gwp_a
        row.result_ac = gwp_ac
        row.result_acd = gwp_acd
        
        # Bio-korrigierte Werte
        if hasattr(row, 'result_a_bio'):
            row.result_a_bio = gwp_a_bio
            row.result_ac_bio = gwp_ac_bio
            row.result_acd_bio = gwp_acd_bio
        
        return row
    
    def get_sum_for_boundary(
        self,
        sum_a: float,
        sum_ac: float,
        sum_acd: Optional[float],
        system_boundary: str
    ) -> float:
        """
        Gibt die passende Summe für die gewählte Systemgrenze zurück
        
        Args:
            sum_a: Summe A1-A3
            sum_ac: Summe A1-A3+C3+C4
            sum_acd: Summe A1-A3+C3+C4+D (optional)
            system_boundary: Gewählte Systemgrenze
        
        Returns:
            Passende Summe
        """
        
        if system_boundary == "A1-A3":
            return sum_a
        elif system_boundary == "A1-A3+C3+C4":
            return sum_ac
        elif system_boundary == "A1-A3+C3+C4+D":
            return sum_acd if sum_acd is not None else sum_ac
        else:
            self.logger.warning(f"Unbekannte Systemgrenze: {system_boundary}")
            return sum_a
