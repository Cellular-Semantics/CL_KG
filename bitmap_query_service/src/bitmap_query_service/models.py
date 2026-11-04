from typing import Literal

from pydantic import BaseModel, Field, model_validator


class BitmapQueryRequest(BaseModel):
    census_version: str = Field(min_length=1)
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
