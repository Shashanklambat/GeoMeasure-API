# Geospatial File Measurement API

A lightweight **FastAPI** application that accepts geospatial files, extracts their geographical features, and calculates **polygon area** and **line length** using an appropriate projected coordinate reference system (CRS).

The project implements the three required REST API endpoints. It also includes a small, optional web interface for uploading a file and viewing its information and measurements in separate panels.

## Live Demo

**Website:** https://geomeasure-api-w75x.onrender.com/ <br>
**API Docs:** https://geomeasure-api-w75x.onrender.com/docs

A simple web interface was additionally deployed to make API
testing easier without manually sending requests.

## Features

- Upload **KML (`.kml`)** or **Shapefile ZIP (`.zip`)** files.
- Read geographical features and return their **index, geometry type, geometry, CRS, and properties**.
- Calculate **Polygon area in square metres (m²)** and **LineString length in metres (m)**.
- Return **no measurement for Points** and a clear status for unsupported or invalid geometries.
- Transform supported geometries to a locally estimated **UTM projected CRS** before measuring them.
- Retrieve file information and measurements through separate GET endpoints using a unique file ID.
- Show the results in a simple browser interface, in addition to FastAPI's Swagger UI.

## Technology Stack

| Technology | Purpose |
| --- | --- |
| Python | Application language |
| FastAPI | REST API and file-upload handling |
| Uvicorn | ASGI server |
| Python Multipart | Handling multipart file uploads |
| Pyogrio / GDAL | Discovering and reading geospatial layers |
| GeoPandas | Processing features and transforming coordinates |
| Shapely | Geometry validation, area, and length |
| PyProj / PROJ | CRS definitions and coordinate transformations used by GeoPandas |
| HTML, CSS, JavaScript | Optional browser interface |
| Python standard library | ZIP handling, XML checks, temporary files, and UUIDs |

**No database or frontend framework is required.** Processed results are held in a Python dictionary while the server is running.

## Supported Input Files

| Input | Contents | Notes |
| --- | --- | --- |
| `.kml` | XML-based geographical features such as Points, LineStrings, and Polygons | Must be readable as KML and contain geographical features |
| `.zip` | A Shapefile dataset with matching `.shp`, `.shx`, and `.dbf` components | Include a valid `.prj` file so the application can identify the CRS; `.cpg` is optional |

A Shapefile ZIP might contain:

```text
survey.zip
├── survey.shp   # Geometry
├── survey.shx   # Geometry index
├── survey.dbf   # Attributes
├── survey.prj   # Coordinate reference system
└── survey.cpg   # Optional text encoding
```

The current implementation accepts **one Shapefile per ZIP archive**. It limits the uploaded file to **10 MiB**, the total declared uncompressed ZIP contents to **50 MiB**, and ZIP archives to **50 file entries**.

## Project Structure

```text
geospatial-measurement-api/
├── app/
│   ├── __init__.py
│   ├── main.py            # API endpoints, temporary storage, UI route
│   ├── file_handler.py    # KML validation and Shapefile ZIP extraction
│   ├── geo_processor.py   # Read layers and extract feature information
│   ├── measurements.py    # CRS transformation and area/length calculation
│   └── index.html         # Optional upload/results web interface
├── requirements.txt
└── README.md
```

## Local Setup

### Prerequisites

- **Python 3.12** is recommended.
- An internet connection to install the Python dependencies.
- A terminal such as **PowerShell**, Command Prompt, or a terminal in VS Code.

### 1. Get the project

Clone your public GitHub repository or download its ZIP, then open a terminal in the folder containing `requirements.txt`.

### 2. Create and activate a virtual environment

**Windows (PowerShell):**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the API

Run the following command from the project root:

```bash
uvicorn app.main:app --reload
```
or
```bash
cd app
uvicorn main:app --reload
```

Open:

- **Web interface:** http://127.0.0.1:8000/
- **Interactive API documentation (Swagger UI):** http://127.0.0.1:8000/docs
- **OpenAPI specification:** http://127.0.0.1:8000/openapi.json

