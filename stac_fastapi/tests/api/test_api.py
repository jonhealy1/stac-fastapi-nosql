import random
import uuid
from copy import deepcopy
from datetime import datetime, timedelta, timezone

import pytest

from ..conftest import create_collection, create_item

ROUTES = {
    "GET /_mgmt/ping",
    "GET /docs/oauth2-redirect",
    "HEAD /docs/oauth2-redirect",
    "GET /",
    "GET /conformance",
    "GET /api",
    "GET /api.html",
    "HEAD /api",
    "HEAD /api.html",
    "GET /queryables",
    "GET /collections",
    "GET /collections/{collection_id}",
    "GET /collections/{collection_id}/queryables",
    "GET /collections/{collection_id}/items",
    "GET /collections/{collection_id}/items/{item_id}",
    "GET /search",
    "POST /search",
    "DELETE /collections/{collection_id}",
    "DELETE /collections/{collection_id}/items/{item_id}",
    "POST /collections",
    "POST /collections/{collection_id}/items",
    "PUT /collections/{collection_id}",
    "PUT /collections/{collection_id}/items/{item_id}",
    "GET /aggregations",
    "GET /aggregate",
    "POST /aggregations",
    "POST /aggregate",
    "GET /collections/{collection_id}/aggregations",
    "GET /collections/{collection_id}/aggregate",
    "POST /collections/{collection_id}/aggregations",
    "POST /collections/{collection_id}/aggregate",
}


@pytest.mark.asyncio
async def test_post_search_content_type(app_client, ctx):
    params = {"limit": 1}
    resp = await app_client.post("/search", json=params)
    assert resp.headers["content-type"] == "application/geo+json"


@pytest.mark.asyncio
async def test_get_search_content_type(app_client, ctx):
    resp = await app_client.get("/search")
    assert resp.headers["content-type"] == "application/geo+json"


