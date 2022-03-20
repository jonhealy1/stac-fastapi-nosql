import json
import os
from typing import Callable, Dict

import pytest
from starlette.testclient import TestClient

from stac_fastapi.api.app import StacApi
from stac_fastapi.api.models import create_request_model
from stac_fastapi.elasticsearch.config import ElasticsearchSettings
from stac_fastapi.elasticsearch.core import CoreCrudClient
from stac_fastapi.elasticsearch.extensions import QueryExtension
from stac_fastapi.elasticsearch.indexes import IndexesClient
from stac_fastapi.elasticsearch.transactions import (
    BulkTransactionsClient,
    TransactionsClient,
)
from stac_fastapi.extensions.core import (
    ContextExtension,
    FieldsExtension,
    SortExtension,
    TokenPaginationExtension,
    TransactionExtension,
)
from stac_fastapi.types.config import Settings
from stac_fastapi.types.errors import ConflictError
from stac_fastapi.types.search import BaseSearchGetRequest, BaseSearchPostRequest
import pytest_asyncio
import asyncio

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


class TestSettings(ElasticsearchSettings):
    class Config:
        env_file = ".env.test"


settings = TestSettings()
Settings.set(settings)


@pytest_asyncio.fixture(autouse=True)
async def cleanup(es_core: CoreCrudClient, es_transactions: TransactionsClient):
    yield
    collections = await es_core.all_collections(request=MockStarletteRequest)
    for coll in collections["collections"]:
        if coll["id"].split("-")[0] == "test":
            # Delete the items
            items = await es_core.item_collection(
                coll["id"], limit=100, request=MockStarletteRequest
            )
            for feat in items["features"]:
                try:
                    await es_transactions.delete_item(
                        feat["id"], feat["collection"], request=MockStarletteRequest
                    )
                except Exception:
                    pass

            # Delete the collection
            try:
                await es_transactions.delete_collection(
                    coll["id"], request=MockStarletteRequest
                )
            except Exception:
                pass

            yield


@pytest.fixture
def load_test_data() -> Callable[[str], Dict]:
    def load_file(filename: str) -> Dict:
        with open(os.path.join(DATA_DIR, filename)) as file:
            return json.load(file)

    return load_file


class MockStarletteRequest:
    base_url = "http://test-server"


# @pytest.fixture
# def db_session() -> Session:
#     return Session(
#         reader_conn_string=settings.reader_connection_string,
#         writer_conn_string=settings.writer_connection_string,
#     )


@pytest.fixture
def es_core():
    return CoreCrudClient(session=None)


@pytest.fixture
def es_transactions():
    return TransactionsClient(session=None)


@pytest.fixture
def es_bulk_transactions():
    return BulkTransactionsClient(session=None)


@pytest.fixture
def api_client():
    settings = ElasticsearchSettings()
    extensions = [
        TransactionExtension(
            client=TransactionsClient(session=None), settings=settings
        ),
        ContextExtension(),
        SortExtension(),
        FieldsExtension(),
        QueryExtension(),
        TokenPaginationExtension(),
    ]

    get_request_model = create_request_model(
        "SearchGetRequest",
        base_model=BaseSearchGetRequest,
        extensions=extensions,
        request_type="GET",
    )

    post_request_model = create_request_model(
        "SearchPostRequest",
        base_model=BaseSearchPostRequest,
        extensions=extensions,
        request_type="POST",
    )

    return StacApi(
        settings=settings,
        client=CoreCrudClient(
            session=None,
            extensions=extensions,
            post_request_model=post_request_model,
        ),
        extensions=extensions,
        search_get_request_model=get_request_model,
        search_post_request_model=post_request_model,
    )


@pytest_asyncio.fixture
async def app_client(api_client, load_test_data):
    IndexesClient().create_indexes()

    coll = load_test_data("test_collection.json")
    client = TransactionsClient(session=None)
    try:
        await client.create_collection(coll, request=MockStarletteRequest)
    except ConflictError:
        try:
            await client.delete_item("test-item", "test-collection")
        except Exception:
            pass

    with TestClient(api_client.app) as test_app:
        yield test_app


@pytest.fixture(scope="session")
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
