"""Azure functions for truck location upload and distance calculation from warehouses"""
from datetime import datetime
import logging
import azure.functions as func
import pyodbc
import requests
import json

# Define the Azure Function application
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="uploadTruckData")
def upload_truck_data(req: func.HttpRequest) -> func.HttpResponse:
    """
    Processes HTTP requests to upload truck data to the database.

    The function expects a JSON payload with the following structure:
    {
        "truck_id": 1,
        "latitude": 51.509865,
        "longitude": -0.118092,
        "timestamp": "2024-11-18T10:00:00"
    }

    The data is validated and then inserted into the TruckLocations table
    in the TruckWarehouseMonitor database.
    """
    logging.info("Processing truck data upload request.")

    # Define the connection string for the Azure SQL Database
    connection_string = (
        "Driver={ODBC Driver 18 for SQL Server};"
        "Server=distributed-systems-module-server.database.windows.net,1433;"
        "Database=TruckWarehouseMonitor;"
        "Uid=sc22r2s;"
        "Pwd=Qwertyui123_;"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )

    # Parse and validate the request body
    try:
        req_body = req.get_json()  # Parse JSON from the request
        truck_id = int(req_body.get("truck_id"))  # Extract and validate truck ID
        latitude = float(req_body.get("latitude"))  # Extract and validate latitude
        longitude = float(req_body.get("longitude"))  # Extract and validate longitude
        timestamp = req_body.get("timestamp")  # Extract timestamp

        # Ensure the timestamp is in a valid ISO 8601 format
        datetime.fromisoformat(timestamp)

    except ValueError as e:
        # Handle invalid data formats (e.g., incorrect types or timestamp format)
        logging.error("Invalid data format: %s", e)
        return func.HttpResponse(
            "Invalid data format. Please check your input.",
            status_code=400
        )
    except Exception as e:
        # Handle any other errors during request parsing
        logging.error("Error parsing request body: %s", e)
        return func.HttpResponse(
            "Invalid request body. Please provide truck_id, latitude, "
            "longitude, and timestamp.",
            status_code=400
        )

    # Check for missing parameters
    if not all([truck_id, latitude, longitude, timestamp]):
        return func.HttpResponse(
            "Missing one or more required parameters.",
            status_code=400
        )

    # Insert data into the database
    try:
        # Connect to the database
        connection = pyodbc.connect(connection_string)
        cursor = connection.cursor()

        # SQL query to insert data into the TruckLocations table
        query = """
        INSERT INTO TruckLocations (TruckID, Latitude, Longitude, Timestamp)
        VALUES (?, ?, ?, ?)
        """
        cursor.execute(query, (truck_id, latitude, longitude, timestamp))
        connection.commit()  # Commit the transaction

        logging.info("Data inserted successfully.")
        return func.HttpResponse(
            f"Data for TruckID {truck_id} inserted successfully.",
            status_code=200
        )

    except Exception as e:
        # Log and handle database connection or insertion errors
        logging.error("Error connecting to the database or inserting data: %s", e)
        return func.HttpResponse(
            "An error occurred while processing the request.",
            status_code=500
        )

    finally:
        # Ensure the database connection is closed
        if "connection" in locals() and connection:
            connection.close()


def compare_truck_warehouse_location(payload):
    # function_url = "https://TruckMonitoringSystem.azurewebsites.net/api/compareLocations"
    function_url = "http://localhost:7071/api/compareLocations"

    # Make the POST request
    try:
        response = requests.post(function_url, json=payload)

        # Check the response
        if response.status_code == 200:
            print("Response:", response.text)
        else:
            print(f"Error: {response.status_code} - {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


def fetch_warehouses():
    """
    Fetch all rows from the Warehouses table.

    Returns:
        list: A list of rows, where each row is a tuple containing column values.
    """
    try:
        connection_string = (
        "Driver={ODBC Driver 18 for SQL Server};"
        "Server=distributed-systems-module-server.database.windows.net,1433;"
        "Database=TruckWarehouseMonitor;"
        "Uid=sc22r2s;"
        "Pwd=Qwertyui123_;"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
        )

        # Connect to the database
        connection = pyodbc.connect(connection_string)
        cursor = connection.cursor()

        # SQL query to fetch data from the Warehouses table
        query = "SELECT * FROM Warehouses"
        cursor.execute(query)

        # Fetch all rows from the query result
        rows = cursor.fetchall()

        # Return the rows
        return rows

    except pyodbc.Error as e:
        print("Error:", e)
        return []

    finally:
        # Ensure resources are closed
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()


@app.sql_trigger(arg_name="truckInfo",
                 table_name="TruckLocations",
                 connection_string_setting="SqlConnectionString")
def calculate_truck_data(truckInfo: str) -> None:
    """
    Triggered when changes are detected in the TruckLocations table.

    Args:
        truckInfo (str): JSON payload containing the change details.
    """
    logging.info("SQL Trigger detected changes: %s", truckInfo)

    trucks = json.loads(truckInfo)
    warehouses = fetch_warehouses()

    for index, truck in enumerate(trucks):
        for warehouse in warehouses:

            warehouse_id = warehouse[0]
            warehouse_latitude = warehouse[2]
            warehouse_longitude = warehouse[3]

            payload = {
                "truck_id": truck["Item"]["TruckID"],
                "warehouse_id": warehouse_id,
                "truck_latitude": truck["Item"]["Latitude"],
                "truck_longitude": truck["Item"]["Longitude"],
                "warehouse_latitude": warehouse_latitude,
                "warehouse_longitude": warehouse_longitude
            }

            compare_truck_warehouse_location(payload)


# def haversine(lat1, lon1, lat2, lon2):
#     R = 6371  # Earth radius in kilometers
#     dlat = math.radians(lat2 - lat1)
#     dlon = math.radians(lon2 - lon1)
#     a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
#     c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
#     return R * c


@app.route(route="compareLocations", auth_level=func.AuthLevel.ANONYMOUS)
def compareLocations(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Calculating truck and warehouse distance request.')

    # Parse and validate the request body
    try:
        req_body = req.get_json()  # Parse JSON from the request
        truck_id = int(req_body.get("truck_id"))
        warehouse_id = int(req_body.get("warehouse_id"))
        truck_latitude = float(req_body.get("truck_latitude"))
        truck_longitude = float(req_body.get("truck_longitude"))
        warehouse_latitude = float(req_body.get("warehouse_latitude"))
        warehouse_longitude = float(req_body.get("warehouse_longitude"))

        logging.info(f"{truck_id} {warehouse_id}")

    except ValueError as e:
        # Handle invalid data formats (e.g., incorrect types or timestamp format)
        logging.error("Invalid data format: %s", e)
        return func.HttpResponse(
            "Invalid data format. Please check your input.",
            status_code=400
        )
    except Exception as e:
        # Handle any other errors during request parsing
        logging.error("Error parsing request body: %s", e)
        return func.HttpResponse(
            "Invalid request body. Please provide truck_id, warehouse_id, "
            "truck_latitude, truck_longitude, warehouse_latitude."
            "and warehouse_longitude",
            status_code=400
        )

    return func.HttpResponse(
            f"Comparison for truck: {truck_id} and warehouse {warehouse_id} successful.",
            status_code=200
        )
