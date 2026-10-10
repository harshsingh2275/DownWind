from src.hello import get_system_status


def test_get_system_status() -> None:
    assert get_system_status() == "ok"
