import shutil
import xml.etree.ElementTree as ET
from pathlib import PurePosixPath
from zipfile import ZipFile, BadZipFile


# Limits for the contents of a ZIP file.
MAX_ZIP_SIZE = 50 * 1024 * 1024
MAX_ZIP_FILES = 50


def validate_kml(file_path):
    """Check that a KML file contains valid XML and a KML root tag."""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError:
        raise ValueError("Invalid KML file")

    # A KML tag may look like {namespace}kml.
    root_name = root.tag.split("}")[-1]

    if root_name != "kml":
        raise ValueError("File is not a KML document")

    return True


def extract_shapefile(zip_path, output_folder):
    """Extract one Shapefile and return the path to its .shp file."""
    try:
        with ZipFile(zip_path) as archive:
            files = []
            total_size = 0

            # Read the list of files inside the ZIP archive.
            for item in archive.infolist():
                if item.is_dir():
                    continue

                name = item.filename
                parts = PurePosixPath(name).parts

                # Do not accept unsafe paths from uploaded ZIP files.
                if name.startswith("/") or "\\" in name or ":" in name:
                    raise ValueError("Unsafe ZIP file path")
                if ".." in parts:
                    raise ValueError("Unsafe ZIP file path")

                files.append(item)
                total_size += item.file_size

            if len(files) == 0 or len(files) > MAX_ZIP_FILES:
                raise ValueError("Invalid ZIP file structure")

            if total_size > MAX_ZIP_SIZE:
                raise ValueError("ZIP contents are too large")

            # Find the .shp file. We accept one Shapefile per ZIP.
            shapefiles = []
            for item in files:
                file_name = PurePosixPath(item.filename)
                if file_name.suffix.lower() == ".shp":
                    shapefiles.append(item)

            if len(shapefiles) != 1:
                raise ValueError("ZIP must contain exactly one Shapefile")

            shp_name = PurePosixPath(shapefiles[0].filename)
            selected_files = []
            found_extensions = []

            # Find the components that belong to this Shapefile.
            for item in files:
                file_name = PurePosixPath(item.filename)
                extension = file_name.suffix.lower()

                if file_name.parent != shp_name.parent:
                    continue
                if file_name.stem.lower() != shp_name.stem.lower():
                    continue
                if extension not in [".shp", ".shx", ".dbf", ".prj", ".cpg"]:
                    continue

                if extension in found_extensions:
                    raise ValueError("Duplicate Shapefile component: " + extension)

                found_extensions.append(extension)
                selected_files.append(item)

            # These three files are required for a Shapefile.
            for extension in [".shp", ".shx", ".dbf"]:
                if extension not in found_extensions:
                    raise ValueError("Missing Shapefile component: " + extension)

            # Our processor also needs CRS information, usually from .prj.
            output_folder.mkdir(parents=True, exist_ok=True)

            for item in selected_files:
                file_name = PurePosixPath(item.filename).name
                output_path = output_folder / file_name

                with archive.open(item) as source_file:
                    with open(output_path, "wb") as saved_file:
                        shutil.copyfileobj(source_file, saved_file)

            return output_folder / shp_name.name

    except (BadZipFile, RuntimeError, NotImplementedError):
        raise ValueError("Invalid or unreadable ZIP archive")
