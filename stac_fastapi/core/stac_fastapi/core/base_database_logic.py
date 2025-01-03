"""Base database logic."""

import abc
from typing import Any, Dict, Iterable, List, Optional


class BaseDatabaseLogic(abc.ABC):
    """
    Abstract base class for database logic.

    This class defines the basic structure and operations for database interactions.
    Subclasses must provide implementations for these methods.
    """

    @abc.abstractmethod
    async def get_all_collections(
        self, token: Optional[str], limit: int
    ) -> Iterable[Dict[str, Any]]:
        """Retrieve a list of all collections from the database."""
        pass

    @abc.abstractmethod
    async def get_one_item(self, collection_id: str, item_id: str) -> Dict:
        """Retrieve a single item from the database."""
        pass

    @abc.abstractmethod
    async def create_item(self, item: Dict, refresh: bool = False) -> None:
        """Create an item in the database."""
        pass

    @abc.abstractmethod
    async def merge_patch_item(
        self,
        collection_id: str,
        item_id: str,
        item: Dict,
        base_url: str,
        refresh: bool = True,
    ) -> Dict:
        """Patch a item in the database follows RF7396."""
        pass

    @abc.abstractmethod
    async def json_patch_item(
        self,
        collection_id: str,
        item_id: str,
        operations: List,
        base_url: str,
        refresh: bool = True,
    ) -> Dict:
        """Patch a item in the database follows RF6902."""
        pass

    @abc.abstractmethod
    async def delete_item(
        self, item_id: str, collection_id: str, refresh: bool = False
    ) -> None:
        """Delete an item from the database."""
        pass

    @abc.abstractmethod
    async def create_collection(self, collection: Dict, refresh: bool = False) -> None:
        """Create a collection in the database."""
        pass

    @abc.abstractmethod
    async def merge_patch_collection(
        self,
        collection_id: str,
        collection: Dict,
        base_url: str,
        refresh: bool = True,
    ) -> Dict:
        """Patch a collection in the database follows RF7396."""
        pass

    @abc.abstractmethod
    async def json_patch_collection(
        self,
        collection_id: str,
        operations: List,
        base_url: str,
        refresh: bool = True,
    ) -> Dict:
        """Patch a collection in the database follows RF6902."""
        pass

    @abc.abstractmethod
    async def find_collection(self, collection_id: str) -> Dict:
        """Find a collection in the database."""
        pass

    @abc.abstractmethod
    async def delete_collection(
        self, collection_id: str, refresh: bool = False
    ) -> None:
        """Delete a collection from the database."""
        pass
