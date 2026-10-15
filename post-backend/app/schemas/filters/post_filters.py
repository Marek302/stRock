"""Filtres du fil communautaire."""
from uuid import UUID
from fastapi import Query
from pydantic import BaseModel, Field

class PostFilters(BaseModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=20)
    search: str | None = None
    location: str | None = None
    exclude_post_ids: list[UUID] | None = None

def get_post_filters(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=20),
                     search: str | None = Query(None), location: str | None = Query(None),
                     exclude_post_ids: list[str] | None = Query(None)):
    excluded = [value.strip() for group in (exclude_post_ids or []) for value in group.split(",") if value.strip()]
    return PostFilters(skip=skip, limit=limit, search=search, location=location, exclude_post_ids=excluded or None)
