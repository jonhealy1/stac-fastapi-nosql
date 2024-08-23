"""API configuration."""

import os
import ssl
from typing import Any, Dict, Set

import certifi
import requests

# RIGHT https://elasticsearch-py.readthedocs.io/en/latest/async.html
# https://elasticsearch-serverless-python.readthedocs.io/en/stable/api.html#module-elasticsearch_serverless
# from elasticsearch import AsyncElasticsearch, Elasticsearch  # type: ignore
from elasticsearch_serverless import AsyncElasticsearch, Elasticsearch

from stac_fastapi.types.config import ApiSettings

# WRONG https://elasticsearch-serverless-python.readthedocs.io/en/latest/api.html#elasticsearch_serverless.client.AsyncSearchClient
# from elasticsearch_serverless.client import AsyncSearchClient


def check_serverless_elasticsearch():
    use_ssl = os.getenv("ES_USE_SSL", "true").lower() == "true"
    scheme = "https" if use_ssl else "http"

    # Configure the hosts parameter with the correct scheme
    host = f"{scheme}://{os.getenv('ES_HOST')}:{os.getenv('ES_PORT')}"

    headers = {"Authorization": f"ApiKey {os.getenv('ES_API_KEY')}"}
    response = requests.get(host, headers=headers)
    if response.ok:
        data = response.json()
        # Look for specific serverless indicators in the response
        if "version" in data and "serverless" == data["version"].get(
            "build_flavor", ""
        ):
            return True, "Serverless Elasticsearch found"
        else:
            return False, "No serverless indicator found"
    else:
        return False, "Error accessing Elasticsearch endpoint"


serverless, message = check_serverless_elasticsearch()


def _es_config() -> Dict[str, Any]:
    # Determine the scheme (http or https)
    use_ssl = os.getenv("ES_USE_SSL", "true").lower() == "true"
    scheme = "https" if use_ssl else "http"

    # Configure the hosts parameter with the correct scheme
    hosts = [f"{scheme}://{os.getenv('ES_HOST')}:{os.getenv('ES_PORT')}"]

    # Initialize the configuration dictionary
    accept = None
    if serverless:
        accept = "application/vnd.elasticsearch+json; compatible-with=8"
    else:
        accept = "application/vnd.elasticsearch+json; compatible-with=7"
    config = {
        "hosts": hosts,
        "headers": {"accept": accept},
    }

    # Handle API key
    if api_key := os.getenv("ES_API_KEY"):
        if isinstance(config["headers"], dict):
            headers = {**config["headers"], "x-api-key": api_key}

        else:
            config["headers"] = {"x-api-key": api_key}

        config["headers"] = headers

    # Explicitly exclude SSL settings when not using SSL
    if not use_ssl:
        return config

    # Include SSL settings if using https
    config["ssl_version"] = ssl.TLSVersion.TLSv1_3  # type: ignore
    config["verify_certs"] = os.getenv("ES_VERIFY_CERTS", "true").lower() != "false"  # type: ignore

    # Include CA Certificates if verifying certs
    if config["verify_certs"]:
        config["ca_certs"] = os.getenv("CURL_CA_BUNDLE", certifi.where())

    # Handle authentication
    if (u := os.getenv("ES_USER")) and (p := os.getenv("ES_PASS")):
        config["http_auth"] = (u, p)

    # Handle API key
    if api_key := os.getenv("ES_API_KEY"):
        if isinstance(config["headers"], dict):
            if serverless:
                headers = {**config["headers"], "Authorization": f"ApiKey {api_key}"}
            else:
                headers = {**config["headers"], "x-api-key": api_key}

        else:
            if serverless:
                config["headers"] = {"Authorization": f"ApiKey {api_key}"}
            else:
                config["headers"] = {"x-api-key": api_key}

        config["headers"] = headers

    return config


_forbidden_fields: Set[str] = {"type"}


class ElasticsearchSettings(ApiSettings):
    """API settings."""

    # Fields which are defined by STAC but not included in the database model
    forbidden_fields: Set[str] = _forbidden_fields
    indexed_fields: Set[str] = {"datetime"}

    @property
    def create_client(self):
        """Create es client."""
        return Elasticsearch(**_es_config())


class AsyncElasticsearchSettings(ApiSettings):
    """API settings."""

    # Fields which are defined by STAC but not included in the database model
    forbidden_fields: Set[str] = _forbidden_fields
    indexed_fields: Set[str] = {"datetime"}

    @property
    def create_client(self):
        """Create async elasticsearch client."""
        return AsyncElasticsearch(**_es_config())
