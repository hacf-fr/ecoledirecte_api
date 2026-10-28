import asyncio
from json import JSONDecodeError
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ecoledirecte_api.client import EDClient
from ecoledirecte_api.const import ED_MFA_REQUIRED, ED_NODATA, ED_OK
from ecoledirecte_api.exceptions import (
    EcoleDirecteException,
    GTKException,
    LoginException,
    MFARequiredException,
    ServiceUnavailableException,
)


def make_response(
    json_result=None,
    *,
    status=200,
    json_error=None,
    text="",
):
    response = Mock(status=status)
    if json_error is not None:
        response.json = AsyncMock(side_effect=json_error)
    else:
        response.json = AsyncMock(return_value=json_result)
    response.text = AsyncMock(return_value=text)
    return response


@pytest.mark.asyncio
async def test_login_sends_encoded_credentials_after_getting_gtk():
    client = EDClient("élève 1", "p@ss word", {})
    def create_session():
        client._session = Mock(headers={})

    client.__get_new_client__ = Mock(side_effect=create_session)
    client.__get_gtk__ = AsyncMock()
    client.__get_token__ = AsyncMock(return_value={"code": ED_OK})

    result = await client.login()

    assert result == {"code": ED_OK}
    client.__get_gtk__.assert_awaited_once_with()
    client.__get_token__.assert_awaited_once_with(
        'data={"identifiant":"%C3%A9l%C3%A8ve%201", '
        '"motdepasse":"p%40ss%20word", "isReLogin": false}'
    )


@pytest.mark.asyncio
async def test_get_gtk_stores_cookie_in_session_headers():
    client = EDClient("username", "password", {}, server_endpoint="https://api.test")
    response = Mock(cookies={"GTK": Mock(value="gtk-cookie")})
    client._session = Mock(headers={})
    client._session.get = AsyncMock(return_value=response)

    await client.__get_gtk__()

    client._session.get.assert_awaited_once_with(
        "https://api.test/login.awp",
        params={"v": client.api_version, "gtk": 1},
        data=None,
        timeout=120,
    )
    assert client._session.headers["x-gtk"] == "gtk-cookie"


@pytest.mark.asyncio
async def test_get_gtk_raises_when_server_does_not_set_cookie():
    client = EDClient("username", "password", {})
    client._session = Mock(headers={})
    client._session.get = AsyncMock(return_value=Mock(cookies={}))

    with pytest.raises(GTKException, match="Unable to get GTK"):
        await client.__get_gtk__()


@pytest.mark.asyncio
async def test_get_token_updates_session_authentication_state():
    client = EDClient("username", "password", {})
    response = make_response({"code": ED_OK})
    response.headers = {"x-token": "token-123", "2FA-Token": "two-factor"}
    client._session = Mock(headers={})
    client._session.post = AsyncMock(return_value=response)
    client._session.cookie_jar = object()

    with patch.object(EDClient, "check_response", new_callable=AsyncMock):
        result = await client.__get_token__("encoded-payload")

    assert result == {"code": ED_OK}
    assert client.token == "token-123"
    assert client.token_2fa == "two-factor"
    assert client._session.headers == {
        "x-token": "token-123",
        "2FA-Token": "two-factor",
    }
    assert client.cookie_jar is client._session.cookie_jar


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("result", "exception"),
    [
        ({"code": ED_MFA_REQUIRED}, MFARequiredException),
        ({"code": 505}, LoginException),
        ({"code": 520}, LoginException),
        ({"code": 525}, LoginException),
        ({"code": 517}, EcoleDirecteException),
        ({"code": 500}, EcoleDirecteException),
    ],
)
async def test_check_response_maps_api_error_codes(result, exception):
    response = make_response(result)

    with pytest.raises(exception) as error:
        await EDClient.check_response(
            response=response,
            path="/endpoint.awp",
            params={"v": "test"},
            payload="data={}",
        )

    assert "/endpoint.awp" in str(error.value)


