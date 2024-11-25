import requests
import json
import math
import random
import datetime


UPLOAD_TRUCK_DATA_URL = "http://localhost:7071/api/uploadTruckData"

def generate_coordinate_at_distance(lat, lon, distance=100, bearing=0):
    """
    Generate a GPS coordinate a specified distance away from a given location.

    :param lat: Latitude of the starting point in degrees
    :param lon: Longitude of the starting point in degrees
    :param distance: Distance in meters (default is 100)
    :param bearing: Bearing in degrees (default is 0, which is north)
    :return: Tuple containing the new latitude and longitude
    """
    # Earth's radius in meters
    earth_radius = 6371000

    # Convert latitude, longitude, and bearing to radians
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    bearing_rad = math.radians(bearing)

    # Calculate the new latitude
    new_lat_rad = math.asin(
        math.sin(lat_rad) * math.cos(distance / earth_radius) +
        math.cos(lat_rad) * math.sin(distance / earth_radius) * math.cos(bearing_rad)
    )

    # Calculate the new longitude
    new_lon_rad = lon_rad + math.atan2(
        math.sin(bearing_rad) * math.sin(distance / earth_radius) * math.cos(lat_rad),
        math.cos(distance / earth_radius) - math.sin(lat_rad) * math.sin(new_lat_rad)
    )

    # Convert the results back to degrees
    new_lat = math.degrees(new_lat_rad)
    new_lon = math.degrees(new_lon_rad)

    return round(new_lat, 6), round(new_lon, 6)

# Function to upload truck data
def upload_truck_data(truck_id, latitude, longitude):
    payload = {
        "truck_id": truck_id,
        "latitude": latitude,
        "longitude": longitude
    }
    response = requests.post(UPLOAD_TRUCK_DATA_URL, json=payload)
    if response.status_code == 200:
        print(f"Truck data for TruckID {truck_id} uploaded successfully.")
    else:
        print(f"Failed to upload truck data: {response.status_code}, {response.text}")

   
if __name__ == "__main__":
    warehouse_lat = 53.8067097  # Latitude of Leeds city center
    warehouse_lon = -1.5558634  # Longitude of Leeds city center

    min_distance = 100 # 100 meters
    max_distance = 5000 # 5 km
    random_distance = random.randint(min_distance, max_distance)

    truck_id=1

    for truck_id in range (1,2) :
        new_lat, new_lon = generate_coordinate_at_distance(warehouse_lat, warehouse_lon, distance=random_distance)
        upload_truck_data(truck_id, new_lat, new_lon)
    