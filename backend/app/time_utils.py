from datetime import datetime, timezone
from typing import Any


UTC = timezone.utc


def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def normalize_utc_datetime(value: Any) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)

        return value.astimezone(UTC)

    if isinstance(value, str):
        normalized_value = value.strip()

        if not normalized_value:
            return None

        if normalized_value.endswith("Z"):
            normalized_value = f"{normalized_value[:-1]}+00:00"

        try:
            parsed = datetime.fromisoformat(normalized_value)
        except ValueError:
            return None

        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)

        return parsed.astimezone(UTC)

    return None


def utc_isoformat(value: Any) -> str:
    normalized = normalize_utc_datetime(value)

    if normalized is None:
        return utc_now().isoformat()

    return normalized.replace(microsecond=0).isoformat()
