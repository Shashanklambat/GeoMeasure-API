import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.file_handler import validate_kml, extract_shapefile
from app.geo_processor import extract_features

from fastapi.responses import FileResponse


app = FastAPI(title="Geospatial File Measurement API")

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(Path(__file__).parent / "index.html")

# Maximum upload size: 10 MB
MAX_UPLOAD_SIZE = 10 * 1024 * 1024

# Save processed results here while the server is running.
uploaded_files = {}


@app.post("/api/files/", status_code=201)
def upload_file(file: UploadFile = File(...)):
    try:
        # Get the name and extension of the uploaded file.
        filename = file.filename or ""
        filename = filename.replace("\\", "/").split("/")[-1]
        extension = Path(filename).suffix.lower()

        if extension != ".kml" and extension != ".zip":
            raise HTTPException(400, "Only KML and ZIP files are allowed")

        # Read up to 10 MB + 1 byte to check the file size safely.
        file_content = file.file.read(MAX_UPLOAD_SIZE + 1)

        if len(file_content) == 0:
            raise HTTPException(400, "Uploaded file is empty")

        if len(file_content) > MAX_UPLOAD_SIZE:
            raise HTTPException(413, "File size exceeds 10 MB")

        # The temporary folder is deleted after the file is processed.
        with tempfile.TemporaryDirectory() as temp_folder:
            folder = Path(temp_folder)
            file_path = folder / ("upload" + extension)

            with open(file_path, "wb") as saved_file:
                saved_file.write(file_content)

            try:
                # KML files can be read directly.
                if extension == ".kml":
                    validate_kml(file_path)
                    input_path = file_path

                # A Shapefile must be extracted from its ZIP archive.
                else:
                    input_path = extract_shapefile(
                        file_path, folder / "extracted"
                    )

                # Read features and calculate their measurements.
                processed_data = extract_features(input_path)

            except (ValueError, OSError, RuntimeError) as error:
                raise HTTPException(400, str(error)) from error

        # Create a unique ID for this upload.
        file_id = str(uuid.uuid4())

        file_info = {
            "id": file_id,
            "filename": filename,
            "feature_count": processed_data["feature_count"],
            "crs": processed_data["crs"],
            "status": "COMPLETED"
        }

        # Save information and measurements in Python memory.
        uploaded_files[file_id] = {
            "info": file_info,
            "features": processed_data["features"]
        }

        return file_info

    finally:
        file.file.close()


@app.get("/api/files/{file_id}/")
def get_file_info(file_id: str):
    if file_id not in uploaded_files:
        raise HTTPException(404, "File not found")

    return uploaded_files[file_id]["info"]


@app.get("/api/files/{file_id}/measurements/")
def get_file_measurements(file_id: str):
    if file_id not in uploaded_files:
        raise HTTPException(404, "File not found")

    saved_file = uploaded_files[file_id]

    return {
        "file_id": file_id,
        "feature_count": saved_file["info"]["feature_count"],
        "measurements": saved_file["features"]
    }
