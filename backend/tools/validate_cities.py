"""Validation module and CLI for cities.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Bounding box for India (including territorial waters and islands)
INDIA_LAT_MIN = 6.0
INDIA_LAT_MAX = 38.0
INDIA_LON_MIN = 68.0
INDIA_LON_MAX = 98.0


def validate_city_item(city: dict[str, Any], index: int, seen_ids: set[str]) -> list[str]:
    """Validate a single city dictionary."""
    errors: list[str] = []

    # Required fields
    required_keys = ["id", "name", "state", "lat", "lon", "population", "populationSource"]
    for key in required_keys:
        if key not in city:
            errors.append(f"City at index {index} is missing required field '{key}'")

    if errors:
        return errors

    city_id = city["id"]
    if not isinstance(city_id, str) or not city_id.strip():
        errors.append(f"City at index {index} has invalid or empty id: {city_id!r}")
    elif city_id in seen_ids:
        errors.append(f"Duplicate city id detected at index {index}: {city_id!r}")
    else:
        seen_ids.add(city_id)

    name = city["name"]
    if not isinstance(name, str) or not name.strip():
        errors.append(f"City at index {index} has invalid name: {name!r}")

    state = city["state"]
    if not isinstance(state, str) or not state.strip():
        errors.append(f"City at index {index} has invalid state: {state!r}")

    lat = city["lat"]
    if not isinstance(lat, (int, float)):
        errors.append(f"City '{city_id}' latitude must be numeric, got: {lat!r}")
    elif not (INDIA_LAT_MIN <= float(lat) <= INDIA_LAT_MAX):
        msg = f"City '{city_id}' latitude {lat} outside India [{INDIA_LAT_MIN}, {INDIA_LAT_MAX}]"
        errors.append(msg)

    lon = city["lon"]
    if not isinstance(lon, (int, float)):
        errors.append(f"City '{city_id}' longitude must be numeric, got: {lon!r}")
    elif not (INDIA_LON_MIN <= float(lon) <= INDIA_LON_MAX):
        msg = f"City '{city_id}' longitude {lon} outside India [{INDIA_LON_MIN}, {INDIA_LON_MAX}]"
        errors.append(msg)

    population = city["population"]
    if not isinstance(population, (int, float)) or isinstance(population, bool):
        errors.append(f"City '{city_id}' population must be a positive number, got: {population!r}")
    elif population <= 0:
        errors.append(f"City '{city_id}' population must be greater than 0, got: {population}")

    source = city["populationSource"]
    if not isinstance(source, str) or not source.strip():
        errors.append(f"City '{city_id}' has missing or empty populationSource")

    return errors


def validate_cities_data(data: Any) -> list[str]:
    """Validate a list of city dictionaries."""
    if not isinstance(data, list):
        return ["Root data must be a JSON array of city objects"]

    if len(data) == 0:
        return ["City list cannot be empty"]

    errors: list[str] = []
    seen_ids: set[str] = set()

    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            errors.append(f"Item at index {idx} is not an object")
            continue
        errors.extend(validate_city_item(item, idx, seen_ids))

    return errors


def validate_cities_file(file_path: Path) -> tuple[bool, list[str]]:
    """Validate a cities.json file on disk."""
    if not file_path.exists():
        return False, [f"File not found: {file_path}"]

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        return False, [f"Invalid JSON in {file_path}: {exc}"]

    errors = validate_cities_data(data)
    return len(errors) == 0, errors


if __name__ == "__main__":
    import sys

    target_path = Path(__file__).resolve().parent.parent / "data" / "cities.json"
    if len(sys.argv) > 1:
        target_path = Path(sys.argv[1])

    is_valid, validation_errors = validate_cities_file(target_path)
    if is_valid:
        print(f"SUCCESS: {target_path} is valid!")
        sys.exit(0)
    else:
        print(f"VALIDATION FAILED for {target_path}:")
        for err in validation_errors:
            print(f"  - {err}")
        sys.exit(1)
