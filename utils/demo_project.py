"""
Demo-Projekt-Generator
Erstellt beim ersten Start ein Beispielprojekt
"""

from models.project import Project
from models.variant import Variant, MaterialRow
from models.material import Material


def create_demo_project() -> Project:
    """
    Erstellt Demo-Projekt mit 3 Varianten
    
    Returns:
        Project-Objekt mit Demo-Daten
    """
    
    project = Project(name="Demo-Projekt: Mehrfamilienhaus")
    
    # Variante 1: Massivbau
    variant_massiv = Variant(name="Massivbau")
    
    # Dummy-Materialien für Massivbau
    materials_massiv = [
        {
            'name': 'Stahlbeton C30/37',
            'unit': 'm³',
            'gwp_a1a3': 320.0,
            'gwp_c3': 5.0,
            'gwp_c4': 2.0,
            'gwp_d': -15.0,
            'quantity': 150.0
        },
        {
            'name': 'Mauerziegel 24cm',
            'unit': 'm²',
            'gwp_a1a3': 45.0,
            'gwp_c3': 1.5,
            'gwp_c4': 0.8,
            'gwp_d': -2.0,
            'quantity': 800.0
        },
        {
            'name': 'Stahlbewehrung BSt500',
            'unit': 't',
            'gwp_a1a3': 1850.0,
            'gwp_c3': 8.0,
            'gwp_c4': 12.0,
            'gwp_d': -1200.0,
            'quantity': 25.0
        },
        {
            'name': 'Mineralwolle Dämmung',
            'unit': 'm³',
            'gwp_a1a3': 180.0,
            'gwp_c3': 2.0,
            'gwp_c4': 1.0,
            'gwp_d': 0.0,
            'quantity': 60.0
        },
        {
            'name': 'Estrich',
            'unit': 'm³',
            'gwp_a1a3': 95.0,
            'gwp_c3': 3.0,
            'gwp_c4': 1.5,
            'gwp_d': 0.0,
            'quantity': 80.0
        }
    ]
    
    for i, mat_data in enumerate(materials_massiv):
        material = Material(
            id=f"demo_massiv_{i}",
            name=mat_data['name'],
            unit=mat_data['unit'],
            gwp_a1a3=mat_data['gwp_a1a3'],
            gwp_c3=mat_data['gwp_c3'],
            gwp_c4=mat_data['gwp_c4'],
            gwp_d=mat_data['gwp_d'],
            dataset_type='generisch',
            source='Demo-Datenbank'
        )
        
        row = MaterialRow()
        row.position = i
        row.material_id = material.id
        row.material_name = material.name
        row.material_unit = material.unit
        row.material_gwp_a1a3 = material.gwp_a1a3
        row.material_gwp_c3 = material.gwp_c3
        row.material_gwp_c4 = material.gwp_c4
        row.material_gwp_d = material.gwp_d
        row.material_source = material.source
        row.material_dataset_type = material.dataset_type
        row.quantity = mat_data['quantity']
        
        # Berechnung
        row.result_a = row.quantity * row.material_gwp_a1a3
        row.result_ac = row.quantity * (row.material_gwp_a1a3 + row.material_gwp_c3 + row.material_gwp_c4)
        row.result_acd = row.result_ac + (row.quantity * row.material_gwp_d)
        
        variant_massiv.rows.append(row)
    
    variant_massiv.calculate_sums()
    project.variants.append(variant_massiv)
    
    # Variante 2: Holzbau
    variant_holz = Variant(name="Holzbau")
    
    materials_holz = [
        {
            'name': 'Brettschichtholz GL24h',
            'unit': 'm³',
            'gwp_a1a3': 185.0,
            'gwp_c3': 3.0,
            'gwp_c4': 1.5,
            'gwp_d': -1850.0,
            'quantity': 120.0
        },
        {
            'name': 'Brettsperrholz BSP',
            'unit': 'm³',
            'gwp_a1a3': 165.0,
            'gwp_c3': 2.8,
            'gwp_c4': 1.2,
            'gwp_d': -1650.0,
            'quantity': 180.0
        },
        {
            'name': 'Holzfaserdämmung',
            'unit': 'm³',
            'gwp_a1a3': 45.0,
            'gwp_c3': 1.0,
            'gwp_c4': 0.5,
            'gwp_d': -450.0,
            'quantity': 85.0
        },
        {
            'name': 'Streifenfundament Beton',
            'unit': 'm³',
            'gwp_a1a3': 320.0,
            'gwp_c3': 5.0,
            'gwp_c4': 2.0,
            'gwp_d': -15.0,
            'quantity': 40.0
        },
        {
            'name': 'Gipskartonplatten',
            'unit': 'm²',
            'gwp_a1a3': 6.5,
            'gwp_c3': 0.2,
            'gwp_c4': 0.1,
            'gwp_d': 0.0,
            'quantity': 950.0
        }
    ]
    
    for i, mat_data in enumerate(materials_holz):
        material = Material(
            id=f"demo_holz_{i}",
            name=mat_data['name'],
            unit=mat_data['unit'],
            gwp_a1a3=mat_data['gwp_a1a3'],
            gwp_c3=mat_data['gwp_c3'],
            gwp_c4=mat_data['gwp_c4'],
            gwp_d=mat_data['gwp_d'],
            dataset_type='generisch',
            source='Demo-Datenbank'
        )
        
        row = MaterialRow()
        row.position = i
        row.material_id = material.id
        row.material_name = material.name
        row.material_unit = material.unit
        row.material_gwp_a1a3 = material.gwp_a1a3
        row.material_gwp_c3 = material.gwp_c3
        row.material_gwp_c4 = material.gwp_c4
        row.material_gwp_d = material.gwp_d
        row.material_source = material.source
        row.material_dataset_type = material.dataset_type
        row.quantity = mat_data['quantity']
        
        row.result_a = row.quantity * row.material_gwp_a1a3
        row.result_ac = row.quantity * (row.material_gwp_a1a3 + row.material_gwp_c3 + row.material_gwp_c4)
        row.result_acd = row.result_ac + (row.quantity * row.material_gwp_d)
        
        variant_holz.rows.append(row)
    
    variant_holz.calculate_sums()
    project.variants.append(variant_holz)
    
    # Variante 3: Hybrid
    variant_hybrid = Variant(name="Hybrid (Holz/Beton)")
    
    materials_hybrid = [
        {
            'name': 'Stahlbeton C30/37 (Fundamente)',
            'unit': 'm³',
            'gwp_a1a3': 320.0,
            'gwp_c3': 5.0,
            'gwp_c4': 2.0,
            'gwp_d': -15.0,
            'quantity': 80.0
        },
        {
            'name': 'Brettsperrholz BSP (Decken)',
            'unit': 'm³',
            'gwp_a1a3': 165.0,
            'gwp_c3': 2.8,
            'gwp_c4': 1.2,
            'gwp_d': -1650.0,
            'quantity': 140.0
        },
        {
            'name': 'Brettschichtholz GL24h (Stützen)',
            'unit': 'm³',
            'gwp_a1a3': 185.0,
            'gwp_c3': 3.0,
            'gwp_c4': 1.5,
            'gwp_d': -1850.0,
            'quantity': 45.0
        },
        {
            'name': 'Stahlbeton C30/37 (Treppenhaus)',
            'unit': 'm³',
            'gwp_a1a3': 320.0,
            'gwp_c3': 5.0,
            'gwp_c4': 2.0,
            'gwp_d': -15.0,
            'quantity': 35.0
        },
        {
            'name': 'Holzfaserdämmung',
            'unit': 'm³',
            'gwp_a1a3': 45.0,
            'gwp_c3': 1.0,
            'gwp_c4': 0.5,
            'gwp_d': -450.0,
            'quantity': 70.0
        }
    ]
    
    for i, mat_data in enumerate(materials_hybrid):
        material = Material(
            id=f"demo_hybrid_{i}",
            name=mat_data['name'],
            unit=mat_data['unit'],
            gwp_a1a3=mat_data['gwp_a1a3'],
            gwp_c3=mat_data['gwp_c3'],
            gwp_c4=mat_data['gwp_c4'],
            gwp_d=mat_data['gwp_d'],
            dataset_type='generisch',
            source='Demo-Datenbank'
        )
        
        row = MaterialRow()
        row.position = i
        row.material_id = material.id
        row.material_name = material.name
        row.material_unit = material.unit
        row.material_gwp_a1a3 = material.gwp_a1a3
        row.material_gwp_c3 = material.gwp_c3
        row.material_gwp_c4 = material.gwp_c4
        row.material_gwp_d = material.gwp_d
        row.material_source = material.source
        row.material_dataset_type = material.dataset_type
        row.quantity = mat_data['quantity']
        
        row.result_a = row.quantity * row.material_gwp_a1a3
        row.result_ac = row.quantity * (row.material_gwp_a1a3 + row.material_gwp_c3 + row.material_gwp_c4)
        row.result_acd = row.result_ac + (row.quantity * row.material_gwp_d)
        
        variant_hybrid.rows.append(row)
    
    variant_hybrid.calculate_sums()
    project.variants.append(variant_hybrid)
    
    return project