Use `Ctrl + C` in the terminal to stop the server. The `--reload` option is intended for local development.

> **Note:** Results are stored in process memory. Restarting the server clears previously uploaded results, so old IDs will no longer be found.

## Using the Web Interface

1. Open http://127.0.0.1:8000/.
2. Choose a `.kml` file or a `.zip` containing a Shapefile.
3. Select **Upload and Measure**.
4. View **File Information** and **Feature Measurements** in separate panels.
5. For each feature, the page highlights the calculated **area** or **length**; additional geometry details are also available.

The page calls the same three REST endpoints documented below. It does not perform its own geographical calculations.

## REST API Reference

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/files/` | Upload, validate, process, and measure a file |
| `GET` | `/api/files/{file_id}/` | Retrieve the uploaded file's information |
| `GET` | `/api/files/{file_id}/measurements/` | Retrieve the file's features and measurement results |

### 1. Upload a file

**Request:** `POST /api/files/`  
**Content type:** `multipart/form-data`  
**Required field:** `file`

Example using `curl` (replace the path with an existing file):

```bash
curl -X POST "http://127.0.0.1:8000/api/files/" \
  -F "file=@survey.kml"
```

On Windows PowerShell, use `curl.exe` instead of the `curl` alias if necessary:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/files/" -F "file=@survey.kml"
```

**Example response — `201 Created`:**

```json
{
  "id": "2469d80a-5dee-47ad-a932-ca4feee18828",
  "filename": "survey.kml",
  "feature_count": 3,
  "crs": "EPSG:4326",
  "status": "COMPLETED"
}
```

The ID is a generated UUID and will be different for each successful upload. The upload is fully processed before this response is returned.

### 2. Retrieve file information

**Request:** `GET /api/files/{file_id}/`

```bash
curl "http://127.0.0.1:8000/api/files/2469d80a-5dee-47ad-a932-ca4feee18828/"
```

**Example response — `200 OK`:**

```json
{
  "id": "2469d80a-5dee-47ad-a932-ca4feee18828",
  "filename": "survey.kml",
  "feature_count": 3,
  "crs": "EPSG:4326",
  "status": "COMPLETED"
}
```

The GET response intentionally contains the same metadata returned by POST: POST creates the processed record; GET retrieves it without uploading or processing the file again.

### 3. Retrieve feature measurements

**Request:** `GET /api/files/{file_id}/measurements/`

```bash
curl "http://127.0.0.1:8000/api/files/2469d80a-5dee-47ad-a932-ca4feee18828/measurements/"
```

**Example response — `200 OK`:**

The following example illustrates a three-feature KML dataset. Properties vary based on the uploaded file; additional attributes may be present.

```json
{
  "file_id": "2469d80a-5dee-47ad-a932-ca4feee18828",
  "feature_count": 3,
  "measurements": [
    {
      "feature_id": 1,
      "geometry_type": "Polygon",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [79.08, 21.14, 0.0],
          [79.081, 21.14, 0.0],
          [79.081, 21.141, 0.0],
          [79.08, 21.141, 0.0],
          [79.08, 21.14, 0.0]
        ]]
      },
      "crs": "EPSG:4326",
      "properties": {"Name": "Test polygon"},
      "area_m2": 11502.77,
      "length_m": null,
      "measurement_crs": "EPSG:32644",
      "measurement_status": "MEASURED"
    },
    {
      "feature_id": 2,
      "geometry_type": "LineString",
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [79.08, 21.14, 0.0],
          [79.081, 21.141, 0.0]
        ]
      },
      "crs": "EPSG:4326",
      "properties": {"Name": "Test line"},
      "area_m2": null,
      "length_m": 151.83,
      "measurement_crs": "EPSG:32644",
      "measurement_status": "MEASURED"
    },
    {
      "feature_id": 3,
      "geometry_type": "Point",
      "geometry": {
        "type": "Point",
        "coordinates": [79.0882, 21.1458, 0.0]
      },
      "crs": "EPSG:4326",
      "properties": {"Name": "Test point"},
      "area_m2": null,
      "length_m": null,
      "measurement_crs": null,
      "measurement_status": "NOT_REQUIRED"
    }
  ]
}
```

