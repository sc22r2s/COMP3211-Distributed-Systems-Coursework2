# **Truck Location Management and Distance Calculation**

## Project Description

This project uses Azure Functions to create a serverless architecture for managing truck location data and calculating distances to warehouses. It demonstrates the use of HTTP and SQL triggers to facilitate real-time data processing and interaction with an Azure SQL database.

## Features

- **Serverless Architecture**: Utilizes Azure Functions for scalable, event-driven processing.
- **Real-Time Data Processing**: Employs HTTP and SQL triggers to process truck location updates and warehouse distances dynamically.
- **Azure SQL Database Integration**: Leverages Azure SQL for robust data management and trigger-based actions.
- **Automated Distance Calculation**: Automatically calculates distances using the Haversine formula when new truck location data is added.

## Azure Deployed Functions

### 1. **Upload Truck Data**

- **Trigger**: HTTP POST
- **Endpoint**: `/uploadTruckData`
- **Description**: This function accepts truck location data via HTTP POST requests and stores the data in the `TruckLocations` table of the Azure SQL database.

### 2. **Calculate Truck Data**

- **Trigger**: SQL (On data change in `TruckLocations`)
- **Description**: Triggered by any changes in the `TruckLocations` table, this function fetches corresponding warehouse data and calculates distances if new entry is found.

### 3. **Compare Locations**

- **Trigger**: HTTP POST
- **Endpoint**: `/compareLocations`
- **Description**: This function compares truck and warehouse coordinates to determine proximity and logs the information if specific criteria are met.

## Database Structure and SQL Trigger

The Azure SQL Database contains tables designed to store truck and warehouse data.

### **Truck**

This table stores information about the trucks.

| Column  | Type      | Description                          |
|---------|-----------|--------------------------------------|
| TruckID | `int`     | Unique identifier for the truck.     |
| Name    | `varchar` | Name of the truck.                   |

### **TruckLocations**

This table stores the location data for trucks.

| Column          | Type      | Description                               |
|-----------------|-----------|-------------------------------------------|
| TruckLocationID | `int`     | Unique identifier for truck location data |
| TruckID         | `int`     | Unique identifier for the truck.          |
| Latitude        | `float`   | Latitude of the truck's location.         |
| Longitude       | `float`   | Longitude of the truck's location.        |
| Timestamp       | `datetime`| Timestamp of the data recorded.           |

### **Warehouses**

This table stores information about warehouses.

| Column       | Type      | Description                              |
|--------------|-----------|------------------------------------------|
| WarehouseID  | `int`     | Unique identifier for the warehouse.     |
| Name         | `varchar` | Name of the warehouse.                   |
| Latitude     | `float`   | Latitude of the warehouse's location.    |
| Longitude    | `float`   | Longitude of the warehouse's location.   |

### **MessageQueue**

This table is used to queue messages for processing actions based on the distance calculations.

| Column       | Type       | Description                                      |
|--------------|------------|--------------------------------------------------|
| QueueID      | `int`      | Unique identifier for each queued message.       |
| TruckID      | `int`      | ID of the truck associated with the message.     |
| WarehouseID  | `int`      | ID of the warehouse associated with the message. |
| Distance     | `float`    | Calculated distance between truck and warehouse. |
| Timestamp    | `datetime` | Timestamp when the message was queued.           |

SQL triggers are used to automatically invoke Azure Functions based on data changes:

```sql
ALTER DATABASE [TruckWareHouseMonitor]
SET CHANGE_TRACKING = ON
(CHANGE_RETENTION = 2 DAYS, AUTO_CLEANUP = ON);

ALTER TABLE [dbo].[TruckLocations]
ENABLE CHANGE_TRACKING;
```

### Example SQL Database Connection Strings

These strings should be put stored in the local variables for the program to work. If deploying it in Azure these value should be stored under the 'Environment Variable' section inside your functions app.

```plaintext
"SqlConnectionString": "Server=distributed-systems-module-server.database.windows.net,1433;Database=TruckWarehouseMonitor;Uid=sc22r2s;Pwd=Qwertyui123_;Encrypt=yes;TrustServerCertificate=no;",

"OdbcSqlConnectionString": "Driver={ODBC Driver 18 for SQL Server};Server=distributed-systems-module-server.database.windows.net,1433;Database=TruckWarehouseMonitor;Uid=sc22r2s;Pwd=Qwertyui123_;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
```

## Example Usage of the Project

**Invoke the `uploadTruckData` Function**

To send data to the `uploadTruckData` function via an HTTP POST request using PowerShell, use the following command:

```powershell
Invoke-WebRequest -Uri "https://truckmonitoringsystem.azurewebsites.net/api/uploadTruckData" `
-Method POST `
-Headers @{ "Content-Type" = "application/json" } `
-Body '{"truck_id": 1, "latitude": 53.8085097, "longitude": -1.5528634, "timestamp": "2024-11-18T10:00:00"}'
```

### Process Flow Description

When the PowerShell command is executed to invoke the `uploadTruckData` function:

1. **Data Submission**:
   - The command sends an HTTP POST request to the Azure Function `uploadTruckData` with a JSON payload containing truck data such as truck ID, latitude, longitude, and timestamp.
   - The function receives this data through the request.

2. **Data Storage**:
   - The `uploadTruckData` function processes the incoming JSON payload and inserts the truck location data into the `TruckLocations` table in the Azure SQL Database. This step includes storing the truck ID, geographical coordinates (latitude and longitude), and the timestamp of the data entry.

3. **Trigger Activation**:
   - Once the data is inserted into the `TruckLocations` table, a SQL trigger that has been set up on this table activates. This trigger is configured to detect new inserts to the table.

4. **Distance Calculation**:
   - The triggered function, `calculateTruckData`, then executes. It retrieves the newly added truck location and compares it against all warehouse locations stored in the `Warehouses` table using the Haversine formula to calculate the distance between each pair of truck and warehouse coordinates.

5. **Proximity Check**:
   - For each distance calculation, the function checks if the result is less than or equal to 500 meters.
   - If the calculated distance between a truck and a warehouse is 500 meters or less, this proximity meets the criteria for further action.

6. **Data Logging**:
   - The details of trucks that are within 500 meters of a warehouse are then logged or inserted into another table, such as the `MessageQueue`. This table records the truck ID, warehouse ID, the calculated distance, and the timestamp when this proximity was identified.

7. **Automated Responses**:
   - Depending on additional business logic, further actions may be automated based on these proximity findings, such as sending notifications or alerts to logistics managers or scheduling immediate deliveries or pickups.
