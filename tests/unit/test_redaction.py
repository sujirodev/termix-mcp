from __future__ import annotations

from termix_mcp.redaction import MASK, redact


def test_password_field_masked() -> None:
    assert redact({"password": "hunter2"}) == {"password": MASK}


def test_nested_secret_masked() -> None:
    data = {"host": {"name": "web1", "authType": "password", "password": "hunter2"}}
    result = redact(data)
    assert result["host"]["password"] == MASK
    assert result["host"]["authType"] == "password"  # allowlisted, not a secret value
    assert result["host"]["name"] == "web1"


def test_list_of_dicts_masked() -> None:
    data = [{"apiKey": "tmx_secret"}, {"apiKey": "tmx_other"}]
    result = redact(data)
    assert result == [{"apiKey": MASK}, {"apiKey": MASK}]


def test_non_string_secret_value_untouched() -> None:
    # hasPassword is a bool flag, not a secret value; explicit allowlist entry.
    assert redact({"hasPassword": True}) == {"hasPassword": True}


def test_unrelated_field_untouched() -> None:
    assert redact({"name": "web1", "port": 22}) == {"name": "web1", "port": 22}


def test_key_material_masked() -> None:
    assert redact({"privateKey": "-----BEGIN..."}) == {"privateKey": MASK}
    assert redact({"totpSecret": "JBSWY3DP"}) == {"totpSecret": MASK}


def test_bare_key_field_masked() -> None:
    # A field literally named "key" (e.g. termix_sdk's CredentialsCreateParams.key, the
    # raw SSH private key content) - regression test for a gap where the regex only
    # matched compound names like "apiKey"/"privateKey", never the bare word "key".
    assert redact({"key": "-----BEGIN..."}) == {"key": MASK}


def test_key_type_not_masked() -> None:
    # keyType describes the key (e.g. "rsa"/"ed25519"), it isn't secret material itself.
    assert redact({"keyType": "ed25519"}) == {"keyType": "ed25519"}
