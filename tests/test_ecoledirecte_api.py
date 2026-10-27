import pytest
from unittest.mock import AsyncMock, patch

from ecoledirecte_api.client import EDClient, relogin
from ecoledirecte_api.const import APIVERSION


@pytest.mark.asyncio
async def test_relogin_callback_freshly_authenticates():
    client = EDClient("username", "password", {})
    client.token = "expired-token"
    client.cookie_jar = object()
    client.cn = "cn"
    client.cv = "cv"

    with patch.object(client, "login", new_callable=AsyncMock) as mock_login:
        await relogin({"args": (client,)})

    mock_login.assert_awaited_once_with()
    assert client.token is None
    assert client.cookie_jar is None
    assert client.cn == "cn"
    assert client.cv == "cv"


@pytest.mark.asyncio
async def test_get_espaces_travail_default():
    client = EDClient("username", "password", {})
    with patch.object(client, "_EDClient__post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = {"code": 200, "data": []}
        result = await client.get_all_espaces_travail()
        assert result == {"code": 200, "data": []}
        mock_post.assert_awaited_once_with(
            path="/1/3745/espacestravail.awp",
            params={
                "verbe": "get",
                "typeModule": "espaceTravail",
                "v": APIVERSION,
            },
            payload="data={}",
        )


@pytest.mark.asyncio
async def test_get_espaces_travail_custom():
    client = EDClient("username", "password", {})
    with patch.object(client, "_EDClient__post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = {"code": 200, "data": []}
        await client.get_all_espaces_travail(eleve_id="1234")
        mock_post.assert_awaited_once_with(
            path="/1/1234/espacestravail.awp",
            params={
                "verbe": "get",
                "typeModule": "espaceTravail",
                "v": APIVERSION,
            },
            payload="data={}",
        )


@pytest.mark.asyncio
async def test_get_espaces_travail_positional_swap():
    client = EDClient("username", "password", {})
    with patch.object(client, "_EDClient__post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = {"code": 200, "data": []}
        await client.get_all_espaces_travail(1, 3745)
        mock_post.assert_awaited_once_with(
            path="/1/3745/espacestravail.awp",
            params={
                "verbe": "get",
                "typeModule": "espaceTravail",
                "v": APIVERSION,
            },
            payload="data={}",
        )