The example measurements are rounded for readability. Actual API responses contain the full calculated floating-point values and the properties extracted from the input file.

### Measurement Rules

| Geometry type | Action | Output |
| --- | --- | --- |
| `Polygon` | Calculate projected planar area | `area_m2` |
| `LineString` | Calculate projected planar length | `length_m` |
| `Point` | No calculation | `NOT_REQUIRED` |
| Other types (e.g. `MultiPoint`) | No calculation | `UNSUPPORTED_GEOMETRY` |

Each returned feature includes its index, geometry type, original geometry, original CRS, properties, and measurement details. A file can have `status: "COMPLETED"` even when an individual feature has an unsupported measurement type: the two statuses describe different stages of processing.

### Measurement Status Values

| Value | Meaning |
| --- | --- |
| `MEASURED` | Area or length calculated successfully |
| `NOT_REQUIRED` | A Point does not need a measurement |
| `EMPTY_GEOMETRY` | Geometry is missing or empty |
| `INVALID_GEOMETRY` | Geometry failed a supported validity check |
| `UNSUPPORTED_GEOMETRY` | Geometry type is not measured by this implementation |
| `UNSUPPORTED_EXTENT` | Geometry lies outside the current UTM strategy's supported extent |
| `CRS_ERROR` | A handled CRS selection or transformation operation failed |

### HTTP Errors

| HTTP status | Example situation |
| --- | --- |
| `400 Bad Request` | Unsupported extension, invalid KML, invalid ZIP, missing Shapefile components, or unusable CRS |
| `404 Not Found` | The requested file ID does not exist in memory |
| `413 Request Entity Too Large` | Uploaded file exceeds 10 MiB |
| `500 Internal Server Error` | An unexpected server-side error |

Example invalid-upload response:

```json
{
  "detail": "Invalid KML file"
}
```

## Architecture and Processing Flow

```text
User / Web Interface / Swagger UI
                |
                v
        POST /api/files/
                |
                v
           app/main.py
    Check type and upload size
    Save to temporary directory
                |
                v
        app/file_handler.py
    Validate KML / Extract ZIP
                |
                v
        app/geo_processor.py
    Read layers and features
                |
                v
         app/measurements.py
    Validate geometry
    Select projected CRS
    Calculate area or length
                |
                v
       Python dictionary (RAM)
    File UUID -> info + features
          /                 \
         v                   v
GET /api/files/{id}/     GET /api/files/{id}/measurements/
     File info               Feature measurements
```

### File Processing

1. FastAPI receives an uploaded `.kml` or `.zip` file and checks its extension, size, and whether it is empty.
2. A temporary directory is created. KML is checked for a valid XML/KML root; a Shapefile ZIP is inspected and its matching components are extracted.
3. Pyogrio discovers geographical layers, and GeoPandas reads them.
4. For each feature, the application records a sequential **feature index**, geometry type, geometry, original CRS, and properties.
5. The measurement function handles supported geometry types and returns a measurement result or descriptive status.
6. The original temporary files are removed. Processed results are stored under a generated UUID and are available to both GET endpoints.

### Measurement and CRS Handling

Geographic CRSs such as **EPSG:4326** use longitude and latitude **degrees**. Treating degrees as metres would produce incorrect area and length values.

For each measurable Polygon or LineString, the application:

1. Creates a GeoPandas `GeoSeries` using the input feature's original CRS.
2. Transforms a copy to EPSG:4326 to inspect its geographic bounds.
3. Rejects extents wider than **6° longitude or 6° latitude**, and latitudes outside **-80° to +84°**, as unsupported by the current approach.
4. Calls `estimate_utm_crs()` to select a local UTM projected CRS.
5. Transforms the geometry to that CRS using `to_crs()`.
6. Uses Shapely's `.area` for Polygons or `.length` for LineStrings.

