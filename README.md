# stac-fastapi-elasticsearch-opensearch (sfeos)

<!-- markdownlint-disable MD033 MD041 -->

<p align="left">
  <img src="https://github.com/radiantearth/stac-site/raw/master/images/logo/stac-030-long.png" width=600>
  <p align="left"><b>Elasticsearch and Opensearch backends for the stac-fastapi project.</b></p>
  <p align="left"><b>Featuring stac-fastapi.core for simplifying the creation and maintenance of custom STAC api backends.</b></p>
</p>

  
  [![PyPI version](https://badge.fury.io/py/stac-fastapi.elasticsearch.svg)](https://badge.fury.io/py/stac-fastapi.elasticsearch)
  [![Join the chat at https://gitter.im/stac-fastapi-elasticsearch/community](https://badges.gitter.im/stac-fastapi-elasticsearch/community.svg)](https://gitter.im/stac-fastapi-elasticsearch/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)


---

**Online Documentation**: [https://stac-utils.github.io/stac-fastapi-elasticsearch-opensearch](https://stac-utils.github.io/stac-fastapi-elasticsearch-opensearch/)

**Source Code**: [https://github.com/stac-utils/stac-fastapi-elasticsearch-opensearch](https://github.com/stac-utils/stac-fastapi-elasticsearch-opensearch)


---

### Notes:
  
- Our Api core library can be used to create custom backends. See [stac-fastapi-mongo](https://github.com/Healy-Hyperspatial/stac-fastapi-mongo) for a working example.
- Reach out on our [Gitter](https://app.gitter.im/#/room/#stac-fastapi-elasticsearch_community:gitter.im) channel or feel free to add to our [Discussions](https://github.com/stac-utils/stac-fastapi-elasticsearch-opensearch/discussions) page here on github.
- There is [Postman](https://documenter.getpostman.com/view/12888943/2s8ZDSdRHA) documentation here for examples on how to run some of the API routes locally - after starting the elasticsearch backend via the docker-compose.yml file.
- The `/examples` folder shows an example of running stac-fastapi-elasticsearch from PyPI in docker without needing any code from the repository. There is also a Postman collection here that you can load into Postman for testing the API routes.

- For changes, see the [Changelog](CHANGELOG.md)
- We are always welcoming contributions. For the development notes: [Contributing](CONTRIBUTING.md)


### To install from PyPI:

```shell
pip install stac_fastapi.elasticsearch
```
or
```
pip install stac_fastapi.opensearch
```

### To install and run via pre-built Docker Images

We provide ready-to-use Docker images through GitHub Container Registry ([ElasticSearch](https://github.com/stac-utils/stac-fastapi-elasticsearch-opensearch/pkgs/container/stac-fastapi-es) and [OpenSearch](https://github.com/stac-utils/stac-fastapi-elasticsearch-opensearch/pkgs/container/stac-fastapi-os) backends). You can easily pull and run these images:

```shell
# For Elasticsearch backend
docker pull ghcr.io/stac-utils/stac-fastapi-es:latest

# For OpenSearch backend
docker pull ghcr.io/stac-utils/stac-fastapi-os:latest
```

## Run Elasticsearch API backend on localhost:8080

You need to ensure [**Docker Compose**](https://docs.docker.com/compose/install/) or [**Podman Compose**](https://podman-desktop.io/docs/compose) installed and running on your machine. In the follwoing command instead of `docker-compose` you can use `podman-compose` as well.

```shell
docker-compose up elasticsearch app-elasticsearch
```

By default, docker-compose uses Elasticsearch 8.x and OpenSearch 2.11.1.
If you wish to use a different version, put the following in a 
file named `.env` in the same directory you run docker-compose from:

```shell
ELASTICSEARCH_VERSION=7.17.1
OPENSEARCH_VERSION=2.11.0
```
The most recent Elasticsearch 7.x versions should also work. See the [opensearch-py docs](https://github.com/opensearch-project/opensearch-py/blob/main/COMPATIBILITY.md) for compatibility information.

#### **Configuration reference keys:**

You can customize additional settings in your `.env` file:
###### Key variables to configure:

| Variable                     | Description                                                                          | Default                  | Required                                                                                     |
|------------------------------|--------------------------------------------------------------------------------------|--------------------------|---------------------------------------------------------------------------------------------|
| `ES_HOST`                    | Hostname for external Elasticsearch/OpenSearch.                                      | `localhost`              | Optional                                                                                    |
| `ES_PORT`                    | Port for Elasticsearch/OpenSearch.                                                   | `9200` (ES) / `9202` (OS)| Optional                                                                                    |
| `ES_USE_SSL`                 | Use SSL for connecting to Elasticsearch/OpenSearch.                                  | `false`                  | Optional                                                                                    |
| `ES_VERIFY_CERTS`            | Verify SSL certificates when connecting.                                             | `false`                  | Optional                                                                                    |
| `STAC_FASTAPI_TITLE`         | Title of the API in the documentation.                                               | `stac-fastapi-elasticsearch` or `stac-fastapi-opensearch` | Optional                                                                                    |
| `STAC_FASTAPI_DESCRIPTION`   | Description of the API in the documentation.                                         | N/A                      | Optional                                                                                    |
| `STAC_FASTAPI_VERSION`       | API version.                                                                         | `2.1`                    | Optional                                                                                    |
| `APP_HOST`                   | Server bind address.                                                                 | `0.0.0.0`                | Optional                                                                                    |
| `APP_PORT`                   | Server port.                                                                         | `8080`                   | Optional                                                                                    |
| `ENVIRONMENT`                | Runtime environment.                                                                 | `local`                  | Optional                                                                                    |
| `WEB_CONCURRENCY`            | Number of worker processes.                                                          | `10`                     | Optional                                                                                    |
| `RELOAD`                     | Enable auto-reload for development.                                                  | `true`                   | Optional                                                                                    |
| `STAC_FASTAPI_RATE_LIMIT`    | API rate limit per client.                                                           | `200/minute`             | Optional                                                                                    |
| `BACKEND`                    | Tests-related variable                                                               | `elasticsearch` or `opensearch` based on the backend | Optional                                                                                    |
| `ELASTICSEARCH_VERSION`      | ElasticSearch version                                                                | `7.17.1`                 | Optional                                                                                    |
| `OPENSEARCH_VERSION`         | OpenSearch version                                                                   | `2.11.0`                 | Optional                                                                                    |

> [!NOTE]
> The variables `ES_HOST`, `ES_PORT`, `ES_USE_SSL`, and `ES_VERIFY_CERTS` apply to both Elasticsearch and OpenSearch backends, so there is no need to rename the key names to `OS_` even if you're using OpenSearch.

## Interacting with the API

To create a new Collection:

```shell
curl -X "POST" "http://localhost:8080/collections" \
     -H 'Content-Type: application/json; charset=utf-8' \
     -d $'{
  "id": "my_collection"
}'
```

Note: this "Collections Transaction" behavior is not part of the STAC API, but may be soon.

## Configure the API

By default the API title and description are set to `stac-fastapi-<backend>`. Change the API title and description from the default by setting the `STAC_FASTAPI_TITLE` and `STAC_FASTAPI_DESCRIPTION` environment variables, respectively.

By default the API will read from and write to the `collections` and `items_<collection name>` indices. To change the API collections index and the items index prefix, change the `STAC_COLLECTIONS_INDEX` and `STAC_ITEMS_INDEX_PREFIX` environment variables.

The application root path is left as the base url by default. If deploying to AWS Lambda with a Gateway API, you will need to define the app root path to be the same as the Gateway API stage name where you will deploy the API. The app root path can be defined with the `STAC_FASTAPI_ROOT_PATH` environment variable (`/v1`, for example)

## Collection pagination

The collections route handles optional `limit` and `token` parameters. The `links` field that is
returned from the `/collections` route contains a `next` link with the token that can be used to 
get the next page of results.

```shell
curl -X "GET" "http://localhost:8080/collections?limit=1&token=example_token"
```

## Ingesting Sample Data CLI Tool

```shell
Usage: data_loader.py [OPTIONS]

  Load STAC items into the database.

Options:
  --base-url TEXT       Base URL of the STAC API  [required]
  --collection-id TEXT  ID of the collection to which items are added
  --use-bulk            Use bulk insert method for items
  --data-dir PATH       Directory containing collection.json and feature
                        collection file
  --help                Show this message and exit.
```

```shell
python3 data_loader.py --base-url http://localhost:8080
```


## Elasticsearch Mappings

Mappings apply to search index, not source. The mappings are stored in index templates on application startup.
These templates will be used implicitly when creating new Collection and Item indices.
    

## Managing Elasticsearch Indices
### Snapshots

This section covers how to create a snapshot repository and then create and restore snapshots with this.

Create a snapshot repository. This puts the files in the `elasticsearch/snapshots` in this git repo clone, as
the elasticsearch.yml and docker-compose files create a mapping from that directory to 
`/usr/share/elasticsearch/snapshots` within the Elasticsearch container and grant permissions on using it.

```shell
curl -X "PUT" "http://localhost:9200/_snapshot/my_fs_backup" \
     -H 'Content-Type: application/json; charset=utf-8' \
     -d $'{
            "type": "fs",
            "settings": {
                "location": "/usr/share/elasticsearch/snapshots/my_fs_backup"
            }
}'
```

The next step is to create a snapshot of one or more indices into this snapshot repository.  This command creates
a snapshot named `my_snapshot_2` and waits for the action to be completed before returning. This can also be done
asynchronously, and queried for status. The `indices` parameter determines which indices are snapshotted, and
can include wildcards.

```shell
curl -X "PUT" "http://localhost:9200/_snapshot/my_fs_backup/my_snapshot_2?wait_for_completion=true" \
     -H 'Content-Type: application/json; charset=utf-8' \
     -d $'{
  "metadata": {
    "taken_because": "dump of all items",
    "taken_by": "pvarner"
  },
  "include_global_state": false,
  "ignore_unavailable": false,
  "indices": "items_my-collection"
}'
```

To see the status of this snapshot:

```shell
curl http://localhost:9200/_snapshot/my_fs_backup/my_snapshot_2
```

To see all the snapshots:

```shell
curl http://localhost:9200/_snapshot/my_fs_backup/_all
```

To restore a snapshot, run something similar to the following. This specific command will restore any indices that
match `items_*` and rename them so that the new index name will be suffixed with `-copy`.

```shell
curl -X "POST" "http://localhost:9200/_snapshot/my_fs_backup/my_snapshot_2/_restore?wait_for_completion=true" \
     -H 'Content-Type: application/json; charset=utf-8' \
     -d $'{
  "include_aliases": false,
  "include_global_state": false,
  "ignore_unavailable": true,
  "rename_replacement": "items_$1-copy",
  "indices": "items_*",
  "rename_pattern": "items_(.+)"
}'
```

Now the item documents have been restored in to the new index (e.g., `my-collection-copy`), but the value of the
`collection` field in those documents is still the original value of `my-collection`. To update these to match the
new collection name, run the following Elasticsearch Update By Query command, substituting the old collection name
into the term filter and the new collection name into the script parameter:

```shell
curl -X "POST" "http://localhost:9200/items_my-collection-copy/_update_by_query" \
     -H 'Content-Type: application/json; charset=utf-8' \
     -d $'{
    "query": {
        "match_all": {}
},
  "script": {
    "lang": "painless",
    "params": {
      "collection": "my-collection-copy"
    },
    "source": "ctx._source.collection = params.collection"
  }
}'
```

Then, create a new collection through the api with the new name for each of the restored indices:

```shell
curl -X "POST" "http://localhost:8080/collections" \
     -H 'Content-Type: application/json' \
     -d $'{
  "id": "my-collection-copy"
}'
```

Voila! You have a copy of the collection now that has a resource URI (`/collections/my-collection-copy`) and can be
correctly queried by collection name.

### Reindexing
This section covers how to reindex documents stored in Elasticsearch/OpenSearch. 
A reindex operation might be useful to apply changes to documents or to correct dynamically generated mappings.

The index templates will make sure that manually created indices will also have the correct mappings and settings.

In this example, we will make a copy of an existing Item index `items_my-collection-lower_my-collection-hex-000001` but change the Item identifier to be lowercase.

```shell
curl -X "POST" "http://localhost:9200/_reindex" \
  -H 'Content-Type: application/json' \
  -d $'{
    "source": {
      "index": "items_my-collection-lower_my-collection-hex-000001"
    }, 
    "dest": {
      "index": "items_my-collection-lower_my-collection-hex-000002"
    },
    "script": {
      "source": "ctx._source.id = ctx._source.id.toLowerCase()",
      "lang": "painless"
    }
  }'
```

If we are happy with the data in the newly created index, we can move the alias `items_my-collection` to the new index `items_my-collection-lower_my-collection-hex-000002`.
```shell
curl -X "POST" "http://localhost:9200/_aliases" \
  -h 'Content-Type: application/json' \
  -d $'{
    "actions": [
      {
        "remove": {
          "index": "*",
          "alias": "items_my-collection"
        }
      },
      {
        "add": {
          "index": "items_my-collection-lower_my-collection-hex-000002",
          "alias": "items_my-collection"
        }
      }
    ]
  }'
```

The modified Items with lowercase identifiers will now be visible to users accessing `my-collection` in the STAC API.


## Auth

Authentication is an optional feature that can be enabled through `Route Dependencies` examples can be found and a more detailed explanation in [examples/auth](examples/auth).

## Aggregation

Aggregation of points and geometries, as well as frequency distribution aggregation of any other property including dates is supported in stac-fatsapi-elasticsearch-opensearch. Aggregations can be defined at the root Catalog level (`/aggregations`) and at the Collection level (`/<collection_id>/aggregations`). Details for supported aggregations can be found at [./docs/src/aggregation.md](./docs/src/aggregation.md)

## Rate Limiting

Rate limiting is an optional security feature that controls API request frequency on a remote address basis. It's enabled by setting the `STAC_FASTAPI_RATE_LIMIT` environment variable, e.g., `500/minute`. This limits each client to 500 requests per minute, helping prevent abuse and maintain API stability. Implementation examples are available in the [examples/rate_limit](examples/rate_limit) directory.