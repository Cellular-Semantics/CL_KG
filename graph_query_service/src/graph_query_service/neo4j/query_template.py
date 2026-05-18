def build_query() -> str:
    return (
        "WITH $cell_labels AS cell_labels\n"
        "MATCH (n:Cell)-[:composed_primarily_of]-(child:Cell_cluster)\n"
        "WHERE ANY(label IN n.label WHERE label IN cell_labels)\n"
        "WITH DISTINCT child\n"
        "WHERE child:Cell_cluster\n"
        "OPTIONAL MATCH (child)-[:has_source]->(dataset:Dataset)\n"
        "RETURN child, dataset\n"
        "ORDER BY child.iri"
    )


def summarize_cell_labels(cell_labels: list[str], max_length: int = 280) -> str:
    compact = ", ".join(cell_labels)
    summary = f"cell_labels[{len(cell_labels)}]: {compact}"
    if len(summary) <= max_length:
        return summary
    return f"{summary[: max_length - 3]}..."
