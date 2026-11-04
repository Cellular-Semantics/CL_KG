"""Validate cl_kb_pipeline/config/dumps/*.yaml against the neo4j2owl config schema.

Run by .github/workflows/schema_validator.yaml. Exits 1 if any file fails and
writes the errors to validation.report (in the working directory) for the PR
comment.
"""
import os
import sys

from utils.schema_test_tools import validate_files_against_schema

REPORT_FILE = "validation.report"


def main() -> int:
    errors = validate_files_against_schema(
        path_to_schema_dir="config/dumps/",
        schema_file="neo4j2owl_config_schema.json",
        path_to_test_dir="config/dumps/",
    )
    if not errors:
        return 0
    cwd_prefix = os.getcwd() + os.sep  # show repo-relative paths in the PR comment
    lines = [error.replace(cwd_prefix, "").rstrip("\n") for error in errors]
    with open(REPORT_FILE, "w") as report:
        report.write("```\n" + "\n".join(lines) + "\n```\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
