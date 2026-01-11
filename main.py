import os
from logging import getLogger
import json
from typing import Optional, Iterable
from itertools import islice

import dotenv
from fastapi import FastAPI, status, Depends
from math import inf
from pyproj import CRS, Transformer
from pyproj.enums import PJType
from pyproj.exceptions import CRSError, ProjError
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from pyproj.transformer import AreaOfInterest as PJAreaOfInterest
from pyproj.database import query_crs_info

from database import init_db, get_db
from models.api_models import TransformRequest, TransformResponse, TransformErrorResponse, \
    QueryProjectionRequest, ProjectionResult, CrsQueryRequest, CrsQueryResponse, QueryProjectionResponse
from models.crs_model import PROJJSONModel, SimpleCrsModel
from services.crs_service import CRSService

app = FastAPI(title="CRS Transformation and Query API", version="1.0.0", docs_url="/docs")
logger = getLogger(__name__)
dotenv.load_dotenv()

allowed_origins = os.getenv("ALLOWED_ORIGINS", '').split(',')

@app.on_event("startup")
def startup_event():
    init_db()
    db = next(get_db())
    CRSService.populate_cache(db)
    logger.info("Database initialized and cache populated")


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def coordinates_within_aoi(coordinates, aoi: PJAreaOfInterest) -> bool:
    for lat, lon in coordinates:
        if not (aoi.west_lon_degree <= lon <= aoi.east_lon_degree and
                aoi.south_lat_degree <= lat <= aoi.north_lat_degree):
            return False
    return True

@app.post('/transform', tags=['transform'])
def query_projection(
        request: QueryProjectionRequest,
        db: Session = Depends(get_db)
) -> QueryProjectionResponse:
    aoi = request.area_of_interest.to_pj_area_of_interest() if request.area_of_interest else None

    # Use database query instead of pyproj query
    cached_crs, count = CRSService.query_crs(
        db=db,
        query=request.query,
        west_lon=aoi.west_lon_degree if aoi else None,
        south_lat=aoi.south_lat_degree if aoi else None,
        east_lon=aoi.east_lon_degree if aoi else None,
        north_lat=aoi.north_lat_degree if aoi else None,
        limit=request.pagination.size if request.pagination else 20,
        offset=((request.pagination.page - 1) * request.pagination.size) if request.pagination else 0
    )

    crs_list = [CRS.from_epsg(int(cached.code)) for cached in cached_crs]

    if not request.coordinates:
        return QueryProjectionResponse(
            count=count,
            results=[ProjectionResult.from_crs(crs)
            for crs in crs_list
        ])

    results = []
    # We need to setup spatialite to handle this in the db,
    # so for now we return `success=False` for out-of-aoi projections
    for crs_from in crs_list:
        # crs_from = CRS.from_epsg(crs_info.code)
        try:
            transformer = Transformer.from_crs(crs_from, request.crs_to)
            out_coordinates = list(transformer.itransform(request.coordinates))
            success = True
            if aoi and not coordinates_within_aoi(out_coordinates, request.area_of_interest.to_pj_area_of_interest()):
                success = False
            if inf in out_coordinates[0] or any(any(map(lambda v: v != v, coord)) for coord in out_coordinates):
                success = False
                out_coordinates = []
            results.append(ProjectionResult.from_crs(crs_from, coordinates=list(out_coordinates), success=success))
        except (ProjError, ValueError):
            results.append(ProjectionResult(success=False, crs=SimpleCrsModel.from_crs(crs_from), coordinates=[]))

    return QueryProjectionResponse(
        count=count,
        results=results)