from pydantic import BaseModel
from typing import List, Optional


class ExtractGraphRequest(BaseModel):
    text: str


class NodeResponse(BaseModel):
    id: str
    label: str
    type: Optional[str]
    source: str


class EdgeResponse(BaseModel):
    head: str
    tail: str
    type: str
    confidence: float


class GraphResponse(BaseModel):
    nodes: List[NodeResponse]
    edges: List[EdgeResponse]
