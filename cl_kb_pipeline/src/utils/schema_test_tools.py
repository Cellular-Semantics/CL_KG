import json
import sys
from jsonschema import Draft4Validator, RefResolver, SchemaError
import os
import glob
from ruamel.yaml import YAML, YAMLError
import warnings
from pathlib import Path


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


def get_validator(filename, base_uri=''):
    """Load schema from JSON file;
    Check whether it's a valid schema;
    Return a Draft4Validator object.
    Optionally specify a base URI for relative path
    resolution of JSON pointers (This is especially useful
    for local resolution via base_uri of form file://{some_path}/)
    """

    schema = get_json_from_file(filename)
    try:
        # Check schema via class method call. Works, despite IDE complaining
        # However, it appears that this doesn't catch every schema issue.
        Draft4Validator.check_schema(schema)
        print("%s is a valid JSON schema" % filename)
    except SchemaError:
        raise
    if base_uri:
        resolver = RefResolver(base_uri=base_uri,
                               referrer=filename)
    else:
        resolver = None
    return Draft4Validator(schema=schema,
                           resolver=resolver)


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
        warnings.warn(message)
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
    """Tests all instances in a test_folder against a single schema.
    Assumes all schema files in single dir.
    Assumes all *.json files in the test_dir should validate against the schema.
       * path_to_schema_dir:  Absolute or relative path to schema dir
       * schema_file: schema file name
       * test_dir: path to test directory (absolute or local to schema dir)
    Returns a list of error messages for all files; an empty list means all passed.
    """
    file_ext = 'json'
    loader = get_json_from_file
    if load_yaml:
        file_ext = 'yaml'
        loader = get_yaml_from_file
    # Getting script directory, schema directory and test directory
    script_folder = Path(os.path.dirname(os.path.realpath(__file__))).parent
    schema_dir = Path(os.path.dirname(path_to_schema_dir))
    test_dir = Path(os.path.dirname(path_to_test_dir))
    # Checking whether schema directory and test directory are in the parent directory of script directory
    if not os.path.exists(os.path.join(script_folder.parent, schema_dir)):
        raise Exception("Please provide valid path_to_schema_dir")
    if not os.path.exists(os.path.join(script_folder.parent, test_dir)):
        raise Exception("Please provide valid path_to_test_dir")
    else:
        sv = get_validator(os.path.join(script_folder.parent, schema_dir, schema_file))
        test_dir_files = ''.join(['/*.', file_ext])
        test_files = glob.glob(pathname=os.path.join(script_folder.parent, test_dir) + test_dir_files)
        # print("Found test files: %s in %s" % (str(test_files), path_to_test_dir))
        errors = []
        for instance_file in test_files:
            print("Testing: %s" % instance_file)
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
