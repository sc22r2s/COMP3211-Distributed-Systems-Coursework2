import azure.functions as func
import logging
import pyodbc
from datetime import datetime

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
