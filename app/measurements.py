import geopandas as gpd
from shapely.geometry import shape


def calculate_measurement(geometry_data, source_crs):
    """Calculate Polygon area or LineString length in metres."""
    result = {
        "area_m2": None,
        "length_m": None,
        "measurement_crs": None,
        "measurement_status": "NOT_REQUIRED"
    }

    if geometry_data is None:
        result["measurement_status"] = "EMPTY_GEOMETRY"
        return result

    # Convert geometry data into a Shapely object.
    try:
        geometry = shape(geometry_data)
    except (ValueError, TypeError, KeyError):
        result["measurement_status"] = "INVALID_GEOMETRY"
        return result

    if geometry.is_empty:
        result["measurement_status"] = "EMPTY_GEOMETRY"
        return result

    if not geometry.is_valid:
        result["measurement_status"] = "INVALID_GEOMETRY"
        return result

    geometry_type = geometry.geom_type

    # The assignment does not require measurements for Points.
    if geometry_type == "Point":
        return result

    # Only Polygon and LineString measurements are required.
    if geometry_type != "Polygon" and geometry_type != "LineString":
        result["measurement_status"] = "UNSUPPORTED_GEOMETRY"
        return result

    try:
        # Tell GeoPandas which CRS the original coordinates use.
        geo_series = gpd.GeoSeries([geometry], crs=source_crs)

        # Get longitude/latitude to check if UTM is suitable.
        geographic = geo_series.to_crs("EPSG:4326")
        bounds = geographic.total_bounds

        min_lon = bounds[0]
        min_lat = bounds[1]
        max_lon = bounds[2]
        max_lat = bounds[3]

        # This simple UTM method is for local and regional features.
        if max_lon - min_lon > 6 or max_lat - min_lat > 6:
            result["measurement_status"] = "UNSUPPORTED_EXTENT"
            return result

        if min_lat < -80 or max_lat > 84:
            result["measurement_status"] = "UNSUPPORTED_EXTENT"
            return result

        # Select a suitable UTM projection with metre units.
        projected_crs = geographic.estimate_utm_crs()

        if projected_crs is None:
            result["measurement_status"] = "CRS_ERROR"
            return result

        # Convert the original geometry into the chosen projected CRS.
        projected = geo_series.to_crs(projected_crs)
        projected_geometry = projected.iloc[0]

    except (ValueError, RuntimeError, TypeError):
        result["measurement_status"] = "CRS_ERROR"
        return result

    result["measurement_crs"] = projected_crs.to_string()

    if geometry_type == "Polygon":
        result["area_m2"] = float(projected_geometry.area)

    if geometry_type == "LineString":
        result["length_m"] = float(projected_geometry.length)

    result["measurement_status"] = "MEASURED"
    return result
