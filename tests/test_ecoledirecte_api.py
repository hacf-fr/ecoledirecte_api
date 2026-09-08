import pytest
from unittest.mock import AsyncMock, patch

from ecoledirecte_api.client import EDClient
from ecoledirecte_api.const import APIVERSION


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
