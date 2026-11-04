import os
from dataclasses import dataclass

from graph_query_service.errors import ConfigurationError


@dataclass(frozen=True)
class Settings:
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    neo4j_database: str = "neo4j"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"


def get_settings() -> Settings:
    """Read settings from the environment.

    Raises:
        ConfigurationError: a NEO4J_* variable is not set or PORT is not an integer.
    """
    neo4j_uri = os.environ.get("NEO4J_URI", "").strip()
    neo4j_user = os.environ.get("NEO4J_USER", "").strip()
    neo4j_password = os.environ.get("NEO4J_PASSWORD", "").strip()
    if not neo4j_uri:
        raise ConfigurationError("NEO4J_URI environment variable must be set.")
    if not neo4j_user:
        raise ConfigurationError("NEO4J_USER environment variable must be set.")
    if not neo4j_password:
        raise ConfigurationError("NEO4J_PASSWORD environment variable must be set.")

    port_text = os.environ.get("PORT", "8000").strip()
    try:
        port = int(port_text)
    except ValueError as exc:
        raise ConfigurationError(f"PORT must be an integer, got {port_text!r}.") from exc

    return Settings(
        neo4j_uri=neo4j_uri,
        neo4j_user=neo4j_user,
        neo4j_password=neo4j_password,
        neo4j_database=os.environ.get("NEO4J_DATABASE", "neo4j").strip() or "neo4j",
        host=os.environ.get("HOST", "0.0.0.0").strip() or "0.0.0.0",
        port=port,
        log_level=os.environ.get("LOG_LEVEL", "INFO").strip() or "INFO",
    )
