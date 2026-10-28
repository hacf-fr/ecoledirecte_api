import logging
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ecoledirecte_api.client import EDClient


@pytest.mark.asyncio
async def test_get_token_logs_code_without_request_or_response_data(caplog):
    client = EDClient("username", "password", {})
    response = Mock()
    response.headers = {"x-token": "session-token"}
    response.json = AsyncMock(
        return_value={
            "code": 200,
            "data": {"student": "private student name"},
        }
    )
    client._session = Mock()
    client._session.post = AsyncMock(return_value=response)
    client._session.headers = {}
    client._session.cookie_jar = object()

    with (
        patch.object(EDClient, "check_response", new_callable=AsyncMock),
        caplog.at_level(logging.DEBUG, logger="ecoledirecte_api.client"),
    ):
        await client.__get_token__("private login payload")

    assert "code=200" in caplog.text
    assert "private login payload" not in caplog.text
    assert "private student name" not in caplog.text


@pytest.mark.asyncio
async def test_get_qcm_connexion_logs_code_without_response_data(caplog):
    client = EDClient("username", "password", {})
    response = Mock()
    response.headers = {"x-token": "session-token"}
    response.json = AsyncMock(
        return_value={
            "code": 200,
            "data": {
                "question": "private security question",
                "propositions": ["private answer"],
            },
        }
    )
    client._session = Mock()
    client._session.post = AsyncMock(return_value=response)
    client._session.headers = {}

    with caplog.at_level(logging.DEBUG, logger="ecoledirecte_api.client"):
        await client.__get_qcm_connexion__()

    assert "code=200" in caplog.text
    assert "private security question" not in caplog.text
    assert "private answer" not in caplog.text
