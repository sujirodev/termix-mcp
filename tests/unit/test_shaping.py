from __future__ import annotations

from typing import Any, cast

from termix_sdk import TermixObject

from termix_mcp.shaping import drop_fields, paginate, simplify, to_plain


def _obj(data: dict[str, Any]) -> TermixObject:
    return cast(TermixObject, TermixObject.construct_from(data))


def test_to_plain_converts_termix_object() -> None:
    obj = _obj({"id": "1", "name": "web1"})
    assert to_plain(obj) == {"id": "1", "name": "web1"}


def test_to_plain_passes_through_scalars() -> None:
    assert to_plain(5) == 5
    assert to_plain("x") == "x"
    assert to_plain(None) is None


def test_to_plain_converts_list_of_objects() -> None:
    objs = [_obj({"id": "1"}), _obj({"id": "2"})]
    assert to_plain(objs) == [{"id": "1"}, {"id": "2"}]


def test_drop_fields_removes_named_keys() -> None:
    assert drop_fields({"a": 1, "b": 2, "c": 3}, ["b"]) == {"a": 1, "c": 3}


def test_paginate_reports_truncation() -> None:
    result = paginate(list(range(10)), max_items=3)
    assert result == {"items": [0, 1, 2], "total": 10, "truncated": True}


def test_paginate_no_truncation_when_under_limit() -> None:
    result = paginate([1, 2], max_items=5)
    assert result == {"items": [1, 2], "total": 2, "truncated": False}


def test_simplify_dict_drops_fields() -> None:
    obj = _obj({"id": "1", "password": "secret", "name": "web1"})
    assert simplify(obj, drop=["password"]) == {"id": "1", "name": "web1"}


def test_simplify_list_paginates_and_drops() -> None:
    objs = [_obj({"id": str(i), "noisy": "x"}) for i in range(5)]
    result = simplify(objs, drop=["noisy"], max_items=2)
    assert result["items"] == [{"id": "0"}, {"id": "1"}]
    assert result["total"] == 5
    assert result["truncated"] is True


def test_simplify_scalar_passthrough() -> None:
    assert simplify("hello") == "hello"
