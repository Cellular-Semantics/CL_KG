# Bitmap Query Service

## Summary
`bitmap_query_service` is a standalone FastAPI service for reading roaring bitmap files produced by `anndata2rdf`.

The current implementation is intentionally narrow:
- direct `Cell_cluster` IRI lookup only
- no Neo4j resolution
- no Census-backed query flow
- no metadata-driven bitmap discovery
- no bitmap set operations yet

## Current state
The repo already contains a working initial vertical slice in [bitmap_query_service](</Users/ub2/github/CL_KB/bitmap_query_service>).

Implemented pieces:
- service module with Dockerfile, requirements, app code, and tests
- `GET /health`
- `POST /bitmap/query`
- bitmap filename resolution aligned with `anndata2rdf`
- bitmap loading from the shared bitmap volume
- Docker compose wiring in `cl_kb_pipeline/docker-compose.yml`

Current `POST /bitmap/query` behavior:
- supports `lookup` only
- requires exactly one cluster IRI
- requires `census_version`
- resolves the bitmap filename from the cluster IRI
- loads the bitmap from disk
- returns:
  - `operation`
  - `cluster_iris`
  - `census_version`
  - `count`
  - `bitmap_base64`

## API contract

### `GET /health`
Returns simple readiness information and the configured bitmap directory.

### `POST /bitmap/query`
Request JSON:

```json
{
  "census_version": "stable",
  "operation": "lookup",
  "clusters": [
    "http://example.org/cluster/11111111-1111-1111-1111-111111111111"
  ]
}
```

Current response JSON:

```json
{
  "operation": "lookup",
  "cluster_iris": [
    "http://example.org/cluster/11111111-1111-1111-1111-111111111111"
  ],
  "census_version": "stable",
  "count": 12345,
  "bitmap_base64": "BASE64_ENCODED_BITMAP"
}
```

Error behavior:
- `404` when a referenced bitmap file does not exist
- `422` for schema validation failures
- `500` for unreadable or corrupt bitmap files

## Storage and resolution
The service reuses the same bitmap keying convention as `anndata2rdf`.

Resolution rules:
- if the IRI contains a UUID, use that UUID as the storage id
- otherwise, derive a deterministic UUID5 from the full IRI
- construct filenames as `"{storage_id}__{census_version}.bitmap"`

This logic is aligned to [anndata2rdf/src/bitmap_builder.py](/Users/ub2/github/CL_KB/anndata2rdf/src/bitmap_builder.py).

## Module layout

```text
bitmap_query_service/
├── Dockerfile
├── README.md
├── requirements.txt
├── src/
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── bitmap_ops.py
│   ├── bitmap_store.py
│   └── iri_utils.py
└── tests/
```

Key responsibilities:
- `src/main.py`: FastAPI app and HTTP endpoints
- `src/config.py`: environment loading
- `src/models.py`: request and response validation
- `src/iri_utils.py`: IRI to bitmap filename resolution
- `src/bitmap_store.py`: file lookup and bitmap deserialization
- `src/bitmap_ops.py`: bitmap serialization and count helpers

## Deployment
The service is wired into [cl_kb_pipeline/docker-compose.yml](/Users/ub2/github/CL_KB/cl_kb_pipeline/docker-compose.yml).

Current compose shape:
- service name: `bitmap-query-service`
- depends on `anndata2rdf` with `condition: service_completed_successfully`
- exposes port `8010`
- mounts `clkg_bitmap_data` read-only at `/app/bitmaps`
- sets `BITMAP_DIR=/app/bitmaps`

The service treats the bitmap directory as the source of truth. It does not depend on Neo4j or Census at runtime in this version, but it does depend on `anndata2rdf` to populate the shared bitmap volume before startup.

## Testing
Current local test coverage includes:
- IRI storage-id resolution
- bitmap filename derivation
- bitmap loading from disk
- missing-file behavior
- `GET /health`
- successful `lookup` request

## Deferred work
Planned but not implemented:
- `union`
- `intersection`
- `difference`
- CL term input
- graph traversal to `Cell_cluster` IRIs
- Neo4j integration
- Census-backed query endpoints
- production hardening such as auth, metrics, tracing, and caching

## Recommended next steps
If development resumes, the next increments should be:

1. Add `union`, `intersection`, and `difference` to `POST /bitmap/query`.
2. Expand tests to cover multi-bitmap operations and failure modes.
3. Add a graph-aware layer that resolves higher-level inputs to `Cell_cluster` IRIs.
4. Add optional Census-backed endpoints only after the bitmap API contract is stable.