The result is reported in **m²** or **m**, alongside the selected `measurement_crs`. For example, a small feature near Nagpur, India may use **EPSG:32644**.

**Accuracy note:** This per-feature UTM strategy is intended for local/regional geometries. A 6° extent check is a practical limit, **not a guarantee** that a feature fits entirely within one UTM zone or that distortion is negligible. Large, polar, or date-line-crossing geometries need a more advanced measurement strategy.

## Design Decisions and Alternatives

| Decision | Reason | Alternative considered |
| --- | --- | --- |
| **FastAPI** | Lightweight API framework with built-in interactive documentation | Django REST Framework |
| **GeoPandas + Pyogrio** | Read KML/Shapefile data and their attributes without writing format parsers | Manual parsing and lower-level GIS library calls |
| **Shapely** | Established library for validity checks and planar geometry operations | Implementing geometry algorithms manually |
| **Per-feature UTM projection** | Allows metre-based calculation for supported local/regional features | Geodesic measurements or alternative projections for other extents |
| **In-memory dictionary** | Keeps the assignment small, with no database configuration | PostgreSQL or SQLite for persistence |
| **Temporary file processing** | Avoids retaining original uploads after processing | Permanent uploaded-file storage |
| **Plain HTML/CSS/JavaScript UI** | Adds an optional demonstration page without a frontend build system | React or other frontend frameworks |

## Verification

You can test the application through the web page or http://127.0.0.1:8000/docs.

Recommended manual checks:

1. Upload a valid KML containing Polygon, LineString, and Point geometries.
2. Upload a valid Shapefile ZIP with `.shp`, `.shx`, `.dbf`, and `.prj` files.
3. Confirm that POST returns a UUID and file information, then use that UUID in both GET endpoints.
4. Check that Polygon area is returned in m², LineString length in m, and Point values are `null` with `NOT_REQUIRED`.
5. Check that the original CRS and the selected projected measurement CRS are reported.
6. Try invalid KML, corrupt/incomplete ZIP archives, an unsupported extension, and an unknown file ID; confirm appropriate errors.

For a simple numeric reference, a 10 m × 10 m square defined in **EPSG:32644** should have an area of approximately **100 m²**.

## Known Limitations

- **Non-persistent results:** The dictionary is cleared when the FastAPI process restarts. Previously returned IDs then produce `404`.
- **Single-process storage:** Independent server workers do not share this dictionary. Run one worker for this implementation.
- **No automatic cleanup of saved results:** Processed features remain in memory until the process stops, so long-running public deployments may use increasing memory.
- **Limited projection strategy:** The chosen UTM approach is not suitable for every geographic extent or geometry.
- **Input restrictions:** One Shapefile per ZIP and a known CRS are required by this implementation.
- **Basic validation:** XML and ZIP checks are useful but are not a full security audit or a complete KML/Shapefile specification validator.

## Learning Outcomes

This project demonstrates practical use of:

- Designing REST endpoints and handling uploaded files with FastAPI.
- Working with KML, Shapefiles, layers, geometry types, and feature attributes.
- Understanding geographic vs. projected coordinate reference systems.
- Transforming coordinates before calculating area and length.
- Separating file handling, geospatial processing, measurement logic, and API routing into readable modules.
- Making implementation trade-offs between simplicity, persistence, accuracy, and operational reliability.

## Future Scope

- Add persistent storage for file information and measurement results.
- Support additional geometry types, such as MultiPolygon and MultiLineString.
- Use projection-aware or geodesic measurement strategies for larger and more complex geographic extents.
- Add automated API and geometry tests, broader error handling, and stronger archive validation.
- Add result expiration, upload quotas, and other safeguards for public deployment.
- Support exporting the processed feature results.
