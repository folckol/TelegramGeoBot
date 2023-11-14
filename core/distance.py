from geopy.geocoders import Nominatim
import math

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Радиус Земли в километрах
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance


def get_name_position(latitude, longitude):

    geolocator = Nominatim(user_agent='my_app')

    location = geolocator.reverse((latitude, longitude), exactly_one=True)

    if location:
        address = location.raw['address']
        street_name = address.get('road')
        house_number = address.get('house_number')
        return f'{street_name} {house_number}'