"""FastAPI application."""

import os

from stac_fastapi.api.app import StacApi
from stac_fastapi.api.models import create_get_request_model, create_post_request_model
from stac_fastapi.core.core import (
    AsyncCollectionSearchClient,
    BulkTransactionsClient,
    CoreClient,
    EsAsyncBaseFiltersClient,
    TransactionsClient,
)
from stac_fastapi.core.extensions import CollectionSearchPostExtension, QueryExtension
from stac_fastapi.core.extensions.aggregation import (
    EsAggregationExtensionGetRequest,
    EsAggregationExtensionPostRequest,
    EsAsyncAggregationClient,
)
from stac_fastapi.core.extensions.fields import FieldsExtension
from stac_fastapi.core.models import CollectionSearchPostRequest
from stac_fastapi.core.route_dependencies import get_route_dependencies
from stac_fastapi.core.session import Session
from stac_fastapi.elasticsearch.config import ElasticsearchSettings
from stac_fastapi.elasticsearch.database_logic import (
    DatabaseLogic,
    create_collection_index,
    create_index_templates,
)
from stac_fastapi.extensions.core import (  # CollectionSearchExtension,; CollectionSearchPostExtension
    AggregationExtension,
    FilterExtension,
    FreeTextExtension,
    SortExtension,
    TokenPaginationExtension,
    TransactionExtension,
)
from stac_fastapi.extensions.third_party import BulkTransactionExtension

settings = ElasticsearchSettings()
session = Session.create_from_settings(settings)

filter_extension = FilterExtension(client=EsAsyncBaseFiltersClient())
filter_extension.conformance_classes.append(
    "http://www.opengis.net/spec/cql2/1.0/conf/advanced-comparison-operators"
)

database_logic = DatabaseLogic()

aggregation_extension = AggregationExtension(
    client=EsAsyncAggregationClient(
        database=database_logic, session=session, settings=settings
    )
)
aggregation_extension.POST = EsAggregationExtensionPostRequest
aggregation_extension.GET = EsAggregationExtensionGetRequest

collection_client = AsyncCollectionSearchClient(database=database_logic)
search_extensions = [
    CollectionSearchPostExtension(
        POST=CollectionSearchPostRequest, client=collection_client, settings=settings
    ),
    TransactionExtension(
        client=TransactionsClient(
            database=database_logic, session=session, settings=settings
        ),
        settings=settings,
    ),
    BulkTransactionExtension(
        client=BulkTransactionsClient(
            database=database_logic,
            session=session,
            settings=settings,
        )
    ),
    FieldsExtension(),
    QueryExtension(),
    SortExtension(),
    TokenPaginationExtension(),
    filter_extension,
    FreeTextExtension(),
]

extensions = [aggregation_extension] + search_extensions

database_logic.extensions = [type(ext).__name__ for ext in extensions]

post_request_model = create_post_request_model(search_extensions)

api = StacApi(
    title=os.getenv("STAC_FASTAPI_TITLE", "stac-fastapi-elasticsearch"),
    description=os.getenv("STAC_FASTAPI_DESCRIPTION", "stac-fastapi-elasticsearch"),
    api_version=os.getenv("STAC_FASTAPI_VERSION", "2.1"),
    settings=settings,
    extensions=extensions,
    client=CoreClient(
        database=database_logic, session=session, post_request_model=post_request_model
    ),
    search_get_request_model=create_get_request_model(search_extensions),
    search_post_request_model=post_request_model,
    route_dependencies=get_route_dependencies(),
)
app = api.app
app.root_path = os.getenv("STAC_FASTAPI_ROOT_PATH", "")


@app.on_event("startup")
async def _startup_event() -> None:
    await create_index_templates()
    await create_collection_index()


def run() -> None:
    """Run app from command line using uvicorn if available."""
    try:
        import uvicorn

        uvicorn.run(
            "stac_fastapi.elasticsearch.app:app",
            host=settings.app_host,
            port=settings.app_port,
            log_level="info",
            reload=settings.reload,
        )
    except ImportError:
        raise RuntimeError("Uvicorn must be installed in order to use command")


if __name__ == "__main__":
    run()


def create_handler(app):
    """Create a handler to use with AWS Lambda if mangum available."""
    try:
        from mangum import Mangum

        return Mangum(app)
    except ImportError:
        return None


handler = create_handler(app)
