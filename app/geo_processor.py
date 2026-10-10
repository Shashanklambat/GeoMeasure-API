import geopandas as gpd
import pyogrio

from app.measurements import calculate_measurement


def extract_features(file_path):
    """Read geographical features from a KML or Shapefile."""
    features = []
    crs_list = []

    # Some files, such as KML, can contain multiple layers.
    layers = pyogrio.list_layers(str(file_path))

    for layer in layers:
        layer_name = layer[0]
        layer_type = layer[1]

        if layer_type is None:
            continue

        data = gpd.read_file(str(file_path), layer=layer_name, engine="pyogrio")

        if data.crs is None:
            raise ValueError("CRS information is missing")

        crs = data.crs.to_string()

        if crs not in crs_list:
            crs_list.append(crs)

        for feature in data.iterfeatures(na="null"):
            geometry = feature["geometry"]

            geometry_type = None
            if geometry is not None:
                geometry_type = geometry["type"]

            measurement = calculate_measurement(geometry, crs)

            feature_result = {
                "feature_id": len(features) + 1,
                "geometry_type": geometry_type,
                "geometry": geometry,
                "crs": crs,
                "properties": feature["properties"],
                "area_m2": measurement["area_m2"],
                "length_m": measurement["length_m"],
                "measurement_crs": measurement["measurement_crs"],
                "measurement_status": measurement["measurement_status"]
            }

            features.append(feature_result)

    if len(features) == 0:
        raise ValueError("No geographical features found")

    # File CRS is shown only if all layers use the same CRS.
    file_crs = None
    if len(crs_list) == 1:
        file_crs = crs_list[0]

    return {
        "feature_count": len(features),
        "crs": file_crs,
        "features": features
    }
