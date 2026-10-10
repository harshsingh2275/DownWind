import json
from pathlib import Path

from src.region import (
    is_point_in_geojson,
    point_in_polygon,
    simplify_geojson_geometry,
    simplify_ring,
)


def test_point_in_polygon_basic() -> None:
    # A box around 74.0 to 77.0 lon, 29.0 to 32.0 lat (representative of Punjab/Haryana area)
    box_coords = [
        [
            [74.0, 29.0],
            [77.0, 29.0],
            [77.0, 32.0],
            [74.0, 32.0],
            [74.0, 29.0],
        ]
    ]

    # Clearly inside
    assert point_in_polygon(lon=75.5, lat=30.5, coordinates=box_coords) is True

    # Clearly outside
    assert point_in_polygon(lon=78.0, lat=30.5, coordinates=box_coords) is False
    assert point_in_polygon(lon=73.0, lat=30.5, coordinates=box_coords) is False
    assert point_in_polygon(lon=75.5, lat=33.0, coordinates=box_coords) is False
    assert point_in_polygon(lon=75.5, lat=28.0, coordinates=box_coords) is False


def test_near_border_classification() -> None:
    box_coords = [
        [
            [74.0, 29.0],
            [77.0, 29.0],
            [77.0, 32.0],
            [74.0, 32.0],
            [74.0, 29.0],
        ]
    ]

    # Just inside the boundary (by 0.001 deg ~ 100 meters)
    assert point_in_polygon(lon=74.001, lat=30.5, coordinates=box_coords) is True
    assert point_in_polygon(lon=76.999, lat=30.5, coordinates=box_coords) is True

    # Just outside the boundary (by 0.001 deg)
    assert point_in_polygon(lon=73.999, lat=30.5, coordinates=box_coords) is False
    assert point_in_polygon(lon=77.001, lat=30.5, coordinates=box_coords) is False


def test_geojson_feature_collection() -> None:
    feature_collection = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "PunjabBox"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [74.0, 30.0],
                            [76.0, 30.0],
                            [76.0, 32.0],
                            [74.0, 32.0],
                            [74.0, 30.0],
                        ]
                    ],
                },
            },
            {
                "type": "Feature",
                "properties": {"name": "HaryanaBox"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [76.0, 28.0],
                            [78.0, 28.0],
                            [78.0, 30.0],
                            [76.0, 30.0],
                            [76.0, 28.0],
                        ]
                    ],
                },
            },
        ],
    }

    # Point in PunjabBox
    assert is_point_in_geojson(lat=31.0, lon=75.0, geojson_data=feature_collection) is True
    # Point in HaryanaBox
    assert is_point_in_geojson(lat=29.0, lon=77.0, geojson_data=feature_collection) is True
    # Point outside both boxes
    assert is_point_in_geojson(lat=27.0, lon=75.0, geojson_data=feature_collection) is False


def test_simplification_reduces_points() -> None:
    # A ring with many co-linear points
    ring = [
        [0.0, 0.0],
        [1.0, 0.001],
        [2.0, -0.001],
        [3.0, 0.0],
        [3.0, 3.0],
        [0.0, 3.0],
        [0.0, 0.0],
    ]
    simplified = simplify_ring(ring, tolerance=0.01)
    assert len(simplified) < len(ring)
    assert simplified[0] == simplified[-1]  # Must remain closed


def test_simplify_geojson_geometry() -> None:
    geometry = {
        "type": "Polygon",
        "coordinates": [
            [
                [0.0, 0.0],
                [1.0, 0.001],
                [2.0, 0.0],
                [2.0, 2.0],
                [0.0, 2.0],
                [0.0, 0.0],
            ]
        ],
    }
    simplified_geom = simplify_geojson_geometry(geometry, tolerance=0.01)
    assert simplified_geom["type"] == "Polygon"
    assert len(simplified_geom["coordinates"][0]) < len(geometry["coordinates"][0])


def test_region_geojson_real_cities() -> None:
    data_path = Path(__file__).resolve().parent.parent / "data" / "region.geojson"
    assert data_path.exists(), f"region.geojson not found at {data_path}"
    with open(data_path, "r", encoding="utf-8") as f:
        region_data = json.load(f)

    # Clearly inside Punjab/Haryana (shapeISO IN-PB, IN-HR)
    # Ludhiana (PB), Karnal (HR), Hisar (HR)
    assert is_point_in_geojson(lat=30.91, lon=75.85, geojson_data=region_data) is True
    assert is_point_in_geojson(lat=29.69, lon=76.99, geojson_data=region_data) is True
    assert is_point_in_geojson(lat=29.15, lon=75.70, geojson_data=region_data) is True

    # Clearly outside Punjab/Haryana
    # Delhi, Ghaziabad (UP), Lahore (PK)
    assert is_point_in_geojson(lat=28.61, lon=77.23, geojson_data=region_data) is False
    assert is_point_in_geojson(lat=28.67, lon=77.42, geojson_data=region_data) is False
    assert is_point_in_geojson(lat=31.55, lon=74.34, geojson_data=region_data) is False

