"""
Azure Functions for Truck Location Management and Distance Calculation.

This module implements a serverless workflow using Microsoft Azure Functions
to manage truck location data and calculate distances to warehouses. It demonstrates
event-driven architectures with HTTP and SQL triggers.

### Workflow:
1. **Data Upload (`upload_truck_data`)**:
   - HTTP-triggered function to validate and store truck location data in Azure SQL.

2. **Distance Calculation (`calculate_truck_data`)**:
   - SQL-triggered function to process new truck data, compute distances to warehouses,
     and invoke further actions for close-proximity trucks.

3. **Comparison (`compare_locations`)**:
   - HTTP-triggered function to calculate and log truck-to-warehouse distances.

### Features:
- Serverless design using Azure Functions.
- Integration with Azure SQL Database.
- Distance computation with the Haversine formula.
- Scalable, modular, and extensible design.
"""

from datetime import datetime
import json
import logging
import math
import os

import azure.functions as func
import pyodbc
import requests


# Define the Azure Function application
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

def get_sql_connection_string() -> str:
    """
    Retrieve the SQL connection string from environment variables.

    Returns:
        str: The ODBC SQL connection string required to connect to the database.
    """
    return os.environ["OdbcSqlConnectionString"]


@app.route(route="uploadTruckData")
def upload_truck_data(req: func.HttpRequest) -> func.HttpResponse:
    """
    Processes HTTP requests to upload truck data to the database.

    The function expects a JSON payload with the following structure:
    {
        "truck_id": int,
        "latitude": float,
        "longitude": float,
        "timestamp": str (ISO 8601 format)
    }

    The data is validated and inserted into the TruckLocations table.

    Args:
        req (func.HttpRequest): The HTTP request containing the truck data.

    Returns:
        func.HttpResponse: Success or error message with appropriate status code.
    """
    logging.info("Processing truck data upload request.")

    # Get the SQL connection string
    connection_string = get_sql_connection_string()

    # Parse and validate the request body
    try:
        req_body = req.get_json()
        truck_id = int(req_body.get("truck_id"))
        latitude = float(req_body.get("latitude"))
        longitude = float(req_body.get("longitude"))
        timestamp = req_body.get("timestamp")

        # Ensure the timestamp is in a valid ISO 8601 format
        datetime.fromisoformat(timestamp)

    except (ValueError, TypeError) as e:
        logging.error("Invalid data format: %s", e)
        return func.HttpResponse(
            "Invalid data format. Please check your input.",
            status_code=400
        )

    # Ensure all required parameters are provided
    if not all([truck_id, latitude, longitude, timestamp]):
        return func.HttpResponse(
            "Missing one or more required parameters.",
            status_code=400
        )

    # Insert data into the database
    try:
        with pyodbc.connect(connection_string) as connection:
            with connection.cursor() as cursor:
                query = """
                INSERT INTO TruckLocations (TruckID, Latitude, Longitude, Timestamp)
                VALUES (?, ?, ?, ?)
                """
                cursor.execute(query, (truck_id, latitude, longitude, timestamp))
                connection.commit()

        logging.info("Truck location data inserted successfully.")
        return func.HttpResponse(
            f"Data for TruckID {truck_id} inserted successfully.",
            status_code=200
        )

    except pyodbc.Error as e:
        logging.error("Error interacting with the database: %s", e)
        return func.HttpResponse(
            "Database error occurred. Please try again later.",
            status_code=500
        )


def compare_truck_warehouse_location(payload: dict):
    """
    Sends a POST request to compare truck and warehouse locations.

    Args:
        payload (dict): A dictionary containing truck and warehouse data.

    The payload should include:
    {
        "truck_id": int,
        "warehouse_id": int,
        "truck_latitude": float,
        "truck_longitude": float,
        "warehouse_latitude": float,
        "warehouse_longitude": float
    }
    """
    function_url = "https://TruckMonitoringSystem.azurewebsites.net/api/compareLocations"
    # function_url = "http://localhost:7071/api/compareLocations"

    try:
        response = requests.post(function_url, json=payload)

        if response.status_code == 200:
            logging.info("Response from comparison API: %s", response.text)
        else:
            logging.error("Comparison API error: %s - %s", response.status_code, response.text)

    except requests.exceptions.RequestException as e:
        logging.error("Error occurred during the request: %s", e)


def fetch_warehouses():
    """
    Fetch all rows from the Warehouses table in the database.

    The table structure is assumed to include:
    - WarehouseID (int): The unique ID of the warehouse.
    - Name (str): The name of the warehouse.
    - Latitude (float): The latitude of the warehouse's location.
    - Longitude (float): The longitude of the warehouse's location.

    Returns:
        list[tuple]: A list of rows, where each row is a tuple containing column values
                     (e.g., WarehouseID, Name, Latitude, Longitude).
    """
    try:
        connection_string = get_sql_connection_string()

        # Connect to the database
        with pyodbc.connect(connection_string) as connection:
            with connection.cursor() as cursor:
                # SQL query to fetch data from the Warehouses table
                query = "SELECT WarehouseID, Name, Latitude, Longitude FROM Warehouses"
                cursor.execute(query)

                # Fetch all rows from the query result
                rows = cursor.fetchall()

        return rows

    except pyodbc.Error as e:
        logging.error("Database error while fetching warehouses: %s", e)
        return []


