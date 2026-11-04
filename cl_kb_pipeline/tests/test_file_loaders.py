import pytest

from utils.schema_test_tools import get_json_from_file, get_yaml_from_file


def test_yaml_loads_valid_file(tmp_path):
    path = tmp_path / "ok.yaml"
    path.write_text("a: 1\nb: [x, y]\n")
    assert get_yaml_from_file(str(path)) == {"a": 1, "b": ["x", "y"]}


def test_yaml_parse_error_names_file_and_line(tmp_path):
    path = tmp_path / "broken.yaml"
    path.write_text("a: 1\nb: [x, y\nc: 3\n")
    with pytest.raises(ValueError) as exc_info:
        get_yaml_from_file(str(path))
    message = str(exc_info.value)
    assert "broken.yaml is not valid YAML" in message
    assert "line" in message


def test_json_loads_valid_file(tmp_path):
    path = tmp_path / "ok.json"
    path.write_text('{"a": [1, 2]}')
    assert get_json_from_file(str(path)) == {"a": [1, 2]}


def test_json_parse_error_names_file_and_line(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text('{"a": [1, 2}')
    with pytest.raises(ValueError, match=r"broken\.json is not valid JSON: .*line 1"):
        get_json_from_file(str(path))


def test_missing_file_still_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        get_yaml_from_file(str(tmp_path / "missing.yaml"))
