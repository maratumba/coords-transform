from pydantic import BaseModel
from typing import Tuple, List, Optional

from pyproj import CRS
from pyproj.transformer import AreaOfInterest as PJAreaOfInterest
from models.crs_model import PROJJSONModel, SimpleCrsModel

class AreaOfInterest(BaseModel):
    northeast: Tuple[float, float]  # (latitude, longitude)
    southwest: Tuple[float, float]  # (latitude, longitude)

    def to_pj_area_of_interest(self) -> PJAreaOfInterest:
        return PJAreaOfInterest(
            west_lon_degree=self.southwest[1],
            south_lat_degree=self.southwest[0],
            east_lon_degree=self.northeast[1],
            north_lat_degree=self.northeast[0],
        )

class Pagination(BaseModel):
    page: int = 1
    size: int = 10

class TransformRequest(BaseModel):
    crs_from_list: List[str]
    crs_to: str
    coordinates: List[List[float]]
    area_of_interest: Optional[AreaOfInterest]

class TransformResponse(BaseModel):
    coordinates: List[List[float]]

class TransformErrorResponse(BaseModel):
    msg: str

class QueryProjectionRequest(BaseModel):
    coordinates: List[List[float]]
    query: str
    crs_to: str
    crs_from_list: Optional[List[str]]
    pagination: Optional[Pagination] = None
    area_of_interest: Optional[AreaOfInterest]

class ProjectionResult(BaseModel):
    crs: SimpleCrsModel
    coordinates: Optional[List[List[float]]]
    success: bool = True

    @staticmethod
    def from_crs(crs: CRS, coordinates: Optional[List[List[float]]] = None) -> "ProjectionResult":
        crs = SimpleCrsModel.from_crs(crs)
        return ProjectionResult(crs=crs, coordinates=coordinates, success=True)

class QueryProjectionResponse(BaseModel):
    count: int
    results: List[ProjectionResult]

class CrsQueryRequest(BaseModel):
    query: str
    pagination: Optional[Pagination] = None
    area_of_interest: Optional[AreaOfInterest] = None

class CrsQueryResponse(BaseModel):
    results: List[SimpleCrsModel]
    count: int
