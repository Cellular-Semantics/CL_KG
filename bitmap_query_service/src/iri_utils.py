import re
import uuid


UUID_PATTERN = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)


def iri_storage_id(node_iri: str) -> str:
    match = UUID_PATTERN.search(node_iri)
    if match:
        return match.group(0).lower()
    return str(uuid.uuid5(uuid.NAMESPACE_URL, node_iri))


def bitmap_filename(node_iri: str, census_version: str) -> str:
    return f"{iri_storage_id(node_iri)}__{census_version}.bitmap"
