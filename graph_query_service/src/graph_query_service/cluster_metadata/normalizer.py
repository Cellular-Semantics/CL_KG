import json
from collections.abc import Mapping
from typing import Any


def property_map(entity: Any) -> dict[str, Any]:
    if entity is None:
        return {}
    if isinstance(entity, Mapping):
        properties = entity.get("properties")
        if isinstance(properties, Mapping):
            return dict(properties)
        return dict(entity)
    raw_properties = getattr(entity, "_properties", None)
    if isinstance(raw_properties, Mapping):
        return dict(raw_properties)
    if hasattr(entity, "items"):
        return dict(entity.items())
    raise TypeError(f"Unsupported entity type: {type(entity)!r}")


def first_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, list):
        if not value:
            return None
        if len(value) == 1:
            return value[0]
    return value


def string_value(props: Mapping[str, Any], key: str) -> str | None:
    value = first_value(props.get(key))
    if value is None:
        return None
    return str(value)


def label_value(props: Mapping[str, Any]) -> str | None:
    label = string_value(props, "label")
    if label:
        return label
    label_rdfs = first_value(props.get("label_rdfs"))
    if label_rdfs is None:
        return None
    return str(label_rdfs)


def annotation_value(props: Mapping[str, Any], key: str | None) -> Any:
    if not key:
        return None
    return first_value(props.get(key))


def synonym_columns(props: Mapping[str, Any]) -> list[str]:
    raw_value = props.get("author_synonym_columns")
    if raw_value is None:
        return []

    normalized = first_value(raw_value)
    if normalized is None:
        return []

    if isinstance(normalized, list):
        return [str(item) for item in normalized if str(item)]

    if isinstance(normalized, str):
        stripped = normalized.strip()
        if not stripped:
            return []
        if stripped.startswith("["):
            try:
                parsed = json.loads(stripped)
            except json.JSONDecodeError:
                return [stripped]
            if isinstance(parsed, list):
                return [str(item) for item in parsed if str(item)]
        return [stripped]

    return [str(normalized)]
