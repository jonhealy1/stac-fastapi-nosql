## Aggregation

Stac-fastapi-elasticsearch-opensearch supports the STAC API [Aggregation Extension](https://github.com/stac-api-extensions/aggregation). This enables aggregation of points and geometries, as well as frequency distribution aggregation of any other property including dates. Aggregations can be defined at the root Catalog level (`/aggregations`) and at the Collection level (`/<collection_id>/aggregations`). The [Filter Extension](https://github.com/stac-api-extensions/filter) is also fully supported, enabling aggregated returns of search queries. Any query made with `/search` may also be executed with `/aggregate`, provided that the relevant aggregation fields are available,

A field named `aggregations` should be added to the Collection object for the collection for which the aggregations are available, for example:

Available aggregations are:

- total_count (count of total items)
- collection_frequency (Item `collection` field)
- platform_frequency (Item.Properties.platform)
- cloud_cover_frequency (Item.Properties.eo:cloud_cover)
- datetime_frequency (Item.Properties.datetime, monthly interval)
- datetime_min (earliest Item.Properties.datetime)
- datetime_max (latest Item.Properties.datetime)
- sun_elevation_frequency (Item.Properties.view:sun_elevation)
- sun_azimuth_frequency (Item.Properties.view:sun_azimuth)
- off_nadir_frequency (Item.Properties.view:off_nadir)
- grid_code_frequency (Item.Properties.grid:code)
- centroid_geohash_grid_frequency ([geohash grid](https://opensearch.org/docs/latest/aggregations/bucket/geohash-grid/)  on Item.Properties.proj:centroid)
- centroid_geohex_grid_frequency ([geohex grid](https://opensearch.org/docs/latest/aggregations/bucket/geohex-grid/) on Item.Properties.proj:centroid)
- centroid_geotile_grid_frequency (geotile on Item.Properties.proj:centroid)
- geometry_geohash_grid_frequency ([geohash grid](https://opensearch.org/docs/latest/aggregations/bucket/geohash-grid/) on Item.geometry)
- geometry_geotile_grid_frequency ([geotile grid](https://opensearch.org/docs/latest/aggregations/bucket/geotile-grid/) on Item.geometry)

Support for additional fields and new aggregations can be added in the [OpenSearch database_logic.py](../../stac_fastapi/opensearch/stac_fastapi/opensearch/database_logic.py) and [ElasticSearch database_logic.py](../../stac_fastapi/elasticsearch/stac_fastapi/elasticsearch/database_logic.py) files.

```json
"aggregations": [
    {
      "name": "total_count",
      "data_type": "integer"
    },
    {
      "name": "datetime_max",
      "data_type": "datetime"
    },
    {
      "name": "datetime_min",
      "data_type": "datetime"
    },
    {
      "name": "datetime_frequency",
      "data_type": "frequency_distribution",
      "frequency_distribution_data_type": "datetime"
    },
    {
      "name": "sun_elevation_frequency",
      "data_type": "frequency_distribution",
      "frequency_distribution_data_type": "numeric"
    },
    {
      "name": "platform_frequency", 
      "data_type": "frequency_distribution",
      "frequency_distribution_data_type": "string"
    },
    {
      "name": "sun_azimuth_frequency",
      "data_type": "frequency_distribution",
      "frequency_distribution_data_type": "numeric"
    },
    {
      "name": "off_nadir_frequency",
      "data_type": "frequency_distribution",
      "frequency_distribution_data_type": "numeric"
    },
    {
      "name": "cloud_cover_frequency",
      "data_type": "frequency_distribution",
      "frequency_distribution_data_type": "numeric"
    },
    {
      "name": "grid_code_frequency",
      "data_type": "frequency_distribution",
      "frequency_distribution_data_type": "string"
    },
    {
      "name": "centroid_geohash_grid_frequency",
      "data_type": "frequency_distribution",
      "frequency_distribution_data_type": "string"
    },
    {
        "name": "centroid_geohex_grid_frequency",
        "data_type": "frequency_distribution",
        "frequency_distribution_data_type": "string"
    },
    {
        "name": "centroid_geotile_grid_frequency",
        "data_type": "frequency_distribution",
        "frequency_distribution_data_type": "string"
    },
    {
      "name": "geometry_geohash_grid_frequency",
      "data_type": "frequency_distribution",
      "frequency_distribution_data_type": "numeric"
    },
    {
      "name": "geometry_geotile_grid_frequency",
      "data_type": "frequency_distribution",
      "frequency_distribution_data_type": "string"
    }
]
  ```


