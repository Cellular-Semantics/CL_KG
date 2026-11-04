import pytest
from jsonschema import Draft4Validator

import test_neo2owl_config as ci_script
from utils.schema_test_tools import validate

SCHEMA = {"type": "object", "required": ["name"], "properties": {"name": {"type": "string"}}}


def test_validate_returns_true_for_valid_instance():
    assert validate(Draft4Validator(SCHEMA), {"name": "ok"}) is True


def test_validate_returns_false_and_collects_errors_without_exiting():
    errors = []
    with pytest.warns(UserWarning):
        result = validate(Draft4Validator(SCHEMA), {"name": 1}, errors)
    assert result is False
    assert len(errors) == 1 and "is not of type 'string'" in errors[0]


def test_ci_script_passes_on_repository_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert ci_script.main() == 0
    assert not (tmp_path / "validation.report").exists()


def test_ci_script_fails_and_writes_report(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        ci_script, "test_local", lambda **kwargs: [f"{tmp_path}/config.yaml: bad value\n"]
    )
    assert ci_script.main() == 1
    assert (tmp_path / "validation.report").read_text() == "```\nconfig.yaml: bad value\n```\n"
