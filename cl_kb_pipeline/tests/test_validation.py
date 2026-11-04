import pytest
from jsonschema import Draft4Validator

import validate_neo2owl_config as ci_script
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
        ci_script, "validate_files_against_schema", lambda **kwargs: [f"{tmp_path}/config.yaml: bad value\n"]
    )
    assert ci_script.main() == 1
    assert (tmp_path / "validation.report").read_text() == "```\nconfig.yaml: bad value\n```\n"


NESTED_SCHEMA = {
    "type": "object",
    "properties": {
        "a": {"oneOf": [{"type": "integer"}, {"type": "boolean"}]},
        "b": {"type": "array", "items": {"type": "string"}},
    },
}


def test_error_report_nesting_and_locations():
    errors = []
    with pytest.warns(UserWarning):
        validate(Draft4Validator(NESTED_SCHEMA), {"a": "x", "b": ["ok", 2]}, errors)

    # 'a' failed oneOf: its two sub-errors are indented one level. 'b/1' is a
    # sibling of 'a' and stays at level 0 (the old code indented it further).
    assert errors == [
        "a: 'x' is not valid under any of the given schemas  [schema: properties/a/oneOf]",
        "  a: 'x' is not of type 'integer'  [schema: properties/a/oneOf/0/type]",
        "  a: 'x' is not of type 'boolean'  [schema: properties/a/oneOf/1/type]",
        "b/1: 2 is not of type 'string'  [schema: properties/b/items/type]",
    ]


def test_error_report_uses_dollar_for_document_root():
    errors = []
    with pytest.warns(UserWarning):
        validate(Draft4Validator(SCHEMA), "just a string", errors)
    assert errors == ["$: 'just a string' is not of type 'object'  [schema: type]"]
