"""Error handling: exception hierarchy, store errors, config errors, HTTP mapping."""
import logging
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from bitmap_query_service.bitmap_store import load_bitmap, resolve_bitmap_path
from bitmap_query_service.config import get_settings
from bitmap_query_service.errors import (
    BitmapNotFoundError,
    BitmapQueryServiceError,
    BitmapReadError,
    ConfigurationError,
)
from bitmap_query_service.main import app

IRI = "http://example.org/cluster/11111111-1111-1111-1111-111111111111"


@pytest.mark.parametrize("error", [ConfigurationError, BitmapNotFoundError, BitmapReadError])
def test_all_service_errors_share_one_base_class(error):
    assert issubclass(error, BitmapQueryServiceError)


def test_directory_in_place_of_bitmap_is_not_found(tmp_path: Path):
    resolve_bitmap_path(str(tmp_path), IRI, "stable").mkdir()
    with pytest.raises(BitmapNotFoundError) as exc_info:
        load_bitmap(str(tmp_path), IRI, "stable")
    assert isinstance(exc_info.value.__cause__, IsADirectoryError)


@pytest.mark.parametrize(
    "content, cause", [(b"not a bitmap", ValueError), (b"", IndexError)]
)
def test_corrupt_or_empty_bitmap_is_read_error_with_cause(tmp_path: Path, content, cause):
    path = resolve_bitmap_path(str(tmp_path), IRI, "stable")
    path.write_bytes(content)
    with pytest.raises(BitmapReadError) as exc_info:
        load_bitmap(str(tmp_path), IRI, "stable")
    assert exc_info.value.path == path
    assert isinstance(exc_info.value.__cause__, cause)


@pytest.mark.skipif(os.geteuid() == 0, reason="root can read files without permission")
def test_unreadable_bitmap_is_read_error(tmp_path: Path):
    path = resolve_bitmap_path(str(tmp_path), IRI, "stable")
    path.write_bytes(b"x")
    path.chmod(0)
    try:
        with pytest.raises(BitmapReadError, match="could not be read"):
            load_bitmap(str(tmp_path), IRI, "stable")
    finally:
        path.chmod(0o600)


def test_missing_bitmap_dir_setting_is_configuration_error(monkeypatch):
    monkeypatch.delenv("BITMAP_DIR", raising=False)
    with pytest.raises(ConfigurationError, match="BITMAP_DIR"):
        get_settings()


def test_non_integer_port_is_configuration_error(monkeypatch):
    monkeypatch.setenv("BITMAP_DIR", "/tmp")
    monkeypatch.setenv("PORT", "eighty")
    with pytest.raises(ConfigurationError, match="PORT must be an integer, got 'eighty'"):
        get_settings()


def test_corrupt_bitmap_returns_500_without_internals_and_logs_cause(
    tmp_path: Path, monkeypatch, caplog
):
    path = resolve_bitmap_path(str(tmp_path), IRI, "stable")
    path.write_bytes(b"not a bitmap")
    monkeypatch.setenv("BITMAP_DIR", str(tmp_path))
    with caplog.at_level(logging.ERROR), TestClient(app) as client:
        response = client.post(
            "/bitmap/query",
            json={"census_version": "stable", "operation": "lookup", "clusters": [IRI]},
        )
    assert response.status_code == 500
    assert response.json() == {"detail": f"Failed to load bitmap file '{path.name}'."}
    assert str(tmp_path) not in response.text
    assert "not a valid roaring bitmap" in caplog.text
