"""Strict, lossless validation of API evidence and JSON payloads."""
import json

from backend.contracts import EvidenceRecord


def collect_evidence_ids(value) -> set[str]:
    """Collect every evidence_ids suffix, including nested provenance additions."""
    identifiers = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(key, str) and key.endswith('evidence_ids'):
                if not isinstance(child, list) or any(not isinstance(item, str) for item in child):
                    raise ValueError('Evidence references must be arrays of strings.')
                identifiers.update(child)
            else:
                identifiers.update(collect_evidence_ids(child))
    elif isinstance(value, list):
        for child in value:
            identifiers.update(collect_evidence_ids(child))
    return identifiers


def validate_json(value) -> None:
    """Reject non-finite numbers and values unavailable in strict JSON."""
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError, OverflowError, RecursionError):
        raise ValueError('Response must contain only strict JSON values.') from None


def validate_evidence_registry(records: list[dict], canonical: dict[str, dict]) -> dict[str, dict]:
    """Validate canonical core fields without discarding additional provenance."""
    if not isinstance(records, list):
        raise ValueError('Evidence registry must be an array.')
    registry = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError('Evidence record must be an object.')
        try:
            validated = EvidenceRecord.model_validate(record, strict=True).model_dump()
        except ValueError:
            raise ValueError('Evidence record has an invalid schema.') from None
        identifier = validated['id']
        if identifier in registry:
            raise ValueError('Evidence registry contains duplicate IDs.')
        expected = canonical.get(identifier)
        if expected is None or any(validated[key] != expected.get(key) for key in validated):
            raise ValueError('Evidence record does not match a canonical source.')
        registry[identifier] = record
    validate_json(records)
    return registry
