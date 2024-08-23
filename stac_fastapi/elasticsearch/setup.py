"""stac_fastapi: elasticsearch module."""

from setuptools import find_namespace_packages, setup

with open("README.md") as f:
    desc = f.read()

install_requires = [
    "stac-fastapi.core==3.0.0",
    "uvicorn",
    "starlette",
]

install_requires_es = [
    "elasticsearch[async]==8.11.0",
    "elasticsearch-dsl==8.11.0",
]

install_requires_serverless_es = [
    "elasticsearch_serverless[async]",
    "elasticsearch-dsl",
    "requests",
]

extra_reqs = {
    "dev": [
        "pytest",
        "pytest-cov",
        "pytest-asyncio",
        "pre-commit",
        "requests",
        "ciso8601",
        "httpx",
        "debugpy",
    ],
    "docs": ["mkdocs", "mkdocs-material", "pdocs"],
    "server": ["uvicorn[standard]==0.19.0"],
    "es": install_requires_es,
    "serverless_es": install_requires_serverless_es,
}

setup(
    name="stac-fastapi.elasticsearch",
    description="An implementation of STAC API based on the FastAPI framework with both Elasticsearch and Opensearch.",
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
    packages=find_namespace_packages(exclude=["alembic", "tests", "scripts"]),
    zip_safe=False,
    install_requires=install_requires,
    tests_require=extra_reqs["dev"],
    extras_require=extra_reqs,
    entry_points={
        "console_scripts": [
            "stac-fastapi-elasticsearch=stac_fastapi.elasticsearch.app:run"
        ]
    },
)
