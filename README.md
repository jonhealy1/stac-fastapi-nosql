# stac-fastapi-elasticsearch

Elasticsearch backend for stac-fastapi. 

**WIP** This backend is not yet stable (notice no releases yet), so use the pgstac backend instead.

For changes, see the [Changelog](CHANGELOG.md).

## Development Environment Setup

Install [pre-commit](https://pre-commit.com/#install).

Prior to commit, run:

```shell
pre-commit run --all-files`
```

```shell
cd stac_fastapi/elasticsearch
pip install .[dev]
```

## Building

```shell
docker-compose build
```

## Running API on localhost:8083

```shell
docker-compose up
```

By default, docker-compose uses Elasticsearch 8.x. If you wish to use a different version, put the following in a 
file named `.env` in the same directory you run docker-compose from:

```shell
ELASTICSEARCH_VERSION=7.17.1
```

To create a new Collection:

```shell
curl -X "POST" "http://localhost:8083/collections" \
     -H 'Content-Type: application/json; charset=utf-8' \
     -d $'{
  "id": "my_collection"
}'
```

Note: this "Collections Transaction" behavior is not part of the STAC API, but may be soon.

## Testing

```shell
make test
```

## Ingest sample data

```shell
make ingest
```

## Elasticsearch Mappings

Mappings apply to search index, not source. 