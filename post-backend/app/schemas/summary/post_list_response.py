"""
Fichier pour la class PostListResponse
"""

from typing import List
from pydantic import BaseModel, Field
from app.schemas.summary.post_response_summary import PostResponseSummary

MIN_LIST_COUNT = 0
MAX_LIST_COUNT = 20

class PostListResponse(BaseModel):
    """
    Objet de réponse pour une liste de Post
    """
    posts: List[PostResponseSummary]
    count: int = Field(ge=MIN_LIST_COUNT, le=MAX_LIST_COUNT)
    skip: int = Field(ge=0)
    limit: int = Field(ge=MIN_LIST_COUNT, le=MAX_LIST_COUNT)
