from __future__ import annotations

from unittest.mock import AsyncMock

from termix_mcp.tools.tools_credentials import register_credentials_tools

CREDENTIAL = {"id": "1", "name": "prod-key", "authType": "key", "key": "-----BEGIN...-----"}


async def test_list_credentials_masks_secrets(build_mcp, mock_client) -> None:
    mock_client.credentials.list = AsyncMock(return_value=[CREDENTIAL])
    mcp, _ = build_mcp(register_credentials_tools, TERMIX_MCP_TOOLSETS="credentials")

    result = await mcp.call_tool("termix_list_credentials", {})
    assert result.structured_content["items"][0]["key"] == "***"


async def test_get_credential_masks_secrets(build_mcp, mock_client) -> None:
    mock_client.credentials.retrieve = AsyncMock(return_value=CREDENTIAL)
    mcp, _ = build_mcp(register_credentials_tools, TERMIX_MCP_TOOLSETS="credentials")

    result = await mcp.call_tool("termix_get_credential", {"credential_id": "1"})
    assert result.structured_content["key"] == "***"
    assert result.structured_content["name"] == "prod-key"


async def test_reveal_credential_masked_by_default(build_mcp, mock_client) -> None:
    mock_client.credentials.retrieve = AsyncMock(return_value=CREDENTIAL)
    mcp, _ = build_mcp(register_credentials_tools, TERMIX_MCP_TOOLSETS="credentials")

    result = await mcp.call_tool("termix_reveal_credential", {"credential_id": "1"})
    assert result.structured_content["key"] == "***"


async def test_reveal_credential_unmasked_when_redact_disabled(build_mcp, mock_client) -> None:
    mock_client.credentials.retrieve = AsyncMock(return_value=CREDENTIAL)
    mcp, _ = build_mcp(
        register_credentials_tools,
        TERMIX_MCP_TOOLSETS="credentials",
        TERMIX_MCP_REDACT_SECRETS="false",
    )

    result = await mcp.call_tool("termix_reveal_credential", {"credential_id": "1"})
    assert result.structured_content["key"] == "-----BEGIN...-----"


async def test_create_credential_only_sends_provided_fields(build_mcp, mock_client) -> None:
    mock_client.credentials.create = AsyncMock(return_value=CREDENTIAL)
    mcp, _ = build_mcp(register_credentials_tools, TERMIX_MCP_TOOLSETS="credentials")

    await mcp.call_tool(
        "termix_create_credential", {"name": "prod-key", "auth_type": "key", "key": "abc"}
    )
    mock_client.credentials.create.assert_awaited_once_with(
        name="prod-key", authType="key", key="abc"
    )


async def test_update_credential_only_sends_provided_fields(build_mcp, mock_client) -> None:
    mock_client.credentials.update = AsyncMock(return_value=CREDENTIAL)
    mcp, _ = build_mcp(register_credentials_tools, TERMIX_MCP_TOOLSETS="credentials")

    await mcp.call_tool(
        "termix_update_credential", {"credential_id": "1", "description": "rotated"}
    )
    args, kwargs = mock_client.credentials.update.await_args
    assert args == ("1",)
    assert kwargs == {"description": "rotated"}


async def test_delete_credential_happy_path(build_mcp, mock_client) -> None:
    mock_client.credentials.delete = AsyncMock(
        return_value={"message": "Credential deleted successfully"}
    )
    mcp, _ = build_mcp(register_credentials_tools, TERMIX_MCP_TOOLSETS="credentials")

    result = await mcp.call_tool("termix_delete_credential", {"credential_id": "1"})
    assert result.structured_content["message"] == "Credential deleted successfully"


async def test_write_tools_absent_in_read_only_mode(build_mcp) -> None:
    mcp, _ = build_mcp(
        register_credentials_tools, TERMIX_MCP_TOOLSETS="credentials", TERMIX_MCP_READ_ONLY="true"
    )

    assert await mcp.get_tool("termix_list_credentials") is not None
    assert await mcp.get_tool("termix_reveal_credential") is not None  # read-only tool
    assert await mcp.get_tool("termix_create_credential") is None
    assert await mcp.get_tool("termix_delete_credential") is None
