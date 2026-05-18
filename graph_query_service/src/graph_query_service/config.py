import os
from dataclasses import dataclass


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
    neo4j_uri = os.environ.get("NEO4J_URI", "").strip()
    neo4j_user = os.environ.get("NEO4J_USER", "").strip()
    neo4j_password = os.environ.get("NEO4J_PASSWORD", "").strip()
    if not neo4j_uri:
        raise RuntimeError("NEO4J_URI environment variable must be set.")
    if not neo4j_user:
        raise RuntimeError("NEO4J_USER environment variable must be set.")
    if not neo4j_password:
        raise RuntimeError("NEO4J_PASSWORD environment variable must be set.")

    port_text = os.environ.get("PORT", "8000").strip()
    return Settings(
        neo4j_uri=neo4j_uri,
        neo4j_user=neo4j_user,
        neo4j_password=neo4j_password,
        neo4j_database=os.environ.get("NEO4J_DATABASE", "neo4j").strip() or "neo4j",
        host=os.environ.get("HOST", "0.0.0.0").strip() or "0.0.0.0",
        port=int(port_text),
        log_level=os.environ.get("LOG_LEVEL", "INFO").strip() or "INFO",
    )
