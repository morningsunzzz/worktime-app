import sys
import types
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def client():
    # Stub asyncpg before any module that imports it
    sys.modules.setdefault("asyncpg", types.SimpleNamespace(Pool=object, Record=object))

    import backend.database as db

    # Mock lifespan so no real DB connection is attempted
    with patch.object(db, "init_db", new_callable=AsyncMock):
        with patch.object(db, "close_pool", new_callable=AsyncMock):
            from backend.main import app

            mock_pool = MagicMock()
            mock_conn = AsyncMock()

            # pool.acquire() must return a sync context manager with async __aenter__/__aexit__
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_ctx.__aexit__ = AsyncMock()
            mock_pool.acquire = MagicMock(return_value=mock_ctx)

            # pool.fetchrow/fetchval/fetch are awaited directly on the pool
            mock_pool.fetchrow = AsyncMock()
            mock_pool.fetchval = AsyncMock()
            mock_pool.fetch = AsyncMock()

            db.pool = mock_pool

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as c:
                c._mock_conn = mock_conn
                c._mock_pool = mock_pool
                yield c
