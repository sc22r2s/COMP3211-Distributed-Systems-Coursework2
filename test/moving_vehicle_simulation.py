import requests
import math
import random
import time
import datetime

# URL for uploading truck data
# UPLOAD_TRUCK_DATA_URL = "https://TruckMonitoringSystem.azurewebsites.net/api/uploadTruckData"
UPLOAD_TRUCK_DATA_URL= "http://localhost:7071/api/uploadTruckData"


def generate_coordinate_at_distance(lat, lon, distance=100, bearing=0):
    """
    Generate a GPS coordinate a specified distance away from a given location.

    :param lat: Latitude of the starting point in degrees.
    :param lon: Longitude of the starting point in degrees.
    :param distance: Distance in meters (default is 100).
    :param bearing: Bearing in degrees (default is 0, which is north).
    :return: Tuple containing the new latitude and longitude.
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


def upload_truck_data(truck_id, latitude, longitude):
    """
    Upload truck data to the server and measure execution time.

    :param truck_id: Unique identifier for the truck.
    :param latitude: Latitude of the truck's location.
    :param longitude: Longitude of the truck's location.
    :return: Execution time in seconds.
    """
    payload = {
        "truck_id": truck_id,
        "latitude": latitude,
        "longitude": longitude
    }

    try:
        # Start timing the request
        start_time = time.time()

        # Send the HTTP request
        response = requests.post(UPLOAD_TRUCK_DATA_URL, json=payload)

        # Stop timing
        end_time = time.time()

        # Calculate execution time
        execution_time = end_time - start_time

        # Print the result
        if response.status_code == 200:
            print(
                f"Truck data for TruckID {truck_id} uploaded successfully. "
                f"Execution time: {execution_time:.2f} seconds."
            )
        else:
            print(
                f"Failed to upload truck data for TruckID {truck_id}: "
                f"HTTP {response.status_code}, Response: {response.text}"
            )

        return execution_time

    except requests.RequestException as e:
        print(f"Error while uploading truck data for TruckID {truck_id}: {e}")
        return None


if __name__ == "__main__":
    # Warehouse coordinates (e.g., Leeds city center)
    warehouse_lat = 53.8067097
    warehouse_lon = -1.5558634

    # Define distance range in meters for random coordinate generation
    min_distance = 100  # Minimum distance of 100 meters
    max_distance = 5000  # Maximum distance of 5 kilometers

    # Truck ID for data upload
    truck_id = 1

    # Simulate uploading data for n locations
    for i in range(1, 1001):
        # Generate random distance and compute new coordinates
        random_distance = random.randint(min_distance, max_distance)
        new_lat, new_lon = generate_coordinate_at_distance(
            warehouse_lat, warehouse_lon, distance=random_distance
        )

        # Upload the generated truck data and record execution time
        upload_truck_data(truck_id, new_lat, new_lon)
