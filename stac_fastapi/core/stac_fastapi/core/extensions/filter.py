"""Filter extension logic for es conversion."""

# """
# Implements Filter Extension.

# Basic CQL2 (AND, OR, NOT), comparison operators (=, <>, <, <=, >, >=), and IS NULL.
# The comparison operators are allowed against string, numeric, boolean, date, and datetime types.

# Advanced comparison operators (http://www.opengis.net/spec/cql2/1.0/req/advanced-comparison-operators)
# defines the LIKE, IN, and BETWEEN operators.

# Basic Spatial Operators (http://www.opengis.net/spec/cql2/1.0/conf/basic-spatial-operators)
# defines the intersects operator (S_INTERSECTS).
# """

import re
from enum import Enum
from typing import Any, Dict


def cql2_like_to_es(string: str) -> str:
    """
    Convert CQL2 wildcard characters to Elasticsearch wildcard characters. Specifically, it converts '_' to '?' and '%' to '*', handling escape characters properly.

    Args:
        string (str): The string containing CQL2 wildcard characters.

    Returns:
        str: The converted string with Elasticsearch compatible wildcards.
    """
    # Translate '%' and '_' only if they are not preceded by a backslash '\'
    percent_pattern = r"(?<!\\)%"
    underscore_pattern = r"(?<!\\)_"
    # Remove the escape character before '%' or '_'
    escape_pattern = r"\\(?=[_%])"

    # Replace '%' with '*' for broad wildcard matching
    string = re.sub(percent_pattern, "*", string)
    # Replace '_' with '?' for single character wildcard matching
    string = re.sub(underscore_pattern, "?", string)
    # Remove the escape character used in the CQL2 format
    string = re.sub(escape_pattern, "", string)

    return string


class LogicalOp(str, Enum):
    """Enumeration for logical operators used in constructing Elasticsearch queries."""

    AND = "and"
    OR = "or"
    NOT = "not"


class ComparisonOp(str, Enum):
    """Enumeration for comparison operators used in filtering queries according to CQL2 standards."""

    EQ = "="
    NEQ = "<>"
    LT = "<"
    LTE = "<="
    GT = ">"
    GTE = ">="
    IS_NULL = "isNull"


class AdvancedComparisonOp(str, Enum):
    """Enumeration for advanced comparison operators like 'like', 'between', and 'in'."""

    LIKE = "like"
    BETWEEN = "between"
    IN = "in"


class SpatialIntersectsOp(str, Enum):
    """Enumeration for spatial intersection operator as per CQL2 standards."""

    S_INTERSECTS = "s_intersects"


queryables_mapping = {
    "id": "id",
    "collection": "collection",
    "geometry": "geometry",
    "datetime": "properties.datetime",
    "created": "properties.created",
    "updated": "properties.updated",
    "cloud_cover": "properties.eo:cloud_cover",
    "cloud_shadow_percentage": "properties.s2:cloud_shadow_percentage",
    "nodata_pixel_percentage": "properties.s2:nodata_pixel_percentage",
}


def to_es_field(field: str) -> str:
    """
    Map a given field to its corresponding Elasticsearch field according to a predefined mapping.

    Args:
        field (str): The field name from a user query or filter.

    Returns:
        str: The mapped field name suitable for Elasticsearch queries.
    """
    return queryables_mapping.get(field, field)


def to_es(query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform a simplified CQL2 query structure to an Elasticsearch compatible query DSL.

    Args:
        query (Dict[str, Any]): The query dictionary containing 'op' and 'args'.

    Returns:
        Dict[str, Any]: The corresponding Elasticsearch query in the form of a dictionary.
    """
    if query["op"] in [LogicalOp.AND, LogicalOp.OR, LogicalOp.NOT]:
        bool_type = {
            LogicalOp.AND: "must",
            LogicalOp.OR: "should",
            LogicalOp.NOT: "must_not",
        }[query["op"]]
        return {"bool": {bool_type: [to_es(sub_query) for sub_query in query["args"]]}}

    elif query["op"] in [
        ComparisonOp.EQ,
        ComparisonOp.NEQ,
        ComparisonOp.LT,
        ComparisonOp.LTE,
        ComparisonOp.GT,
        ComparisonOp.GTE,
    ]:
        field = to_es_field(query["args"][0]["property"])
        value = query["args"][1]
        if isinstance(value, dict) and "timestamp" in value:
            # Handle timestamp fields specifically
            value = value["timestamp"]
        if query["op"] == ComparisonOp.IS_NULL:
            return {"bool": {"must_not": {"exists": {"field": field}}}}
        else:
            if query["op"] == ComparisonOp.EQ:
                return {"term": {field: value}}
            elif query["op"] == ComparisonOp.NEQ:
                return {"bool": {"must_not": [{"term": {field: value}}]}}
            else:
                range_op = {
                    ComparisonOp.LT: "lt",
                    ComparisonOp.LTE: "lte",
                    ComparisonOp.GT: "gt",
                    ComparisonOp.GTE: "gte",
                }[query["op"]]
                return {"range": {field: {range_op: value}}}

    elif query["op"] == AdvancedComparisonOp.BETWEEN:
        field = to_es_field(query["args"][0]["property"])
        gte, lte = query["args"][1], query["args"][2]
        if isinstance(gte, dict) and "timestamp" in gte:
            gte = gte["timestamp"]
        if isinstance(lte, dict) and "timestamp" in lte:
            lte = lte["timestamp"]
        return {"range": {field: {"gte": gte, "lte": lte}}}

    elif query["op"] == AdvancedComparisonOp.IN:
        field = to_es_field(query["args"][0]["property"])
        values = query["args"][1]
        if not isinstance(values, list):
            raise ValueError(f"Arg {values} is not a list")
        return {"terms": {field: values}}

    elif query["op"] == AdvancedComparisonOp.LIKE:
        field = to_es_field(query["args"][0]["property"])
        pattern = cql2_like_to_es(query["args"][1])
        return {"wildcard": {field: {"value": pattern, "case_insensitive": True}}}

    elif query["op"] == SpatialIntersectsOp.S_INTERSECTS:
        field = to_es_field(query["args"][0]["property"])
        geometry = query["args"][1]
        return {"geo_shape": {field: {"shape": geometry, "relation": "intersects"}}}

    return {}
