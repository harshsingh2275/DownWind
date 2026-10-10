"""Script to filter and simplify geoBoundaries ADM1 GeoJSON into region.geojson."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.region import simplify_geojson_geometry


def build_region_geojson(
    input_path: Path,
    output_path: Path,
    target_isos: tuple[str, ...] = ("IN-PB", "IN-HR"),
    tolerance: float = 0.005,
) -> dict[str, object]:
    """Filter features by shapeISO and simplify geometries."""
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    filtered_features = []

    for feat in features:
        props = feat.get("properties", {})
        shape_iso = props.get("shapeISO", "")
        if shape_iso in target_isos:
            simplified_geom = simplify_geojson_geometry(feat["geometry"], tolerance)
            clean_feature = {
                "type": "Feature",
                "properties": {
                    "shapeISO": shape_iso,
                    "shapeName": props.get("shapeName", ""),
                    "source": "geoBoundaries (CC BY 4.0)",
                },
                "geometry": simplified_geom,
            }
            filtered_features.append(clean_feature)

    output_fc = {
        "type": "FeatureCollection",
        "features": filtered_features,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_fc, f, separators=(",", ":"))

    file_size_bytes = output_path.stat().st_size
    return {
        "features_count": len(filtered_features),
        "tolerance": tolerance,
        "file_size_bytes": file_size_bytes,
        "file_size_kb": round(file_size_bytes / 1024, 2),
    }


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    src_file = base_dir / "data" / "geoBoundaries-IND-ADM1_simplified.geojson"
    out_file = base_dir / "data" / "region.geojson"

    result = build_region_geojson(src_file, out_file, tolerance=0.005)
    print("Built region.geojson successfully:")
    print(f"  Features: {result['features_count']}")
    print(f"  Tolerance: {result['tolerance']} deg")
    print(f"  File size: {result['file_size_kb']} KB ({result['file_size_bytes']} bytes)")
