"""Turns SDK objects into small, predictable dicts for the LLM: drop noisy fields, cap lists."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, cast

from termix_sdk import TermixObject


def to_plain(value: Any) -> Any:
    """Recursively convert TermixObject (and nested lists of it) to plain dict/list/scalar."""
    if isinstance(value, TermixObject):
        return value.to_dict()
    if isinstance(value, list):
        return [to_plain(item) for item in value]
    return value


def drop_fields(obj: Mapping[str, Any], drop: Iterable[str]) -> dict[str, Any]:
    drop_set = set(drop)
    return {key: val for key, val in obj.items() if key not in drop_set}


def paginate(items: list[Any], *, max_items: int) -> dict[str, Any]:
    """Cap a list to `max_items`, reporting the total and whether it was truncated."""
    total = len(items)
    truncated = total > max_items
    return {
        "items": items[:max_items],
        "total": total,
        "truncated": truncated,
    }


def simplify(
    value: Any,
    *,
    drop: Iterable[str] = (),
    max_items: int | None = None,
) -> Any:
    """`to_plain` + `drop_fields` on every dict in the result; `paginate` if it's a list."""
    plain = to_plain(value)

    if isinstance(plain, dict):
        return drop_fields(plain, drop)

    if isinstance(plain, list):
        shaped = [drop_fields(item, drop) if isinstance(item, dict) else item for item in plain]
        if max_items is not None:
            return paginate(shaped, max_items=max_items)
        return shaped

    return plain


def simplify_dict(
    value: Any,
    *,
    drop: Iterable[str] = (),
    max_items: int | None = None,
) -> dict[str, Any]:
    """`simplify`, asserted to a dict - for call sites where the result is always one:
    a single TermixObject, or a list shaped with `max_items` (which `paginate`s into a
    dict). Use `simplify` directly for a bare list/scalar result instead."""
    return cast(dict[str, Any], simplify(value, drop=drop, max_items=max_items))
