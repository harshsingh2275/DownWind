"""Unit tests for cities.json validator."""

from pathlib import Path

from tools.validate_cities import validate_cities_data, validate_cities_file


def test_valid_city_data() -> None:
    valid_data = [
        {
            "id": "chandigarh",
            "name": "Chandigarh",
            "state": "Chandigarh",
            "lat": 30.7333,
            "lon": 76.7794,
            "population": 1055450,
            "populationSource": "https://en.wikipedia.org/wiki/Chandigarh",
        },
        {
            "id": "delhi",
            "name": "Delhi",
            "state": "Delhi",
            "lat": 28.6139,
            "lon": 77.2090,
            "population": 16787941,
            "populationSource": "https://en.wikipedia.org/wiki/Delhi",
        },
    ]
    errors = validate_cities_data(valid_data)
    assert errors == []


def test_duplicate_city_id() -> None:
    data_with_duplicates = [
        {
            "id": "delhi",
            "name": "Delhi",
            "state": "Delhi",
            "lat": 28.61,
            "lon": 77.20,
            "population": 1000000,
            "populationSource": "https://example.com",
        },
        {
            "id": "delhi",
            "name": "New Delhi",
            "state": "Delhi",
            "lat": 28.62,
            "lon": 77.21,
            "population": 1100000,
            "populationSource": "https://example.com",
        },
    ]
    errors = validate_cities_data(data_with_duplicates)
    assert any("Duplicate city id" in e for e in errors)


def test_coordinates_outside_india() -> None:
    data_outside_india = [
        {
            "id": "london",
            "name": "London",
            "state": "UK",
            "lat": 51.5074,  # Outside India
            "lon": -0.1278,  # Outside India
            "population": 8982000,
            "populationSource": "https://example.com",
        }
    ]
    errors = validate_cities_data(data_outside_india)
    assert any("outside India" in e for e in errors)


def test_invalid_population_and_missing_source() -> None:
    bad_data = [
        {
            "id": "amritsar",
            "name": "Amritsar",
            "state": "Punjab",
            "lat": 31.634,
            "lon": 74.872,
            "population": -500,  # Negative
            "populationSource": "",  # Empty
        }
    ]
    errors = validate_cities_data(bad_data)
    assert any("population must be greater than 0" in e for e in errors)
    assert any("missing or empty populationSource" in e for e in errors)


def test_empty_city_list() -> None:
    errors = validate_cities_data([])
    assert "City list cannot be empty" in errors


def test_cities_json_on_disk() -> None:
    cities_path = Path(__file__).resolve().parent.parent / "data" / "cities.json"
    assert cities_path.exists(), "backend/data/cities.json must exist"
    is_valid, errors = validate_cities_file(cities_path)
    assert is_valid, f"Validation failed with errors: {errors}"
    assert len(errors) == 0

