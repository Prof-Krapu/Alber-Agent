import json
from typing import Dict

def get_weather_mock(city: str) -> str:
    """
    Simule la météo pour une ville donnée.
    
    Args:
        city (str): Nom de la ville
        
    Returns:
        str: Représentation JSON des données météo simulées
    """
    # Données météo simulées pour quelques villes
    weather_data = {
        "Paris": {
            "city": "Paris",
            "temperature": 18.5,
            "humidity": 72,
            "pressure": 1013,
            "description": "Clair",
            "wind_speed": 3.2
        },
        "Londres": {
            "city": "Londres",
            "temperature": 12.3,
            "humidity": 80,
            "pressure": 1008,
            "description": "Pluvieux",
            "wind_speed": 5.1
        },
        "New York": {
            "city": "New York",
            "temperature": 22.1,
            "humidity": 65,
            "pressure": 1015,
            "description": "Ensoleillé",
            "wind_speed": 2.8
        }
    }
    
    # Si la ville n'est pas dans notre base, on retourne des données par défaut
    if city not in weather_data:
        return json.dumps({
            "city": city,
            "temperature": 20.0,
            "humidity": 60,
            "pressure": 1013,
            "description": "Inconnue",
            "wind_speed": 0.0
        })
    
    return json.dumps(weather_data[city])