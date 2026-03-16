from typing import Any, List, Optional
from pydantic import BaseModel, Field
import requests
from fastapi import (
    APIRouter,
    Request
)

router = APIRouter(
    prefix="/models"
)

class Model(BaseModel):
    id: str
    object: str
    created: int
    owned_by: str
    permission: List[Any] = Field(default_factory=list)  # vLLM returns list of dicts
    root: str
    parent: Optional[str] = None

class ModelResponse(BaseModel):
    object: str
    data: List[Model] = Field(default_factory=list)


@router.get("")
@router.get("/")
def models(
    request: Request
) -> ModelResponse:
    node_url = f"{request.app.state.node_address}/v1/models"
    models = requests.get(node_url).json()["data"]
    return ModelResponse(object="list", data=[Model(**model) for model in models])