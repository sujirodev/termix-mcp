"""Masks secret-looking values in tool output.

termix-sdk 0.2.0 does not expose a public redaction API (`TermixObject.to_dict()` takes
no `redact` argument, and the `redact_value` helper lives in the private `_util` module).
This reimplements the same idea independently: match on key name, not on the SDK's
private helper, so it doesn't break silently if that private helper changes shape.
"""

from __future__ import annotations

import re
from typing import Any

MASK = "***"

_SECRET_KEY_PATTERN = re.compile(
    r"(password|passwd|secret|token|totp|api[_-]?key|private[_-]?key|"
    r"key[_-]?password|credential.*secret|auth.*header|client[_-]?secret)",
    re.IGNORECASE,
)

# Field names that are secret on their own but too short/generic for the regex above to
# match without also matching things like "keyType" - checked as a whole-name match,
# case-insensitive, not a substring search.
_EXACT_SECRET_KEYS = frozenset({"key", "password", "passwd", "secret", "token", "totp"})

# Field names that match the pattern/set above but are never secret values (booleans,
# flags, ids that merely *mention* a secret concept without carrying one).
_ALLOWLIST = frozenset({"hasPassword", "hasKey", "authType", "keyType", "tokenPrefix"})


def redact_value(key: str, value: Any) -> Any:
    if key in _ALLOWLIST:
        return value
    if not isinstance(value, str) or not value:
        return value
    if key.lower() in _EXACT_SECRET_KEYS or _SECRET_KEY_PATTERN.search(key):
        return MASK
    return value


def redact(obj: Any) -> Any:
    """Recursively mask secret-looking values in a dict/list produced by `.to_dict()`."""
    if isinstance(obj, dict):
        return {key: redact_value(key, redact(value)) for key, value in obj.items()}
    if isinstance(obj, list):
        return [redact(item) for item in obj]
    return obj
