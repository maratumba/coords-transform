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