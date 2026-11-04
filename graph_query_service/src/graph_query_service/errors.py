"""Exception hierarchy for the graph query service.

Catch GraphQueryServiceError to handle any error raised by this package.
"""


class GraphQueryServiceError(Exception):
    """Base class for all errors raised by graph_query_service."""


class ConfigurationError(GraphQueryServiceError):
    """The service environment is missing or has an invalid setting."""


class GraphQueryExecutionError(GraphQueryServiceError):
    """Neo4j could not be reached or the manifest query failed."""
