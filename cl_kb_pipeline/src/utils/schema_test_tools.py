import glob
import json
import sys
from pathlib import Path

from jsonschema import Draft4Validator
from ruamel.yaml import YAML, YAMLError


def get_json_from_file(filename):
    """Load JSON from a file; parse errors keep their line/column details."""
    with open(filename) as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{filename} is not valid JSON: {exc}") from exc


def get_yaml_from_file(filename):
    """Load YAML from a file; parse errors keep their line/column details."""
    with open(filename) as stream:
        try:
            return YAML(typ="safe").load(stream)
        except YAMLError as exc:
            raise ValueError(f"{filename} is not valid YAML:\n{exc}") from exc


def get_validator(filename):
    """Load a JSON schema from file, check it is a valid Draft 4 schema
    (raises SchemaError if not) and return a Draft4Validator for it."""
    schema = get_json_from_file(filename)
    Draft4Validator.check_schema(schema)
    print(f"{filename} is a valid JSON schema")
    return Draft4Validator(schema=schema)


def validate(validator, instance, errors=None):
    """Validate an instance against a schema and report errors.

    Returns True if valid. Error messages are reported and, if an `errors` list
    is given, appended to it. Never exits the process; the caller decides.
    """
    if validator.is_valid(instance):
        print("Validation Passes")
        return True
    messages = recurse_through_errors(validator.iter_errors(instance))
    for message in messages:
        print(message, file=sys.stderr)
    if errors is not None:
        errors.extend(messages)
    print("Validation Fails")
    return False


def recurse_through_errors(es, level=0):
    """Format validation errors and their sub-errors (oneOf/anyOf context).

    Each line is '<location in instance>: <message>  [schema: <rule path>]',
    indented two spaces per nesting level; '$' is the document root.
    """
    messages = []
    for e in es:
        location = "/".join(str(part) for part in e.absolute_path) or "$"
        rule = "/".join(str(part) for part in e.absolute_schema_path)
        messages.append(f"{'  ' * level}{location}: {e.message}  [schema: {rule}]")
        if e.context:
            messages.extend(recurse_through_errors(e.context, level + 1))
    return messages


def validate_files_against_schema(path_to_schema_dir, schema_file, path_to_test_dir, load_yaml=True):
    """Validate every instance file in a directory against a single schema.

       * path_to_schema_dir: schema directory, relative to the cl_kb_pipeline folder
       * schema_file: schema file name inside path_to_schema_dir
       * path_to_test_dir: directory of instance files, relative to the cl_kb_pipeline folder
       * load_yaml: validate *.yaml files if True, otherwise *.json files
    Returns a list of error messages for all files; an empty list means all passed.
    """
    file_ext, loader = ("yaml", get_yaml_from_file) if load_yaml else ("json", get_json_from_file)
    # This file lives in cl_kb_pipeline/src/utils/; paths are relative to cl_kb_pipeline/.
    pipeline_root = Path(__file__).resolve().parents[2]
    schema_dir = pipeline_root / path_to_schema_dir
    test_dir = pipeline_root / path_to_test_dir
    for directory in (schema_dir, test_dir):
        if not directory.is_dir():
            raise FileNotFoundError(f"Directory not found: {directory}")

    sv = get_validator(str(schema_dir / schema_file))
    errors = []
    for instance_file in sorted(glob.glob(str(test_dir / f"*.{file_ext}"))):
        print(f"Testing: {instance_file}")
        try:
            instance = loader(instance_file)
        except ValueError as exc:  # unparsable file
            print(exc, file=sys.stderr)
            errors.append(str(exc))
            continue
        file_errors = []
        if not validate(sv, instance, file_errors):
            errors.extend(f"{instance_file}: {message}" for message in file_errors)
    return errors
