from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ecoledirecte_api.client import EDClient


@pytest.mark.asyncio
async def test_api_methods_use_configured_version():
    client = EDClient("username", "password", {}, api_version="custom-version")

    with patch.object(
        client, "_EDClient__post", new_callable=AsyncMock
    ) as mock_post:
        mock_post.return_value = {"code": 200, "data": []}
        await client.get_messages("family", None, "2024-2025")
        await client.get_homeworks_by_date("1234", "2024-09-01")
        await client.get_homeworks("1234")
        await client.post_homework("1234", 1, True)
        await client.get_grades_evaluations("1234", "2024-2025")
        await client.get_vie_scolaire("1234")
        await client.get_lessons("1234", "2024-09-01", "2024-09-30")
        await client.get_all_wallet_balances()
        await client.get_sondages()
        await client.get_formulaires("2024-2025", "E", "1234")

    assert all(
        call.kwargs["params"]["v"] == "custom-version"
        for call in mock_post.await_args_list
    )
    sondages_call = mock_post.await_args_list[8]
    assert sondages_call.kwargs["path"] == "/rdt/sondages.awp?v=custom-version"

    with patch.object(client, "_EDClient__post", new_callable=MagicMock) as mock_post:
        await client.get_classe("1234")

    assert len(mock_post.call_args_list) == 2
    assert all(
        call.kwargs["params"]["v"] == "custom-version"
        for call in mock_post.call_args_list
    )