@pytest.mark.asyncio
async def test_api_headers(app_client):
    resp = await app_client.get("/api")
    assert (
        resp.headers["content-type"] == "application/vnd.oai.openapi+json;version=3.0"
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_router(app):
    api_routes = set([f"{list(route.methods)[0]} {route.path}" for route in app.routes])
    assert len(api_routes - ROUTES) == 0


@pytest.mark.asyncio
async def test_app_transaction_extension(app_client, ctx, load_test_data):
    item = load_test_data("test_item.json")
    item["id"] = str(uuid.uuid4())
    resp = await app_client.post(f"/collections/{item['collection']}/items", json=item)
    assert resp.status_code == 201

    await app_client.delete(f"/collections/{item['collection']}/items/{item['id']}")


@pytest.mark.asyncio
async def test_app_search_response(app_client, ctx):
    resp = await app_client.get("/search", params={"ids": ["test-item"]})
    assert resp.status_code == 200
    resp_json = resp.json()

    assert resp_json.get("type") == "FeatureCollection"
    # stac_version and stac_extensions were removed in v1.0.0-beta.3
    assert resp_json.get("stac_version") is None
    assert resp_json.get("stac_extensions") is None


@pytest.mark.asyncio
async def test_app_context_results(app_client, txn_client, ctx, load_test_data):
    test_item = load_test_data("test_item.json")
    test_item["id"] = "test-item-2"
    test_item["collection"] = "test-collection-2"
    test_collection = load_test_data("test_collection.json")
    test_collection["id"] = "test-collection-2"

    await create_collection(txn_client, test_collection)
    await create_item(txn_client, test_item)

    resp = await app_client.get(
        f"/collections/{test_collection['id']}/items/{test_item['id']}"
    )
    assert resp.status_code == 200
    resp_json = resp.json()
    assert resp_json["id"] == test_item["id"]
    assert resp_json["collection"] == test_item["collection"]

    resp = await app_client.get(f"/collections/{test_collection['id']}")
    assert resp.status_code == 200
    resp_json = resp.json()
    assert resp_json["id"] == test_collection["id"]

    resp = await app_client.post("/search", json={"collections": ["test-collection-2"]})
    assert resp.status_code == 200

    resp_json = resp.json()
    assert len(resp_json["features"]) == 1
    assert resp_json["numReturned"] == 1
    if matched := resp_json.get("numMatched"):
        assert matched == 1


@pytest.mark.asyncio
async def test_app_fields_extension(app_client, ctx, txn_client):
    resp = await app_client.get(
        "/search",
        params={"collections": ["test-collection"], "fields": "+properties.datetime"},
    )
    assert resp.status_code == 200
    resp_json = resp.json()
    assert list(resp_json["features"][0]["properties"]) == ["datetime"]


@pytest.mark.asyncio
async def test_app_fields_extension_query(app_client, ctx, txn_client):
    item = ctx.item
    resp = await app_client.post(
        "/search",
        json={
            "query": {"proj:epsg": {"gte": item["properties"]["proj:epsg"]}},
            "collections": ["test-collection"],
            "fields": {"include": ["properties.datetime", "properties.proj:epsg"]},
        },
    )
    assert resp.status_code == 200
    resp_json = resp.json()
    assert set(resp_json["features"][0]["properties"]) == set(["datetime", "proj:epsg"])


@pytest.mark.asyncio
async def test_app_fields_extension_no_properties_get(app_client, ctx, txn_client):
    resp = await app_client.get(
        "/search", params={"collections": ["test-collection"], "fields": "-properties"}
    )
    assert resp.status_code == 200
    resp_json = resp.json()
    assert "properties" not in resp_json["features"][0]


@pytest.mark.asyncio
async def test_app_fields_extension_no_properties_post(app_client, ctx, txn_client):
    resp = await app_client.post(
        "/search",
        json={
            "collections": ["test-collection"],
            "fields": {"exclude": ["properties"]},
        },
    )
    assert resp.status_code == 200
    resp_json = resp.json()
    assert "properties" not in resp_json["features"][0]


@pytest.mark.asyncio
async def test_app_fields_extension_no_null_fields(app_client, ctx, txn_client):
    resp = await app_client.get("/search", params={"collections": ["test-collection"]})
    assert resp.status_code == 200
    resp_json = resp.json()
    # check if no null fields: https://github.com/stac-utils/stac-fastapi-elasticsearch/issues/166
    for feature in resp_json["features"]:
        # assert "bbox" not in feature["geometry"]
        for link in feature["links"]:
            assert all(a not in link or link[a] is not None for a in ("title", "asset"))
        for asset in feature["assets"]:
            assert all(
                a not in asset or asset[a] is not None
                for a in ("start_datetime", "created")
            )


@pytest.mark.asyncio
async def test_app_fields_extension_return_all_properties(
    app_client, ctx, txn_client, load_test_data
):
    item = load_test_data("test_item.json")
    resp = await app_client.get(
        "/search", params={"collections": ["test-collection"], "fields": "properties"}
    )
    assert resp.status_code == 200
    resp_json = resp.json()
    feature = resp_json["features"][0]
    assert len(feature["properties"]) >= len(item["properties"])
    for expected_prop, expected_value in item["properties"].items():
        if expected_prop in ("datetime", "created", "updated"):
            assert feature["properties"][expected_prop][0:19] == expected_value[0:19]
        else:
            assert feature["properties"][expected_prop] == expected_value


@pytest.mark.asyncio
async def test_app_query_extension_gt(app_client, ctx):
    params = {"query": {"proj:epsg": {"gt": ctx.item["properties"]["proj:epsg"]}}}
    resp = await app_client.post("/search", json=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert len(resp_json["features"]) == 0


@pytest.mark.asyncio
async def test_app_query_extension_gte(app_client, ctx):
    params = {"query": {"proj:epsg": {"gte": ctx.item["properties"]["proj:epsg"]}}}
    resp = await app_client.post("/search", json=params)

    assert resp.status_code == 200
    assert len(resp.json()["features"]) == 1


@pytest.mark.asyncio
async def test_app_query_extension_limit_lt0(app_client):
    assert (
        await app_client.post("/search", json={"query": {}, "limit": -1})
    ).status_code == 400


@pytest.mark.skip(reason="removal of context extension")
@pytest.mark.asyncio
async def test_app_query_extension_limit_gt10000(app_client):
    resp = await app_client.post("/search", json={"limit": 10001})
    assert resp.status_code == 200
    assert resp.json()["context"]["limit"] == 10000


@pytest.mark.asyncio
async def test_app_query_extension_limit_10000(app_client):
    params = {"limit": 10000}
    resp = await app_client.post("/search", json=params)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_app_sort_extension_get_asc(app_client, txn_client, ctx):
    first_item = ctx.item

    second_item = dict(first_item)
    second_item["id"] = "another-item"
    another_item_date = datetime.strptime(
        first_item["properties"]["datetime"], "%Y-%m-%dT%H:%M:%SZ"
    ).replace(tzinfo=timezone.utc) - timedelta(days=1)
    second_item["properties"]["datetime"] = another_item_date.isoformat().replace(
        "+00:00", "Z"
    )

    await create_item(txn_client, second_item)

    resp = await app_client.get("/search?sortby=+properties.datetime")
    assert resp.status_code == 200
    resp_json = resp.json()
    assert resp_json["features"][1]["id"] == first_item["id"]
    assert resp_json["features"][0]["id"] == second_item["id"]


@pytest.mark.asyncio
async def test_app_sort_extension_get_desc(app_client, txn_client, ctx):
    first_item = ctx.item

    second_item = dict(first_item)
    second_item["id"] = "another-item"
    another_item_date = datetime.strptime(
        first_item["properties"]["datetime"], "%Y-%m-%dT%H:%M:%SZ"
    ).replace(tzinfo=timezone.utc) - timedelta(days=1)
    second_item["properties"]["datetime"] = another_item_date.isoformat().replace(
        "+00:00", "Z"
    )
    await create_item(txn_client, second_item)

    resp = await app_client.get("/search?sortby=-properties.datetime")
    assert resp.status_code == 200
    resp_json = resp.json()
    assert resp_json["features"][0]["id"] == first_item["id"]
    assert resp_json["features"][1]["id"] == second_item["id"]


@pytest.mark.asyncio
async def test_app_sort_extension_post_asc(app_client, txn_client, ctx):
    first_item = ctx.item

    second_item = dict(first_item)
    second_item["id"] = "another-item"
    another_item_date = datetime.strptime(
        first_item["properties"]["datetime"], "%Y-%m-%dT%H:%M:%SZ"
    ).replace(tzinfo=timezone.utc) - timedelta(days=1)
    second_item["properties"]["datetime"] = another_item_date.isoformat().replace(
        "+00:00", "Z"
    )
    await create_item(txn_client, second_item)

    params = {
        "collections": [first_item["collection"]],
        "sortby": [{"field": "properties.datetime", "direction": "asc"}],
    }
    resp = await app_client.post("/search", json=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert resp_json["features"][1]["id"] == first_item["id"]
    assert resp_json["features"][0]["id"] == second_item["id"]


@pytest.mark.asyncio
async def test_app_sort_extension_post_desc(app_client, txn_client, ctx):
    first_item = ctx.item

    second_item = dict(first_item)
    second_item["id"] = "another-item"
    another_item_date = datetime.strptime(
        first_item["properties"]["datetime"], "%Y-%m-%dT%H:%M:%SZ"
    ).replace(tzinfo=timezone.utc) - timedelta(days=1)
    second_item["properties"]["datetime"] = another_item_date.isoformat().replace(
        "+00:00", "Z"
    )
    await create_item(txn_client, second_item)

    params = {
        "collections": [first_item["collection"]],
        "sortby": [{"field": "properties.datetime", "direction": "desc"}],
    }
    resp = await app_client.post("/search", json=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert resp_json["features"][0]["id"] == first_item["id"]
    assert resp_json["features"][1]["id"] == second_item["id"]


@pytest.mark.asyncio
async def test_search_invalid_date(app_client, ctx):
    params = {
        "datetime": "2020-XX-01/2020-10-30",
        "collections": [ctx.item["collection"]],
    }

    resp = await app_client.post("/search", json=params)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_search_point_intersects_get(app_client, ctx):
    resp = await app_client.get(
        '/search?intersects={"type":"Point","coordinates":[150.04,-33.14]}'
    )

    assert resp.status_code == 200
    resp_json = resp.json()
    assert len(resp_json["features"]) == 1


@pytest.mark.asyncio
async def test_search_polygon_intersects_get(app_client, ctx):
    resp = await app_client.get(
        '/search?intersects={"type":"Polygon","coordinates":[[[149.04, -34.14],[149.04, -32.14],[151.04, -32.14],[151.04, -34.14],[149.04, -34.14]]]}'
    )

    assert resp.status_code == 200
    resp_json = resp.json()
    assert len(resp_json["features"]) == 1


@pytest.mark.asyncio
async def test_search_point_intersects_post(app_client, ctx):
    point = [150.04, -33.14]
    intersects = {"type": "Point", "coordinates": point}

    params = {
        "intersects": intersects,
        "collections": [ctx.item["collection"]],
    }
    resp = await app_client.post("/search", json=params)

    assert resp.status_code == 200
    resp_json = resp.json()
    assert len(resp_json["features"]) == 1


@pytest.mark.asyncio
async def test_search_point_does_not_intersect(app_client, ctx):
    point = [15.04, -3.14]
    intersects = {"type": "Point", "coordinates": point}

    params = {
        "intersects": intersects,
        "collections": [ctx.item["collection"]],
    }
    resp = await app_client.post("/search", json=params)

    assert resp.status_code == 200
    resp_json = resp.json()
    assert len(resp_json["features"]) == 0


@pytest.mark.asyncio
async def test_datetime_non_interval(app_client, ctx):
    dt_formats = [
        "2020-02-12T12:30:22+00:00",
        "2020-02-12T12:30:22.00Z",
        "2020-02-12T12:30:22Z",
        "2020-02-12T12:30:22.00+00:00",
    ]

    for dt in dt_formats:
        params = {
            "datetime": dt,
            "collections": [ctx.item["collection"]],
        }

        resp = await app_client.post("/search", json=params)
        assert resp.status_code == 200
        resp_json = resp.json()
        # datetime is returned in this format "2020-02-12T12:30:22Z"
        assert resp_json["features"][0]["properties"]["datetime"][0:19] == dt[0:19]


@pytest.mark.asyncio
async def test_bbox_3d(app_client, ctx):
    australia_bbox = [106.343365, -47.199523, 0.1, 168.218365, -19.437288, 0.1]
    params = {
        "bbox": australia_bbox,
        "collections": [ctx.item["collection"]],
    }
    resp = await app_client.post("/search", json=params)
    assert resp.status_code == 200
    resp_json = resp.json()
    assert len(resp_json["features"]) == 1


@pytest.mark.asyncio
async def test_search_line_string_intersects(app_client, ctx):
    line = [[150.04, -33.14], [150.22, -33.89]]
    intersects = {"type": "LineString", "coordinates": line}
    params = {
        "intersects": intersects,
        "collections": [ctx.item["collection"]],
    }

    resp = await app_client.post("/search", json=params)

    assert resp.status_code == 200

    resp_json = resp.json()
    assert len(resp_json["features"]) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "value, expected",
    [
        (32767, 1),  # Short Limit,
        (2147483647, 1),  # Int Limit
        (2147483647 + 5000, 1),  # Above int Limit
        (21474836470, 1),  # Above int Limit
        # This value still fails to return 1
        # Commenting out
        # (9223372036854775807, 1),
    ],
)
async def test_big_int_eo_search(
    app_client, txn_client, test_item, test_collection, value, expected
):

    random_str = "".join(random.choice("abcdef") for i in range(random.randint(1, 5)))
    collection_id = f"test-collection-eo-{random_str}"

    test_big_int_item = test_item
    del test_big_int_item["properties"]["eo:bands"]
    test_big_int_item["collection"] = collection_id
    test_big_int_collection = test_collection
    test_big_int_collection["id"] = collection_id

    # type number
    attr = "eo:full_width_half_max"

    stac_extensions = [
        "https://stac-extensions.github.io/eo/v2.0.0/schema.json",
    ]

    test_collection["stac_extensions"] = stac_extensions

    test_item["stac_extensions"] = stac_extensions

    await create_collection(txn_client, test_collection)

    for val in [
        value,
        value + random.randint(10, 1010),
        value - random.randint(10, 1010),
    ]:
        item = deepcopy(test_item)
        item["id"] = str(uuid.uuid4())
        item["properties"][attr] = val
        await create_item(txn_client, item)

    params = {
        "collections": [item["collection"]],
        "filter": {
            "args": [
                {
                    "args": [
                        {"property": f"properties.{attr}"},
                        value,
                    ],
                    "op": "=",
                }
            ],
            "op": "and",
        },
    }
    resp = await app_client.post("/search", json=params)
    resp_json = resp.json()
    results = set([x["properties"][attr] for x in resp_json["features"]])
    assert len(results) == expected