@pytest.mark.asyncio
@pytest.mark.parametrize("code", [ED_OK, ED_NODATA])
async def test_check_response_accepts_success_and_no_data_codes(code):
    await EDClient.check_response(
        response=make_response({"code": code}),
        path="/endpoint.awp",
    )


@pytest.mark.asyncio
async def test_check_response_allows_mfa_code_when_bypassing_mfa():
    await EDClient.check_response(
        response=make_response({"code": ED_MFA_REQUIRED}),
        path="/login.awp",
        bypassMFA=True,
    )


@pytest.mark.asyncio
async def test_check_response_maps_server_http_error_to_service_unavailable():
    response = make_response(
        status=503,
        json_error=JSONDecodeError("not JSON", "", 0),
        text="maintenance",
    )

    with pytest.raises(ServiceUnavailableException) as error:
        await EDClient.check_response(response, path="/endpoint.awp")

    assert "status [503]" in str(error.value)
    assert "maintenance" in str(error.value)


@pytest.mark.asyncio
async def test_check_response_preserves_non_server_http_error_details():
    response = make_response(
        status=401,
        json_error=JSONDecodeError("not JSON", "", 0),
        text="unauthorized",
    )

    with pytest.raises(EcoleDirecteException) as error:
        await EDClient.check_response(
            response,
            path="/endpoint.awp",
            params={"v": "test"},
            payload="data={}",
        )

    assert "status [401]" in str(error.value)
    assert "unauthorized" in str(error.value)


@pytest.mark.asyncio
async def test_post_logs_in_when_needed_and_decodes_response():
    client = EDClient("username", "password", {}, server_endpoint="https://api.test")
    response = make_response({"code": ED_OK, "data": ["value"]})
    session = Mock()
    session.post = AsyncMock(return_value=response)

    with (
        patch.object(
            client,
            "login",
            new_callable=AsyncMock,
            side_effect=lambda: setattr(client, "_session", session),
        ) as mock_login,
    ):
        result = await client._EDClient__post(
            "/endpoint.awp",
            params={"verbe": "get"},
            payload="data={}",
        )

    mock_login.assert_awaited_once_with()
    session.post.assert_awaited_once_with(
        url="https://api.test/endpoint.awp",
        params={"verbe": "get"},
        data="data={}",
    )
    assert result == {"code": ED_OK, "data": ["value"]}


@pytest.mark.asyncio
async def test_homeworks_retries_login_error_then_returns_response():
    client = EDClient("username", "password", {})
    result = {"code": ED_OK, "data": []}

    with (
        patch.object(
            client,
            "_EDClient__post",
            new_callable=AsyncMock,
            side_effect=[LoginException(message="expired"), result],
        ) as mock_post,
        patch.object(client, "freshlogin", new_callable=AsyncMock) as mock_freshlogin,
        patch.object(asyncio, "sleep", new_callable=AsyncMock),
    ):
        assert await client.get_homeworks("1234") == result

    assert mock_post.await_count == 2
    mock_freshlogin.assert_awaited_once_with()


def test_encode_string_percent_encodes_credentials():
    client = EDClient("username", "password", {})

    assert client.encodeString("élève 1/@") == "%C3%A9l%C3%A8ve%201%2F%40"


def test_encode_body_serializes_nested_values():
    client = EDClient("username", "password", {})

    assert client.encodeBody(
        {"name": "Alice", "options": {"id": 12}, "active": False}
    ) == 'name="Alice",options={"id":"12"},active="False"'


def test_close_closes_and_clears_session():
    client = EDClient("username", "password", {})
    session = Mock()
    session.close = AsyncMock()
    client._session = session

    asyncio.run(client.close())

    session.close.assert_awaited_once_with()
    assert client._session is None


@pytest.mark.asyncio
async def test_close_without_session_is_safe():
    client = EDClient("username", "password", {})

    await client.close()

    assert client._session is None


@pytest.mark.asyncio
async def test_async_context_manager_closes_session():
    client = EDClient("username", "password", {})
    session = Mock()
    session.close = AsyncMock()
    client._session = session

    async with client as entered_client:
        assert entered_client is client

    session.close.assert_awaited_once_with()
    assert client._session is None