@app.sql_trigger(
    arg_name="truckInfo",
    table_name="TruckLocations",
    connection_string_setting="SqlConnectionString"
)
def calculate_truck_data(truckInfo: str) -> None:
    """
    Triggered when changes are detected in the TruckLocations table.

    Processes only INSERT operations and compares truck locations with all warehouses.

    Args:
        truckInfo (str): JSON payload containing the change details.
    """
    logging.info("SQL Trigger detected changes: %s", truckInfo)

    # Parse the truck data from the trigger payload
    trucks = json.loads(truckInfo)

    # Fetch warehouse data from the database
    warehouses = fetch_warehouses()

    for truck in trucks:
        if truck.get("Operation") == 0:  # Operation 0 indicates an INSERT
            for warehouse in warehouses:
                # Map warehouse data to descriptive variables
                warehouse_id = warehouse[0]
                warehouse_latitude = warehouse[2]
                warehouse_longitude = warehouse[3]

                # Map truck data to descriptive variables
                truck_id = truck["Item"]["TruckID"]
                truck_latitude = truck["Item"]["Latitude"]
                truck_longitude = truck["Item"]["Longitude"]

                # Prepare the payload for the comparison function
                payload = {
                    "truck_id": truck_id,
                    "warehouse_id": warehouse_id,
                    "truck_latitude": truck_latitude,
                    "truck_longitude": truck_longitude,
                    "warehouse_latitude": warehouse_latitude,
                    "warehouse_longitude": warehouse_longitude
                }

                # Compare truck and warehouse locations
                compare_truck_warehouse_location(payload)



def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on the Earth's surface.

    The calculation uses the Haversine formula to account for Earth's curvature.

    Args:
        lat1 (float): Latitude of the first point in degrees.
        lon1 (float): Longitude of the first point in degrees.
        lat2 (float): Latitude of the second point in degrees.
        lon2 (float): Longitude of the second point in degrees.

    Returns:
        float: The distance between the two points in kilometers.
    """
    R = 6371.0  # Earth's radius in kilometers

    # Convert latitude and longitude differences to radians
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    # Apply the Haversine formula
    a = (math.sin(dlat / 2)**2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(dlon / 2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Calculate and return the distance
    return R * c


def insert_message_queue(truck_id: int, warehouse_id: int, distance: float) -> None:
    """
    Insert a new record into the MessageQueue table.

    Args:
        truck_id (int): The ID of the truck.
        warehouse_id (int): The ID of the warehouse.
        distance (float): The distance between the truck and the warehouse in kilometers.
    """
    try:
        connection_string = get_sql_connection_string()

        # Connect to the database and insert data
        with pyodbc.connect(connection_string) as connection:
            with connection.cursor() as cursor:
                query = """
                INSERT INTO MessageQueue (TruckID, WarehouseID, Distance)
                VALUES (?, ?, ?);
                """
                cursor.execute(query, (truck_id, warehouse_id, distance))
                connection.commit()

        logging.info("Record successfully inserted into MessageQueue: TruckID=%s, WarehouseID=%s, Distance=%.2f km",
                     truck_id, warehouse_id, distance)

    except pyodbc.Error as e:
        logging.error("Error inserting data into MessageQueue: %s", e)


@app.route(route="compareLocations", auth_level=func.AuthLevel.ANONYMOUS)
def compare_locations(req: func.HttpRequest) -> func.HttpResponse:
    """
    Handle requests to calculate the distance between a truck and a warehouse,
    and trigger actions if the distance is within a specified threshold.

    Args:
        req (func.HttpRequest): The HTTP request containing the truck and warehouse details.

    Returns:
        func.HttpResponse: A response indicating success or failure.
    """
    logging.info("Calculating truck and warehouse distance request.")

    try:
        # Parse and validate the request body
        req_body = req.get_json()

        # Extract and validate required parameters
        truck_id = int(req_body.get("truck_id"))
        warehouse_id = int(req_body.get("warehouse_id"))
        truck_latitude = float(req_body.get("truck_latitude"))
        truck_longitude = float(req_body.get("truck_longitude"))
        warehouse_latitude = float(req_body.get("warehouse_latitude"))
        warehouse_longitude = float(req_body.get("warehouse_longitude"))

        # Calculate the distance using the Haversine formula
        distance = haversine(truck_latitude, truck_longitude,
                             warehouse_latitude, warehouse_longitude)

        logging.info(
            "Truck ID: %s, Warehouse ID: %s, Distance: %.3f km",
            truck_id, warehouse_id, distance
        )

        # Trigger action if distance is within the threshold (e.g., <= 0.5 km)
        if distance <= 0.5:
            logging.info("Distance within threshold. Adding to MessageQueue.")
            insert_message_queue(truck_id, warehouse_id, distance)
        else:
            logging.info("Distance exceeds threshold. No action required.")

        # Return success response
        return func.HttpResponse(
            f"Comparison for truck {truck_id} and warehouse {warehouse_id} successful.",
            status_code=200
        )

    except (ValueError, TypeError) as e:
        # Log and return an error response for invalid input data
        logging.error("Invalid data format: %s", e)
        return func.HttpResponse(
            "Invalid data format. Please check your input.",
            status_code=400
        )
    except Exception as e:
        # Log and return a general error response
        logging.error("Error processing the request: %s", e)
        return func.HttpResponse(
            "An error occurred while processing the request. Please try again later.",
            status_code=500
        )
