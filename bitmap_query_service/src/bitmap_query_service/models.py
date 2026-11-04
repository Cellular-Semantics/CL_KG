from typing import Literal

from pydantic import BaseModel, Field, model_validator


class BitmapQueryRequest(BaseModel):
    # Used in the bitmap filename, so only allow version-like values
    # (e.g. "2025-11-08", "stable"): no path separators or leading dots.
    census_version: str = Field(
        min_length=1, max_length=64, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$"
    )
    operation: Literal["lookup"]
    clusters: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_lookup_arity(self):
        if self.operation == "lookup" and len(self.clusters) != 1:
            raise ValueError("lookup requires exactly one cluster IRI")
        return self


class BitmapQueryResponse(BaseModel):
    operation: Literal["lookup"]
    cluster_iris: list[str]
    census_version: str
    count: int
    bitmap_base64: str
