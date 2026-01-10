import os
from logging import getLogger
import json
from typing import Optional, Iterable
from itertools import islice

import dotenv
from fastapi import FastAPI, status
from pyproj import CRS, Transformer
from pyproj.enums import PJType
from pyproj.exceptions import CRSError, ProjError
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from pyproj.transformer import AreaOfInterest as PJAreaOfInterest
from pyproj.database import query_crs_info

from models.api_models import TransformRequest, TransformResponse, TransformErrorResponse, \
    QueryProjectionRequest, ProjectionResult, CrsQueryRequest, CrsQueryResponse, QueryProjectionResponse
from models.crs_model import PROJJSONModel, SimpleCrsModel

app = FastAPI(title="CRS Transformation and Query API", version="1.0.0")
logger = getLogger(__name__)
dotenv.load_dotenv()

allowed_origins = os.getenv("ALLOWED_ORIGINS", '').split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def paginate_iterable(items: Iterable, page: int, size: int) -> list:
    if page < 1 or size < 1:
        return []
    start = (page - 1) * size
    end = start + size
    return list(islice(items, start, end))

def coordinates_within_aoi(coordinates, aoi: PJAreaOfInterest) -> bool:
    for lat, lon in coordinates:
        if not (aoi.west_lon_degree <= lon <= aoi.east_lon_degree and
                aoi.south_lat_degree <= lat <= aoi.north_lat_degree):
            return False
    return True

def filter_crs(crs_info, query: str, code: Optional[str] = None) -> bool:
    try:
        crs = CRS.from_epsg(crs_info.code)
        if code and str(crs_info.code) != code:
            return False
        if query and query.lower() not in crs.name.lower() and query not in str(crs.srs).lower():
            return False
        return True
    except CRSError:
        return False

def query_crs(request: CrsQueryRequest) -> QueryProjectionResponse:
    aoi = None
    if request.area_of_interest:
        aoi = request.area_of_interest.to_pj_area_of_interest()
    crs_list = [
        CRS.from_epsg(crs.code) for crs in query_crs_info(
            auth_name="EPSG",
            area_of_interest=aoi,
            pj_types=[PJType.PROJECTED_CRS])
        if filter_crs(crs, request.query)
    ]
    results = map(ProjectionResult.from_crs, crs_list)
    paginated_results = paginate_iterable(results, request.pagination.page, request.pagination.size)
    return QueryProjectionResponse(count=len(crs_list), results=paginated_results)

@app.post('/transform',
  tags=['transform'],
)
def query_projection(request: QueryProjectionRequest) -> QueryProjectionResponse:
    if not request.coordinates or len(request.coordinates) == 0 or not request.area_of_interest:
        return query_crs(
            CrsQueryRequest(
                area_of_interest=request.area_of_interest,
                pagination=request.pagination,
                query=request.query
            ))
    aoi = request.area_of_interest.to_pj_area_of_interest()
    crs_list = [
        CRS.from_epsg(crs.code) for crs in query_crs_info(
            auth_name="EPSG",
            area_of_interest=aoi,
            pj_types=[PJType.PROJECTED_CRS])
        if filter_crs(crs, request.query)
    ]
    crs_to = CRS.from_user_input(request.crs_to)
    results = []
    for crs_from in crs_list:
        # crs_from = CRS.from_epsg(crs_info.code)
        try:
            transformer = Transformer.from_crs(crs_from, crs_to)
            out_coordinates = list(transformer.itransform(request.coordinates))
            if aoi and not coordinates_within_aoi(out_coordinates, request.area_of_interest.to_pj_area_of_interest()):
                continue
            results.append(ProjectionResult.from_crs(crs_from, coordinates=list(out_coordinates)))
        except ProjError:
            results.append(ProjectionResult(success=False, crs=SimpleCrsModel.from_crs(crs_from), coordinates=[]))
    paginated_results = paginate_iterable(results, request.pagination.page, request.pagination.size)
    return QueryProjectionResponse(results=paginated_results, count=len(crs_list))
