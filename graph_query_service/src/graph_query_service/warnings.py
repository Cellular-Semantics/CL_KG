def cluster_warning(node_iri: str | None, message: str) -> str:
    if node_iri:
        return f"{node_iri}: {message}"
    return message
