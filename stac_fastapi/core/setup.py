"""stac_fastapi: core elasticsearch/ opensearch module."""

from setuptools import find_namespace_packages, setup

with open("README.md") as f:
    desc = f.read()

install_requires = [
    "fastapi-slim",
    "attrs>=23.2.0",
    "pydantic[dotenv]",
    "stac_pydantic>=3",
    "stac-fastapi.types@git+https://github.com/stac-utils/stac-fastapi.git@refs/pull/744/head#subdirectory=stac_fastapi/types",
    "stac-fastapi.api@git+https://github.com/stac-utils/stac-fastapi.git@refs/pull/744/head#subdirectory=stac_fastapi/api",
    "stac-fastapi.extensions@git+https://github.com/stac-utils/stac-fastapi.git@refs/pull/744/head#subdirectory=stac_fastapi/extensions",
    "orjson",
    "overrides",
    "geojson-pydantic",
    "pygeofilter==0.2.1",
    "typing_extensions==4.8.0",
    "jsonschema",
    "slowapi==0.1.9",
]

setup(
    name="stac_fastapi.core",
    description="Core library for the Elasticsearch and Opensearch stac-fastapi backends.",
    long_description=desc,
    long_description_content_type="text/markdown",
    python_requires=">=3.8",
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
    ],
    url="https://github.com/stac-utils/stac-fastapi-elasticsearch-opensearch",
    license="MIT",
    packages=find_namespace_packages(),
    zip_safe=False,
    install_requires=install_requires,
)
