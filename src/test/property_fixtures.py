"""
Test fixtures for properties
"""

from typing import List, Dict, Any
import random


def get_seville_property_fixtures() -> List[Dict[str, Any]]:
    """
    Property fixtures for Seville, Spain
    """

    seville_areas = [
        "Centro Histórico",
        "Triana",
        "Los Remedios",
        "Nervión",
        "Macarena",
        "Cerro-Amate",
        "San Pablo-Santa Justa",
        "Este-Alcosa-Torreblanca",
        "Bellavista-La Palmera",
        "Sur",
        "Casco Antiguo",
        "Santa Cruz",
        "Alameda de Hércules",
        "La Cartuja",
        "Sevilla Este",
    ]
    street_names = [
        "Calle Sierpes",
        "Avenida de la Constitución",
        "Calle Betis",
        "Calle Feria",
        "Calle San Fernando",
        "Plaza de Armas",
        "Calle Alfarería",
        "Avenida de Jerez",
        "Calle Asunción",
        "Plaza Nueva",
        "Calle Tetuán",
        "Avenida Eduardo Dato",
        "Calle Luis Montoto",
        "Plaza del Salvador",
        "Calle O'Donnell",
    ]
    common_amenities = [
        {"aire_acondicionado": True, "calefaccion": True, "ascensor": True},
        {"terraza": True, "parking": True, "trastero": True},
        {"piscina_comunitaria": True, "jardin": True, "portero": True},
        {"amueblado": True, "electrodomesticos": True, "internet": True},
        {"balcon": True, "chimenea": True, "armarios_empotrados": True},
    ]
    fixtures = []
    property_types = [
        # Apartments (12 properties)
        {"is_apartment": True, "is_house": False, "type_name": "Apartamento"},
        {"is_apartment": True, "is_house": False, "type_name": "Piso"},
        {"is_apartment": True, "is_house": False, "type_name": "Estudio"},
        {"is_apartment": True, "is_house": False, "type_name": "Loft"},
    ]
    house_types = [
        # Houses (8 properties)
        {"is_apartment": False, "is_house": True, "type_name": "Casa"},
        {"is_apartment": False, "is_house": True, "type_name": "Chalet"},
        {"is_apartment": False, "is_house": True, "type_name": "Villa"},
        {"is_apartment": False, "is_house": True, "type_name": "Adosado"},
    ]
    for i in range(12):
        prop_type = random.choice(property_types)
        area = random.choice(seville_areas)
        street = random.choice(street_names)
        base_price = random.randint(120000, 450000)
        fixture = {
            "title": f"{prop_type['type_name']} en {area} - {random.randint(2, 4)} habitaciones",
            "address": f"{street}, {random.randint(1, 150)}, {area}, 41001 Sevilla, España",
            "price": float(base_price),
            "bathrooms": random.randint(1, 3),
            "rooms": random.randint(1, 4),
            "square_meters": float(random.randint(45, 120)),
            "is_apartment": prop_type["is_apartment"],
            "is_house": prop_type["is_house"],
            "building_floor": (
                random.randint(0, 8) if prop_type["is_apartment"] else None
            ),
            "source_url": f"https://idealista.com/inmueble/{random.randint(10000000, 99999999)}/",
            "is_available": random.choice([True, True, True, False]),  # 75% available
            "amenities": random.choice(common_amenities),
        }
        fixtures.append(fixture)
    for i in range(8):
        prop_type = random.choice(house_types)
        area = random.choice(seville_areas)
        street = random.choice(street_names)
        base_price = random.randint(250000, 750000)
        fixture = {
            "title": f"{prop_type['type_name']} independiente en {area}",
            "address": f"{street}, {random.randint(1, 80)}, {area}, 41001 Sevilla, España",
            "price": float(base_price),
            "bathrooms": random.randint(2, 4),
            "rooms": random.randint(3, 6),
            "square_meters": float(random.randint(100, 300)),
            "is_apartment": prop_type["is_apartment"],
            "is_house": prop_type["is_house"],
            "building_floor": None,  # Houses don't have floors
            "source_url": f"https://fotocasa.es/vivienda/{random.randint(10000000, 99999999)}/",
            "is_available": random.choice([True, True, True, False]),
            "amenities": {
                **random.choice(common_amenities),
                "jardin_privado": True,
                "garaje": True,
                "barbacoa": random.choice([True, False]),
            },
        }
        fixtures.append(fixture)

    return fixtures


def get_specific_test_properties() -> List[Dict[str, Any]]:
    """
    Get specific properties for targeted testing
    """
    return [
        {
            "title": "Apartamento de lujo en Santa Cruz",
            "address": "Calle Mateos Gago, 15, Santa Cruz, 41004 Sevilla, España",
            "price": 350000.0,
            "bathrooms": 2,
            "rooms": 3,
            "square_meters": 95.0,
            "is_apartment": True,
            "is_house": False,
            "building_floor": 3,
            "source_url": "https://idealista.com/inmueble/12345678/",
            "is_available": True,
            "amenities": {
                "aire_acondicionado": True,
                "ascensor": True,
                "balcon": True,
                "amueblado": False,
            },
        },
        {
            "title": "Casa familiar en Triana",
            "address": "Calle Betis, 45, Triana, 41010 Sevilla, España",
            "price": 480000.0,
            "bathrooms": 3,
            "rooms": 4,
            "square_meters": 180.0,
            "is_apartment": False,
            "is_house": True,
            "building_floor": None,
            "source_url": "https://fotocasa.es/vivienda/87654321/",
            "is_available": True,
            "amenities": {
                "jardin_privado": True,
                "garaje": True,
                "terraza": True,
                "chimenea": True,
            },
        },
        {
            "title": "Estudio céntrico - No disponible",
            "address": "Calle Sierpes, 8, Centro Histórico, 41001 Sevilla, España",
            "price": 125000.0,
            "bathrooms": 1,
            "rooms": 1,
            "square_meters": 35.0,
            "is_apartment": True,
            "is_house": False,
            "building_floor": 2,
            "source_url": "https://idealista.com/inmueble/11111111/",
            "is_available": False,
            "amenities": {
                "aire_acondicionado": True,
                "amueblado": True,
                "internet": True,
            },
        },
    ]
