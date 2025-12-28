from pydantic import BaseModel, Field
from typing import Tuple, List
from collections import namedtuple


class TransformRequest(BaseModel):
    crs_from: str
    crs_to: str
    coordinates: List[List[float]]

class TransformResponse(BaseModel):
    coordinates: List[List[float]]

class TransformErrorResponse(BaseModel):
    msg: str

class AreaOfInterest(BaseModel):
    northeast: Tuple[float, float]  # (latitude, longitude)
    southwest: Tuple[float, float]  # (latitude, longitude)

class QueryProjectionRequest(BaseModel):
    coordinates: List[List[float]]
    crs_to: str
    area_of_interest: AreaOfInterest

class QueryProjectionQueryResult(BaseModel):
    crs: str
    coordinates: List[List[float]]
    success: bool = True

class QueryProjectionResponse(BaseModel):
    results: List[QueryProjectionQueryResult]