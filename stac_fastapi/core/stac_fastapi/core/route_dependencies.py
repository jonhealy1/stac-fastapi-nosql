"""Route Dependencies Module."""

import importlib
import json
import logging
import os

from fastapi import Depends

_LOGGER = logging.getLogger("uvicorn.default")


def get_route_dependencies() -> list:
    """
    Route dependencies generator.

    Generate a set of route dependencies for authentication to the
    provided FastAPI application.
    """
    route_dependencies_env = os.environ.get("STAC_FASTAPI_ROUTE_DEPENDENCIES")
    route_dependencies = []

    if route_dependencies_env:
        _LOGGER.info("Authentication enabled.")

        if os.path.exists(route_dependencies_env):
            with open(route_dependencies_env) as route_dependencies_file:
                route_dependencies_conf = json.load(route_dependencies_file)

        else:
            try:
                route_dependencies_conf = json.loads(route_dependencies_env)
            except json.JSONDecodeError as exception:
                _LOGGER.error(
                    "Invalid JSON format for route dependencies. %s", exception
                )
                raise

        for route_dependency_conf in route_dependencies_conf:
            routes = route_dependency_conf["routes"]
            dependencies_conf = route_dependency_conf["dependencies"]

            dependencies = []
            for dependency_conf in dependencies_conf:

                module_name, function_name = dependency_conf["method"].rsplit(".", 1)

                module = importlib.import_module(module_name)

                function = getattr(module, function_name)

                dependency = function(
                    *dependency_conf.get("input_args", []),
                    **dependency_conf.get("input_kwargs", {})
                )

                dependencies.append(Depends(dependency))

            route_dependencies.append((routes, dependencies))

    else:
        _LOGGER.info("Authentication skipped.")

    return route_dependencies
