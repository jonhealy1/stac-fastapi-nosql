import json
import os
import uuid
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from random import randint
from urllib.parse import parse_qs, urlparse, urlsplit

import ciso8601
import pytest
from geojson_pydantic.geometries import Polygon
from stac_pydantic import api

from stac_fastapi.core.core import CoreClient
from stac_fastapi.core.datetime_utils import datetime_to_str, now_to_rfc3339_str
from stac_fastapi.types.core import LandingPageMixin

from ..conftest import create_item, refresh_indices

if os.getenv("BACKEND", "elasticsearch").lower() == "opensearch":
    from stac_fastapi.opensearch.database_logic import DatabaseLogic
else:
    from stac_fastapi.elasticsearch.database_logic import DatabaseLogic


def rfc3339_str_to_datetime(s: str) -> datetime:
    return ciso8601.parse_rfc3339(s)


database_logic = DatabaseLogic()


@pytest.mark.asyncio
async def test_create_and_delete_item(app_client, ctx, txn_client):
    """Test creation and deletion of a single item (transactions extension)"""

    test_item = ctx.item

    resp = await app_client.get(
        f"/collections/{test_item['collection']}/items/{test_item['id']}"
    )
    assert resp.status_code == 200

    resp = await app_client.delete(
        f"/collections/{test_item['collection']}/items/{test_item['id']}"
    )
    assert resp.status_code == 204

    await refresh_indices(txn_client)

    resp = await app_client.get(
        f"/collections/{test_item['collection']}/items/{test_item['id']}"
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_item_conflict(app_client, ctx, load_test_data):
    """Test creation of an item which already exists (transactions extension)"""
    test_item = load_test_data("test_item.json")
    test_collection = load_test_data("test_collection.json")

    resp = await app_client.post(
        f"/collections/{test_collection['id']}", json=test_collection
    )

    resp = await app_client.post(
        f"/collections/{test_item['collection']}/items", json=test_item
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_delete_missing_item(app_client, load_test_data):
    """Test deletion of an item which does not exist (transactions extension)"""
    test_item = load_test_data("test_item.json")
    resp = await app_client.delete(
        f"/collections/{test_item['collection']}/items/hijosh"
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_item_missing_collection(app_client, ctx, load_test_data):
    """Test creation of an item without a parent collection (transactions extension)"""
    item = load_test_data("test_item.json")
    item["collection"] = "stac_is_cool"
    resp = await app_client.post(f"/collections/{item['collection']}/items", json=item)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_uppercase_collection_with_item(
    app_client, ctx, txn_client, load_test_data
):
    """Test creation of a collection and item with uppercase collection ID (transactions extension)"""
    item = load_test_data("test_item.json")
    collection = load_test_data("test_collection.json")
    collection_id = "UPPERCASE"
    item["collection"] = collection_id
    collection["id"] = collection_id
    resp = await app_client.post("/collections", json=collection)
    assert resp.status_code == 201
    await refresh_indices(txn_client)
    resp = await app_client.post(f"/collections/{collection_id}/items", json=item)
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_update_item_already_exists(app_client, ctx, load_test_data):
    """Test updating an item which already exists (transactions extension)"""
    item = load_test_data("test_item.json")
    assert item["properties"]["gsd"] != 16
    item["properties"]["gsd"] = 16
    await app_client.put(
        f"/collections/{item['collection']}/items/{item['id']}", json=item
    )
    resp = await app_client.get(f"/collections/{item['collection']}/items/{item['id']}")
    updated_item = resp.json()
    assert updated_item["properties"]["gsd"] == 16

    await app_client.delete(f"/collections/{item['collection']}/items/{item['id']}")


@pytest.mark.asyncio
async def test_update_new_item(app_client, load_test_data):
    """Test updating an item which does not exist (transactions extension)"""
    test_item = load_test_data("test_item.json")
    test_item["id"] = "a"

    resp = await app_client.put(
        f"/collections/{test_item['collection']}/items/{test_item['id']}",
        json=test_item,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_item_missing_collection(app_client, ctx, load_test_data):
    """Test updating an item without a parent collection (transactions extension)"""
    # Try to update collection of the item
    item = load_test_data("test_item.json")
    item["collection"] = "stac_is_cool"

    resp = await app_client.put(
        f"/collections/{item['collection']}/items/{item['id']}", json=item
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_item_geometry(app_client, ctx, load_test_data):
    item = load_test_data("test_item.json")
    item["id"] = "update_test_item_1"

    # Create the item
    resp = await app_client.post(f"/collections/{item['collection']}/items", json=item)
    assert resp.status_code == 201

    new_coordinates = [
        [
            [142.15052873427666, -33.82243006904891],
            [140.1000346138806, -34.257132625788756],
            [139.5776607193635, -32.514709769700254],
            [141.6262528041627, -32.08081674221862],
            [142.15052873427666, -33.82243006904891],
        ]
    ]

    # Update the geometry of the item
    item["geometry"]["coordinates"] = new_coordinates
    resp = await app_client.put(
        f"/collections/{item['collection']}/items/{item['id']}", json=item
    )
    assert resp.status_code == 200

    # Fetch the updated item
    resp = await app_client.get(f"/collections/{item['collection']}/items/{item['id']}")
    assert resp.status_code == 200
    assert resp.json()["geometry"]["coordinates"] == new_coordinates


@pytest.mark.asyncio
async def test_get_item(app_client, ctx):
    """Test read an item by id (core)"""
    get_item = await app_client.get(
        f"/collections/{ctx.item['collection']}/items/{ctx.item['id']}"
    )
    assert get_item.status_code == 200


@pytest.mark.asyncio
async def test_returns_valid_item(app_client, ctx):
    """Test validates fetched item with jsonschema"""
    test_item = ctx.item
    get_item = await app_client.get(
        f"/collections/{test_item['collection']}/items/{test_item['id']}"
    )
    assert get_item.status_code == 200
    item_dict = get_item.json()

    assert api.Item(**item_dict).model_dump(mode="json")


@pytest.mark.asyncio
async def test_get_item_collection(app_client, ctx, txn_client):
    """Test read an item collection (core)"""
    item_count = randint(1, 4)

    for idx in range(item_count):
        ctx.item["id"] = f'{ctx.item["id"]}{idx}'
        await create_item(txn_client, ctx.item)

    resp = await app_client.get(f"/collections/{ctx.item['collection']}/items")
    assert resp.status_code == 200

    item_collection = resp.json()
    if matched := item_collection.get("numMatched"):
        assert matched == item_count + 1


@pytest.mark.asyncio
async def test_item_collection_filter_bbox(app_client, ctx):
    item = ctx.item
    collection = item["collection"]

    bbox = "100,-50,170,-20"
    resp = await app_client.get(
        f"/collections/{collection}/items", params={"bbox": bbox}
    )
    assert resp.status_code == 200
    resp_json = resp.json()
    assert len(resp_json["features"]) == 1

    bbox = "1,2,3,4"
    resp = await app_client.get(
        f"/collections/{collection}/items", params={"bbox": bbox}
    )
    assert resp.status_code == 200
    resp_json = resp.json()
    assert len(resp_json["features"]) == 0


@pytest.mark.asyncio
async def test_item_collection_filter_datetime(app_client, ctx):
    item = ctx.item
    collection = item["collection"]

    datetime_range = "2020-01-01T00:00:00.00Z/.."
    resp = await app_client.get(
        f"/collections/{collection}/items", params={"datetime": datetime_range}
    )
    assert resp.status_code == 200
    resp_json = resp.json()
    assert len(resp_json["features"]) == 1

    datetime_range = "2018-01-01T00:00:00.00Z/2019-01-01T00:00:00.00Z"
    resp = await app_client.get(
        f"/collections/{collection}/items", params={"datetime": datetime_range}
    )
    assert resp.status_code == 200
    resp_json = resp.json()
    assert len(resp_json["features"]) == 0


@pytest.mark.asyncio
@pytest.mark.skip(reason="Pagination extension not implemented")
async def test_pagination(app_client, load_test_data):
    """Test item collection pagination (paging extension)"""
    item_count = 10
    test_item = load_test_data("test_item.json")

    for idx in range(item_count):
        _test_item = deepcopy(test_item)
        _test_item["id"] = test_item["id"] + str(idx)
        resp = await app_client.post(
            f"/collections/{test_item['collection']}/items", json=_test_item
        )
        assert resp.status_code == 200

    resp = await app_client.get(
        f"/collections/{test_item['collection']}/items", params={"limit": 3}
    )
    assert resp.status_code == 200
    first_page = resp.json()
    assert first_page["numReturned"] == 3

    url_components = urlsplit(first_page["links"][0]["href"])
    resp = await app_client.get(f"{url_components.path}?{url_components.query}")
    assert resp.status_code == 200
    second_page = resp.json()
    assert second_page["numReturned"] == 3


@pytest.mark.skip(reason="created and updated fields not be added with stac fastapi 3?")
@pytest.mark.asyncio
async def test_item_timestamps(app_client, ctx, load_test_data):
    """Test created and updated timestamps (common metadata)"""
    # start_time = now_to_rfc3339_str()

    item = load_test_data("test_item.json")
    created_dt = item["properties"]["created"]

    # todo, check lower bound
    # assert start_time < created_dt < now_to_rfc3339_str()
    assert created_dt < now_to_rfc3339_str()

    # Confirm `updated` timestamp
    ctx.item["properties"]["proj:epsg"] = 4326
    resp = await app_client.put(
        f"/collections/{ctx.item['collection']}/items/{ctx.item['id']}",
        json=dict(ctx.item),
    )
    assert resp.status_code == 200
    updated_item = resp.json()

    # Created shouldn't change on update
    assert ctx.item["properties"]["created"] == updated_item["properties"]["created"]
    assert updated_item["properties"]["updated"] > created_dt

    await app_client.delete(
        f"/collections/{ctx.item['collection']}/items/{ctx.item['id']}"
    )


@pytest.mark.asyncio
async def test_item_search_by_id_post(app_client, ctx, txn_client):
    """Test POST search by item id (core)"""
    ids = ["test1", "test2", "test3"]
    for _id in ids:
        ctx.item["id"] = _id
        await create_item(txn_client, ctx.item)

    params = {"collections": [ctx.item["collection"]], "ids": ids}
    resp = await app_client.post("/search", json=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert len(resp_json["features"]) == len(ids)
    assert set([feat["id"] for feat in resp_json["features"]]) == set(ids)


@pytest.mark.asyncio
async def test_item_search_spatial_query_post(app_client, ctx):
    """Test POST search with spatial query (core)"""
    test_item = ctx.item

    params = {
        "collections": [test_item["collection"]],
        "intersects": test_item["geometry"],
    }
    resp = await app_client.post("/search", json=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert resp_json["features"][0]["id"] == test_item["id"]


@pytest.mark.asyncio
async def test_item_search_temporal_query_post(app_client, ctx, load_test_data):
    """Test POST search with single-tailed spatio-temporal query (core)"""

    test_item = load_test_data("test_item.json")

    item_date = rfc3339_str_to_datetime(test_item["properties"]["datetime"])
    item_date = item_date + timedelta(seconds=1)

    params = {
        "collections": [test_item["collection"]],
        "intersects": test_item["geometry"],
        "datetime": f"../{datetime_to_str(item_date)}",
    }
    resp = await app_client.post("/search", json=params)
    resp_json = resp.json()
    assert resp_json["features"][0]["id"] == test_item["id"]


@pytest.mark.asyncio
async def test_item_search_temporal_window_post(app_client, ctx, load_test_data):
    """Test POST search with two-tailed spatio-temporal query (core)"""
    test_item = load_test_data("test_item.json")

    item_date = rfc3339_str_to_datetime(test_item["properties"]["datetime"])
    item_date_before = item_date - timedelta(seconds=1)
    item_date_after = item_date + timedelta(seconds=1)

    params = {
        "collections": [test_item["collection"]],
        "intersects": test_item["geometry"],
        "datetime": f"{datetime_to_str(item_date_before)}/{datetime_to_str(item_date_after)}",
    }
    resp = await app_client.post("/search", json=params)
    resp_json = resp.json()
    assert resp_json["features"][0]["id"] == test_item["id"]


@pytest.mark.asyncio
async def test_item_search_temporal_intersecting_window_post(app_client, ctx):
    """Test POST search with two-tailed spatio-temporal query (core)"""
    test_item = ctx.item

    item_date = rfc3339_str_to_datetime(test_item["properties"]["datetime"])
    item_date_before = item_date - timedelta(days=10)
    item_date_after = item_date - timedelta(days=2)

    params = {
        "collections": [test_item["collection"]],
        "intersects": test_item["geometry"],
        "datetime": f"{datetime_to_str(item_date_before)}/{datetime_to_str(item_date_after)}",
    }
    resp = await app_client.post("/search", json=params)
    resp_json = resp.json()
    assert resp_json["features"][0]["id"] == test_item["id"]


@pytest.mark.asyncio
async def test_item_search_temporal_open_window(app_client, ctx):
    """Test POST search with open spatio-temporal query (core)"""
    test_item = ctx.item
    params = {
        "collections": [test_item["collection"]],
        "intersects": test_item["geometry"],
        "datetime": "../..",
    }
    resp = await app_client.post("/search", json=params)
    resp_json = resp.json()
    assert resp_json["features"][0]["id"] == test_item["id"]


@pytest.mark.asyncio
async def test_item_search_by_id_get(app_client, ctx, txn_client):
    """Test GET search by item id (core)"""
    ids = ["test1", "test2", "test3"]
    for _id in ids:
        ctx.item["id"] = _id
        await create_item(txn_client, ctx.item)

    params = {"collections": ctx.item["collection"], "ids": ",".join(ids)}
    resp = await app_client.get("/search", params=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert len(resp_json["features"]) == len(ids)
    assert set([feat["id"] for feat in resp_json["features"]]) == set(ids)


@pytest.mark.asyncio
async def test_item_search_bbox_get(app_client, ctx):
    """Test GET search with spatial query (core)"""
    params = {
        "collections": ctx.item["collection"],
        "bbox": ",".join([str(coord) for coord in ctx.item["bbox"]]),
    }
    resp = await app_client.get("/search", params=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert resp_json["features"][0]["id"] == ctx.item["id"]


@pytest.mark.asyncio
async def test_item_search_get_without_collections(app_client, ctx):
    """Test GET search without specifying collections"""

    params = {
        "bbox": ",".join([str(coord) for coord in ctx.item["bbox"]]),
    }
    resp = await app_client.get("/search", params=params)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_item_search_get_with_non_existent_collections(app_client, ctx):
    """Test GET search with non-existent collections"""

    params = {"collections": "non-existent-collection,or-this-one"}
    resp = await app_client.get("/search", params=params)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_item_search_temporal_window_get(app_client, ctx, load_test_data):
    """Test GET search with spatio-temporal query (core)"""
    test_item = load_test_data("test_item.json")
    item_date = rfc3339_str_to_datetime(test_item["properties"]["datetime"])
    item_date_before = item_date - timedelta(hours=1)
    item_date_after = item_date + timedelta(hours=1)

    params = {
        "collections": test_item["collection"],
        "bbox": ",".join([str(coord) for coord in test_item["bbox"]]),
        "datetime": f"{datetime_to_str(item_date_before)}/{datetime_to_str(item_date_after)}",
    }
    resp = await app_client.get("/search", params=params)
    resp_json = resp.json()
    assert resp_json["features"][0]["id"] == test_item["id"]


@pytest.mark.asyncio
async def test_item_search_temporal_window_timezone_get(
    app_client, ctx, load_test_data
):
    """Test GET search with spatio-temporal query ending with Zulu and pagination(core)"""
    tzinfo = timezone(timedelta(hours=1))
    test_item = load_test_data("test_item.json")
    item_date = rfc3339_str_to_datetime(test_item["properties"]["datetime"])
    item_date_before = item_date - timedelta(seconds=1)
    item_date_before = item_date_before.replace(tzinfo=tzinfo)
    item_date_after = item_date + timedelta(seconds=1)
    item_date_after = item_date_after.replace(tzinfo=tzinfo)

    params = {
        "collections": test_item["collection"],
        "bbox": ",".join([str(coord) for coord in test_item["bbox"]]),
        "datetime": f"{datetime_to_str(item_date_before)}/{datetime_to_str(item_date_after)}",
    }
    resp = await app_client.get("/search", params=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert resp_json["features"][0]["id"] == test_item["id"]


@pytest.mark.asyncio
async def test_item_search_post_without_collection(app_client, ctx):
    """Test POST search without specifying a collection"""
    test_item = ctx.item
    params = {
        "bbox": test_item["bbox"],
    }
    resp = await app_client.post("/search", json=params)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_item_search_properties_es(app_client, ctx):
    """Test POST search with JSONB query (query extension)"""

    test_item = ctx.item
    # EPSG is a JSONB key
    params = {"query": {"proj:epsg": {"gt": test_item["properties"]["proj:epsg"] + 1}}}
    resp = await app_client.post("/search", json=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert len(resp_json["features"]) == 0


@pytest.mark.asyncio
async def test_item_search_properties_field(app_client):
    """Test POST search indexed field with query (query extension)"""

    # Orientation is an indexed field
    params = {"query": {"orientation": {"eq": "south"}}}
    resp = await app_client.post("/search", json=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert len(resp_json["features"]) == 0


@pytest.mark.asyncio
async def test_item_search_free_text_extension(app_client, txn_client, ctx):
    """Test POST search indexed field with q parameter (free-text)"""
    first_item = ctx.item

    second_item = dict(first_item)
    second_item["id"] = "second-item"
    second_item["properties"]["ft_field1"] = "hello"

    await create_item(txn_client, second_item)

    params = {"q": ["hello"]}
    resp = await app_client.post("/search", json=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert len(resp_json["features"]) == 1


@pytest.mark.asyncio
async def test_item_search_free_text_extension_or_query(app_client, txn_client, ctx):
    """Test POST search indexed field with q parameter with multiple terms (free-text)"""
    first_item = ctx.item

    second_item = dict(first_item)
    second_item["id"] = "second-item"
    second_item["properties"]["ft_field1"] = "hello"
    second_item["properties"]["ft_field2"] = "world"

    await create_item(txn_client, second_item)

    third_item = dict(first_item)
    third_item["id"] = "third-item"
    third_item["properties"]["ft_field1"] = "world"
    await create_item(txn_client, third_item)

    params = {"q": ["hello", "world"]}
    resp = await app_client.post("/search", json=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert len(resp_json["features"]) == 2


@pytest.mark.asyncio
async def test_item_search_get_query_extension(app_client, ctx):
    """Test GET search with JSONB query (query extension)"""

    test_item = ctx.item

    params = {
        "collections": [test_item["collection"]],
        "query": json.dumps(
            {"proj:epsg": {"gt": test_item["properties"]["proj:epsg"] + 1}}
        ),
    }
    resp = await app_client.get("/search", params=params)
    assert resp.json()["numReturned"] == 0

    params["query"] = json.dumps(
        {"proj:epsg": {"eq": test_item["properties"]["proj:epsg"]}}
    )
    resp = await app_client.get("/search", params=params)
    resp_json = resp.json()
    assert resp_json["numReturned"] == 1
    assert (
        resp_json["features"][0]["properties"]["proj:epsg"]
        == test_item["properties"]["proj:epsg"]
    )


@pytest.mark.asyncio
async def test_get_missing_item_collection(app_client):
    """Test reading a collection which does not exist"""
    resp = await app_client.get("/collections/invalid-collection/items")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_pagination_base_links(app_client, ctx):
    """Test that a search query always contains basic links"""
    page = await app_client.get(f"/collections/{ctx.item['collection']}/items")

    page_data = page.json()
    assert {"self", "root"}.issubset({link["rel"] for link in page_data["links"]})


@pytest.mark.asyncio
async def test_pagination_links_behavior(app_client, ctx, txn_client):
    """Test the links in pagination specifically look for last page behavior."""

    # Ingest 5 items
    for _ in range(5):
        ctx.item["id"] = str(uuid.uuid4())
        await create_item(txn_client, item=ctx.item)

    # Setting a limit to ensure the creation of multiple pages
    limit = 1
    first_page = await app_client.get(
        f"/collections/{ctx.item['collection']}/items?limit={limit}"
    )
    first_page_data = first_page.json()

    # Test for 'next' link in the first page
    next_link = next(
        (link for link in first_page_data["links"] if link["rel"] == "next"), None
    )
    assert next_link, "Missing 'next' link on the first page"

    # Follow to the last page using 'next' links
    current_page_data = first_page_data
    while "next" in {link["rel"] for link in current_page_data["links"]}:
        next_page_url = next(
            (
                link["href"]
                for link in current_page_data["links"]
                if link["rel"] == "next"
            ),
            None,
        )
        next_page = await app_client.get(next_page_url)
        current_page_data = next_page.json()

    # Verify the last page does not have a 'next' link
    assert "next" not in {
        link["rel"] for link in current_page_data["links"]
    }, "Unexpected 'next' link on the last page"


@pytest.mark.asyncio
async def test_pagination_item_collection(app_client, ctx, txn_client):
    """Test item collection pagination links (paging extension)"""
    ids = [ctx.item["id"]]

    # Ingest 5 items
    for _ in range(5):
        ctx.item["id"] = str(uuid.uuid4())
        await create_item(txn_client, item=ctx.item)
        ids.append(ctx.item["id"])

    # Paginate through all 6 items with a limit of 1 (expecting 6 requests)
    page = await app_client.get(
        f"/collections/{ctx.item['collection']}/items", params={"limit": 1}
    )

    item_ids = []
    for idx in range(1, 100):
        page_data = page.json()
        next_link = list(filter(lambda link: link["rel"] == "next", page_data["links"]))
        if not next_link:
            assert idx == 6
            break

        assert len(page_data["features"]) == 1
        item_ids.append(page_data["features"][0]["id"])

        href = next_link[0]["href"][len("http://test-server") :]
        page = await app_client.get(href)

    assert idx == len(ids)

    # Confirm we have paginated through all items
    assert not set(item_ids) - set(ids)


@pytest.mark.asyncio
async def test_pagination_post(app_client, ctx, txn_client):
    """Test POST pagination (paging extension)"""
    ids = [ctx.item["id"]]

    # Ingest 5 items
    for _ in range(5):
        ctx.item["id"] = str(uuid.uuid4())
    await create_item(txn_client, ctx.item)
    ids.append(ctx.item["id"])

    # Paginate through all 5 items with a limit of 1 (expecting 5 requests)
    request_body = {"ids": ids, "limit": 1}
    page = await app_client.post("/search", json=request_body)
    item_ids = []
    for idx in range(1, 100):
        page_data = page.json()
        next_link = list(filter(lambda link: link["rel"] == "next", page_data["links"]))
        if not next_link:
            break

        item_ids.append(page_data["features"][0]["id"])

        # Merge request bodies
        request_body.update(next_link[0]["body"])
        page = await app_client.post("/search", json=request_body)

    # Our limit is 1, so we expect len(ids) number of requests before we run out of pages
    assert idx == len(ids)

    # Confirm we have paginated through all items
    assert not set(item_ids) - set(ids)


@pytest.mark.asyncio
async def test_pagination_token_idempotent(app_client, ctx, txn_client):
    """Test that pagination tokens are idempotent (paging extension)"""
    ids = [ctx.item["id"]]

    # Ingest 5 items
    for _ in range(5):
        ctx.item["id"] = str(uuid.uuid4())
        await create_item(txn_client, ctx.item)
        ids.append(ctx.item["id"])

    page = await app_client.get("/search", params={"ids": ",".join(ids), "limit": 3})
    page_data = page.json()
    next_link = list(filter(lambda link: link["rel"] == "next", page_data["links"]))

    # Confirm token is idempotent
    resp1 = await app_client.get(
        "/search", params=parse_qs(urlparse(next_link[0]["href"]).query)
    )
    resp2 = await app_client.get(
        "/search", params=parse_qs(urlparse(next_link[0]["href"]).query)
    )
    resp1_data = resp1.json()
    resp2_data = resp2.json()

    # Two different requests with the same pagination token should return the same items
    assert [item["id"] for item in resp1_data["features"]] == [
        item["id"] for item in resp2_data["features"]
    ]


@pytest.mark.asyncio
async def test_field_extension_get_includes(app_client, ctx):
    """Test GET search with included fields (fields extension)"""
    test_item = ctx.item
    params = {
        "ids": [test_item["id"]],
        "fields": "+properties.proj:epsg,+properties.gsd",
    }
    resp = await app_client.get("/search", params=params)
    feat_properties = resp.json()["features"][0]["properties"]
    assert not set(feat_properties) - {"proj:epsg", "gsd", "datetime"}


@pytest.mark.asyncio
async def test_field_extension_get_excludes(app_client, ctx):
    """Test GET search with included fields (fields extension)"""
    test_item = ctx.item
    params = {
        "ids": [test_item["id"]],
        "fields": "-properties.proj:epsg,-properties.gsd",
    }
    resp = await app_client.get("/search", params=params)
    resp_json = resp.json()
    assert "proj:epsg" not in resp_json["features"][0]["properties"].keys()
    assert "gsd" not in resp_json["features"][0]["properties"].keys()


@pytest.mark.asyncio
async def test_field_extension_post(app_client, ctx):
    """Test POST search with included and excluded fields (fields extension)"""
    test_item = ctx.item
    body = {
        "ids": [test_item["id"]],
        "fields": {
            "exclude": ["assets.B1"],
            "include": [
                "properties.eo:cloud_cover",
                "properties.orientation",
                "assets",
            ],
        },
    }

    resp = await app_client.post("/search", json=body)
    resp_json = resp.json()
    assert "B1" not in resp_json["features"][0]["assets"].keys()
    assert not set(resp_json["features"][0]["properties"]) - {
        "orientation",
        "eo:cloud_cover",
        "datetime",
    }


@pytest.mark.asyncio
async def test_field_extension_exclude_and_include(app_client, ctx):
    """Test POST search including/excluding same field (fields extension)"""
    test_item = ctx.item
    body = {
        "ids": [test_item["id"]],
        "fields": {
            "exclude": ["properties.eo:cloud_cover"],
            "include": ["properties.eo:cloud_cover"],
        },
    }

    resp = await app_client.post("/search", json=body)
    resp_json = resp.json()
    assert "properties" not in resp_json["features"][0]


@pytest.mark.asyncio
async def test_field_extension_exclude_default_includes(app_client, ctx):
    """Test POST search excluding a forbidden field (fields extension)"""
    test_item = ctx.item
    body = {"ids": [test_item["id"]], "fields": {"exclude": ["gsd"]}}

    resp = await app_client.post("/search", json=body)
    resp_json = resp.json()
    assert "gsd" not in resp_json["features"][0]


@pytest.mark.asyncio
async def test_search_intersects_and_bbox(app_client):
    """Test POST search intersects and bbox are mutually exclusive (core)"""
    bbox = [-118, 34, -117, 35]
    geoj = Polygon.from_bounds(*bbox).model_dump(exclude_none=True)
    params = {"bbox": bbox, "intersects": geoj}
    resp = await app_client.post("/search", json=params)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_get_missing_item(app_client, load_test_data):
    """Test read item which does not exist (transactions extension)"""
    test_coll = load_test_data("test_collection.json")
    resp = await app_client.get(f"/collections/{test_coll['id']}/items/invalid-item")
    assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.skip(reason="invalid queries not implemented")
async def test_search_invalid_query_field(app_client):
    body = {"query": {"gsd": {"lt": 100}, "invalid-field": {"eq": 50}}}
    resp = await app_client.post("/search", json=body)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_search_bbox_errors(app_client):
    body = {"query": {"bbox": [0]}}
    resp = await app_client.post("/search", json=body)
    assert resp.status_code == 400

    body = {"query": {"bbox": [100.0, 0.0, 0.0, 105.0, 1.0, 1.0]}}
    resp = await app_client.post("/search", json=body)
    assert resp.status_code == 400

    params = {"bbox": "100.0,0.0,0.0,105.0"}
    resp = await app_client.get("/search", params=params)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_conformance_classes_configurable():
    """Test conformance class configurability"""
    landing = LandingPageMixin()
    landing_page = landing._landing_page(
        base_url="http://test/test",
        conformance_classes=["this is a test"],
        extension_schemas=[],
    )
    assert landing_page["conformsTo"][0] == "this is a test"

    # Update environment to avoid key error on client instantiation
    os.environ["READER_CONN_STRING"] = "testing"
    os.environ["WRITER_CONN_STRING"] = "testing"
    client = CoreClient(
        database=database_logic, base_conformance_classes=["this is a test"]
    )
    assert client.conformance_classes()[0] == "this is a test"


@pytest.mark.asyncio
async def test_search_datetime_validation_errors(app_client):
    bad_datetimes = [
        "37-01-01T12:00:27.87Z",
        "1985-13-12T23:20:50.52Z",
        "1985-12-32T23:20:50.52Z",
        "1985-12-01T25:20:50.52Z",
        "1985-12-01T00:60:50.52Z",
        "1985-12-01T00:06:61.52Z",
        "1990-12-31T23:59:61Z",
        "1986-04-12T23:20:50.52Z/1985-04-12T23:20:50.52Z",
    ]
    for dt in bad_datetimes:
        body = {"query": {"datetime": dt}}
        resp = await app_client.post("/search", json=body)
        assert resp.status_code == 400

        resp = await app_client.get("/search?datetime={}".format(dt))
        assert resp.status_code == 400


# this test should probably pass but doesn't - stac-pydantic
# https://github.com/stac-utils/stac-fastapi-elasticsearch-opensearch/issues/247

# @pytest.mark.asyncio
# async def test_item_custom_links(app_client, ctx, txn_client):
#     item = ctx.item
#     item_id = "test-item-custom-links"
#     item["id"] = item_id
#     item["links"].append(
#         {
#             "href": "https://maps.example.com/wms",
#             "rel": "wms",
#             "type": "image/png",
#             "title": "RGB composite visualized through a WMS",
#             "wms:layers": ["rgb"],
#             "wms:transparent": True,
#         }
#     )
#     await create_item(txn_client, item)

#     resp = await app_client.get("/search", params={"id": item_id})
#     assert resp.status_code == 200
#     resp_json = resp.json()
#     links = resp_json["features"][0]["links"]
#     for link in links:
#         if link["rel"] == "wms":
#             assert link["href"] == "https://maps.example.com/wms"
#             assert link["type"] == "image/png"
#             assert link["title"] == "RGB composite visualized through a WMS"
#             assert link["wms:layers"] == ["rgb"]
#             assert link["wms:transparent"]
#             return True
#     assert False, resp_json
