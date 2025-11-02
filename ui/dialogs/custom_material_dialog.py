"""
Custom Material Dialog - Dialog zum Anlegen eigener EPDs
"""

import customtkinter as ctk
from tkinter import messagebox
from typing import Optional
import logging
import uuid as uuid_module

from models.material import Material

logger = logging.getLogger(__name__)


class CustomMaterialDialog(ctk.CTkToplevel):
    """
    Dialog zum Anlegen eigener Materialien/EPDs
    
    Eingabefelder:
    - Name (Pflicht)
    - Quelle/Hersteller
    - Datensatztyp
    - Einheit
    - GWP A1-A3 (Pflicht)
    - GWP C3 (optional)
    - GWP C4 (optional)
    - GWP D (optional)
    - Biogener Kohlenstoff (optional, für Holz)
    """
    
    def __init__(self, parent, on_save):
        super().__init__(parent)
        
        self.on_save = on_save  # Callback mit Material-Objekt
        self.logger = logger
        
        # Fenster-Konfiguration
        self.title("Eigenes Material anlegen")
        self.geometry("600x700")
        
        # Zentrieren
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"600x700+{x}+{y}")
        
        # Modal
        self.transient(parent)
        self.grab_set()
        
        self._build_ui()
    
    def _build_ui(self) -> None:
        """Erstellt UI"""
        
        # Hauptcontainer
        main_frame = ctk.CTkScrollableFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Titel
        title_label = ctk.CTkLabel(
            main_frame,
            text="Neue EPD anlegen",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Beschreibung
        desc_label = ctk.CTkLabel(
            main_frame,
            text="Legen Sie ein eigenes Material mit GWP-Werten an.\n"
                 "Diese EPD wird in 'custom_materials.csv' gespeichert und bleibt\n"
                 "auch bei ÖKOBAUDAT-Updates erhalten.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        desc_label.pack(pady=(0, 20))
        
        # Eingabefelder
        
        # Name (Pflicht)
        name_frame = self._create_field_frame(main_frame, "Name *", is_required=True)
        self.name_entry = ctk.CTkEntry(name_frame, width=400, placeholder_text="z.B. Holzfaserplatte 160 kg/m³")
        self.name_entry.pack(fill="x", padx=5, pady=5)
        
        # Quelle/Hersteller
        source_frame = self._create_field_frame(main_frame, "Quelle/Hersteller")
        self.source_entry = ctk.CTkEntry(source_frame, width=400, placeholder_text="z.B. Hersteller XY AG")
        self.source_entry.pack(fill="x", padx=5, pady=5)
        
        # Datensatztyp
        type_frame = self._create_field_frame(main_frame, "Datensatztyp")
        self.type_combo = ctk.CTkComboBox(
            type_frame,
            values=["generisch", "spezifisch", "durchschnitt", "repräsentativ"],
            width=400
        )
        self.type_combo.set("spezifisch")
        self.type_combo.pack(fill="x", padx=5, pady=5)
        
        # Konformität/Norm
        conformity_frame = self._create_field_frame(main_frame, "Norm/Konformität")
        conformity_info = ctk.CTkLabel(
            conformity_frame,
            text="Nach welcher Norm wurde die EPD erstellt?",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        conformity_info.pack(anchor="w", padx=5)
        
        self.conformity_combo = ctk.CTkComboBox(
            conformity_frame,
            values=[
                "DIN EN 15804+A2 / ISO 14025",
                "EN 15804+A2 (EF 3.0) / ISO 14025",
                "EN 15804+A2 (EF 3.1) / ISO 14025",
                "DIN EN 15804+A1 / ISO 14025",
                "EN 15804 / ISO 14025",
                "ISO 14025",
                "Eigene EPD"
            ],
            width=400
        )
        self.conformity_combo.set("DIN EN 15804+A2 / ISO 14025")
        self.conformity_combo.pack(fill="x", padx=5, pady=5)
        
        # Einheit
        unit_frame = self._create_field_frame(main_frame, "Einheit *", is_required=True)
        self.unit_combo = ctk.CTkComboBox(
            unit_frame,
            values=["kg", "m²", "m³", "m", "Stück"],
            width=400
        )
        self.unit_combo.set("kg")
        self.unit_combo.pack(fill="x", padx=5, pady=5)
        
        # Trennlinie
        separator1 = ctk.CTkFrame(main_frame, height=2, fg_color="gray")
        separator1.pack(fill="x", pady=20)
        
        # GWP-Werte Header
        gwp_header = ctk.CTkLabel(
            main_frame,
            text="GWP-Werte (Global Warming Potential)",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        gwp_header.pack(pady=(0, 10))
        
        gwp_info = ctk.CTkLabel(
            main_frame,
            text="Angaben in kg CO₂-Äq. pro Einheit",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        gwp_info.pack(pady=(0, 15))
        
        # GWP A1-A3 (Pflicht)
        a1a3_frame = self._create_field_frame(main_frame, "GWP A1-A3 (Herstellung) *", is_required=True)
        self.gwp_a1a3_entry = ctk.CTkEntry(a1a3_frame, width=400, placeholder_text="z.B. 1.234")
        self.gwp_a1a3_entry.pack(fill="x", padx=5, pady=5)
        
        # GWP C3
        c3_frame = self._create_field_frame(main_frame, "GWP C3 (Abfallbehandlung)")
        self.gwp_c3_entry = ctk.CTkEntry(c3_frame, width=400, placeholder_text="Optional, z.B. 0.123")
        self.gwp_c3_entry.pack(fill="x", padx=5, pady=5)
        
        # GWP C4
        c4_frame = self._create_field_frame(main_frame, "GWP C4 (Deponie/Recycling)")
        self.gwp_c4_entry = ctk.CTkEntry(c4_frame, width=400, placeholder_text="Optional, z.B. -0.050")
        self.gwp_c4_entry.pack(fill="x", padx=5, pady=5)
        
        # GWP D
        d_frame = self._create_field_frame(main_frame, "GWP D (Gutschriften)")
        self.gwp_d_entry = ctk.CTkEntry(d_frame, width=400, placeholder_text="Optional, z.B. -0.200")
        self.gwp_d_entry.pack(fill="x", padx=5, pady=5)
        
        # Trennlinie
        separator2 = ctk.CTkFrame(main_frame, height=2, fg_color="gray")
        separator2.pack(fill="x", pady=20)
        
        # Biogener Kohlenstoff
        bio_header = ctk.CTkLabel(
            main_frame,
            text="Biogener Kohlenstoff (für Holz/biobasierte Materialien)",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        bio_header.pack(pady=(0, 10))
        
        bio_frame = self._create_field_frame(main_frame, "Biogene CO₂-Speicherung")
        bio_info = ctk.CTkLabel(
            bio_frame,
            text="Negativer Wert = CO₂-Speicherung, z.B. -1.83 für Holz",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        bio_info.pack(anchor="w", padx=5)
        
        self.bio_carbon_entry = ctk.CTkEntry(bio_frame, width=400, placeholder_text="Optional, z.B. -1.830")
        self.bio_carbon_entry.pack(fill="x", padx=5, pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=20, pady=20)
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="Speichern",
            command=self._on_save,
            width=150,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="green"
        )
        save_btn.pack(side="right", padx=5)
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Abbrechen",
            command=self.destroy,
            width=150,
            height=40
        )
        cancel_btn.pack(side="right", padx=5)
    
    def _create_field_frame(self, parent, label_text: str, is_required: bool = False) -> ctk.CTkFrame:
        """Erstellt Frame für ein Eingabefeld mit Label"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        
        label_color = "red" if is_required else None
        label = ctk.CTkLabel(
            frame,
            text=label_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=label_color,
            anchor="w"
        )
        label.pack(anchor="w", padx=5)
        
        return frame
    
    def _validate_float(self, value_str: str, field_name: str, allow_empty: bool = False) -> Optional[float]:
        """
        Validiert Float-Eingabe
        
        Returns:
            Float-Wert oder None (bei leerem optionalem Feld)
        
        Raises:
            ValueError bei ungültiger Eingabe
        """
        value_str = value_str.strip()
        
        if not value_str:
            if allow_empty:
                return None
            else:
                raise ValueError(f"{field_name}: Pflichtfeld darf nicht leer sein")
        
        try:
            # Komma durch Punkt ersetzen
            value_str = value_str.replace(',', '.')
            return float(value_str)
        except ValueError:
            raise ValueError(f"{field_name}: Ungültiger Zahlenwert '{value_str}'")
    
    def _on_save(self) -> None:
        """Handler für Speichern-Button"""
        
        try:
            # Pflichtfelder validieren
            name = self.name_entry.get().strip()
            if not name:
                raise ValueError("Name ist ein Pflichtfeld")
            
            # Optionale Felder
            source = self.source_entry.get().strip()
            dataset_type = self.type_combo.get()
            conformity = self.conformity_combo.get()
            unit = self.unit_combo.get()
            
            # GWP-Werte validieren
            gwp_a1a3 = self._validate_float(self.gwp_a1a3_entry.get(), "GWP A1-A3", allow_empty=False)
            gwp_c3 = self._validate_float(self.gwp_c3_entry.get(), "GWP C3", allow_empty=True) or 0.0
            gwp_c4 = self._validate_float(self.gwp_c4_entry.get(), "GWP C4", allow_empty=True) or 0.0
            gwp_d = self._validate_float(self.gwp_d_entry.get(), "GWP D", allow_empty=True)
            
            # Biogener Kohlenstoff
            biogenic_carbon = self._validate_float(self.bio_carbon_entry.get(), "Biogener Kohlenstoff", allow_empty=True)
            
            # Material erstellen
            material = Material(
                id=f"custom_{uuid_module.uuid4().hex[:16]}",
                name=name,
                source=source,
                dataset_type=dataset_type,
                unit=unit,
                gwp_a1a3=gwp_a1a3,
                gwp_c3=gwp_c3,
                gwp_c4=gwp_c4,
                gwp_d=gwp_d,
                biogenic_carbon=biogenic_carbon,
                conformity=conformity,
                is_custom=True
            )
            
            self.logger.info(f"Custom Material erstellt: {material.name}")
            
            # Callback aufrufen
            if self.on_save:
                self.on_save(material)
            
            # Dialog schließen
            self.destroy()
            
        except ValueError as e:
            messagebox.showerror("Validierungsfehler", str(e))
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern: {e}", exc_info=True)
            messagebox.showerror("Fehler", f"Fehler beim Speichern:\n{e}")
