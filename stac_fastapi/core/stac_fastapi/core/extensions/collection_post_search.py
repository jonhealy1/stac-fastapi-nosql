"""Request model for the Aggregation extension."""

from typing import List, Optional, Union

import attr
from fastapi import APIRouter, FastAPI
from stac_pydantic.api.collections import Collections
from stac_pydantic.shared import MimeTypes

from stac_fastapi.api.models import GeoJSONResponse
from stac_fastapi.api.routes import create_async_endpoint
from stac_fastapi.extensions.core.collection_search import (
    CollectionSearchExtension,
    ConformanceClasses,
)
from stac_fastapi.extensions.core.collection_search.client import (
    AsyncBaseCollectionSearchClient,
    BaseCollectionSearchClient,
)
from stac_fastapi.extensions.core.collection_search.request import (
    BaseCollectionSearchGetRequest,
    BaseCollectionSearchPostRequest,
)
from stac_fastapi.types.config import ApiSettings


@attr.s
class CollectionSearchPostExtension(CollectionSearchExtension):
    """Collection-Search Extension.

    Extents the collection-search extension with an additional
    POST - /collections endpoint

    NOTE: the POST - /collections endpoint can be conflicting with the
    POST /collections endpoint registered for the Transaction extension.

    https://github.com/stac-api-extensions/collection-search

    Attributes:
        conformance_classes (list): Defines the list of conformance classes for
            the extension
    """

    client: Union[
        AsyncBaseCollectionSearchClient, BaseCollectionSearchClient
    ] = attr.ib()
    settings: ApiSettings = attr.ib()
    conformance_classes: List[str] = attr.ib(
        default=[ConformanceClasses.COLLECTIONSEARCH, ConformanceClasses.BASIS]
    )
    schema_href: Optional[str] = attr.ib(default=None)
    router: APIRouter = attr.ib(factory=APIRouter)

    GET: BaseCollectionSearchGetRequest = attr.ib(
        default=BaseCollectionSearchGetRequest
    )
    POST: BaseCollectionSearchPostRequest = attr.ib(
        default=BaseCollectionSearchPostRequest
    )

    def register(self, app: FastAPI) -> None:
        """Register the extension with a FastAPI application.

        Args:
            app: target FastAPI application.

        Returns:
            None
        """
        self.router.prefix = app.state.router_prefix

        self.router.add_api_route(
            name="Collections searcb",
            path="/collections-search",
            methods=["POST"],
            response_model=(
                Collections if self.settings.enable_response_models else None
            ),
            responses={
                200: {
                    "content": {
                        MimeTypes.json.value: {},
                    },
                    "model": Collections,
                },
            },
            response_class=GeoJSONResponse,
            endpoint=create_async_endpoint(self.client.post_all_collections, self.POST),
        )
        app.include_router(self.router)
