"""Strict, offline nested-field mapping for CBBD season snapshots.

Field paths must be confirmed against the provider schema before use. This
module does not guess paths, synthesize missing metrics, fetch, or publish data.
"""
from collections.abc import Mapping


def extract(row, path):
    if not isinstance(path, str) or not path or any(not part for part in path.split(".")):
        raise ValueError("Mapping path must be a nonempty dotted string")
    current = row
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            raise ValueError(f"Provider field unavailable at mapped path: {path}")
        current = current[part]
    if current is None:
        raise ValueError(f"Provider field null at mapped path: {path}")
    return current


def map_records(records, field_paths, required_fields):
    if not isinstance(records, list) or not records:
        raise ValueError("Expected nonempty provider records")
    if not isinstance(field_paths, dict):
        raise ValueError("Explicit provider field mapping required")
    missing = set(required_fields) - set(field_paths)
    if missing:
        raise ValueError("Unmapped required dashboard fields: " + ", ".join(sorted(missing)))
    output = []
    for row in records:
        if not isinstance(row, Mapping):
            raise ValueError("Provider record must be an object")
        mapped = {field: extract(row, path) for field, path in field_paths.items()}
        output.append(mapped)
    return output
