"""Search model."""

from typing import List, Optional

from stac_fastapi.extensions.core.collection_search.collection_search import (
    BaseCollectionSearchPostRequest,
)
from stac_fastapi.types.search import BaseSearchPostRequest


# CollectionSearchPostRequest model.
class CollectionSearchPostRequest(
    BaseCollectionSearchPostRequest, BaseSearchPostRequest
):
    """The CollectionSearchPostRequest class."""

    query: Optional[str] = None
    token: Optional[str] = None
    fields: Optional[List[str]] = None
    sortby: Optional[str] = None
    intersects: Optional[str] = None
    filter: Optional[str] = None
    filter_lang: Optional[str] = None
    q: Optional[str] = None

    def __init__(self, **kwargs):
        """Run the Constructor."""
        super().__init__(**kwargs)
        self.query = kwargs.get("query", None)
        self.token = kwargs.get("token", None)
        self.sortby = kwargs.get("sortby", None)
        self.fields = kwargs.get("fields", None)
        self.filter = kwargs.get("filter", None)
        self.filter_lang = kwargs.get("filter-lang", None)
        self.q = kwargs.get("q", None)
