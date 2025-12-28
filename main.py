from logging import getLogger

from fastapi import FastAPI, status
from pyproj import CRS, Transformer
from pyproj.enums import PJType
from pyproj.exceptions import CRSError, ProjError
from starlette.responses import JSONResponse
from pyproj.transformer import AreaOfInterest
from pyproj.database import query_crs_info

from models import TransformRequest, TransformResponse, TransformErrorResponse, QueryProjectionResponse, \
    QueryProjectionRequest, QueryProjectionQueryResult

app = FastAPI()
logger = getLogger(__name__)

@app.post('/transform',
    responses={
        status.HTTP_200_OK: {"model": TransformResponse, "description": "The result of the geocoding"},
        status.HTTP_400_BAD_REQUEST: {
            "model": TransformErrorResponse,
            "description": "An error message describing what went wrong",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": TransformErrorResponse,
            "description": "An error message describing what went wrong",
        },
    },
)
def transform_coordinates(request: TransformRequest):
    try:
        crs_from = CRS.from_user_input(request.crs_from)
    except CRSError:
        msg = f"Input CRS '{request.crs_from}' is invalid"
        return JSONResponse(msg, 400)

    try: 
        crs_to = CRS.from_user_input(request.crs_to)
    except CRSError:
        msg = f"Output CRS '{request.crs_to}' is invalid"
        return JSONResponse(msg, 400)
    
    transformer = Transformer.from_crs(crs_from, crs_to)
    out_coordinates = []
    for in_coordinates in request.coordinates:
        out_coordinates.append(transformer.transform(*in_coordinates))

    return TransformResponse(coordinates=out_coordinates)

@app.post('/query',
    responses={
        status.HTTP_200_OK: {"model": QueryProjectionResponse, "description": "The result of the geocoding"},
        status.HTTP_400_BAD_REQUEST: {
            "model": TransformErrorResponse,
            "description": "An error message describing what went wrong",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": TransformErrorResponse,
            "description": "An error message describing what went wrong",
        },
    },
)
def query_projection(request: QueryProjectionRequest):
    area_of_interest = AreaOfInterest(
        west_lon_degree=request.area_of_interest.southwest[1],
        south_lat_degree=request.area_of_interest.southwest[0],
        east_lon_degree=request.area_of_interest.northeast[1],
        north_lat_degree=request.area_of_interest.northeast[0],
    )
    crs_list = query_crs_info( auth_name="EPSG", pj_types=[PJType.PROJECTED_CRS], area_of_interest=area_of_interest, contains=False)
    crs_to = CRS.from_user_input(request.crs_to)
    results = []
    print(crs_list)
    for crs_info in crs_list:
        crs_from = CRS.from_epsg(crs_info.code)
        try:
            transformer = Transformer.from_crs(crs_from, crs_to)
            out_coordinates = list(transformer.itransform(request.coordinates))
            coords_inside_aoi = all(
                area_of_interest.west_lon_degree <= lon <= area_of_interest.east_lon_degree and
                area_of_interest.south_lat_degree <= lat <= area_of_interest.north_lat_degree
                for lat, lon in out_coordinates
            )
            if not coords_inside_aoi:
                continue
            results.append(QueryProjectionQueryResult(
                crs=crs_from.to_string(),
                coordinates=out_coordinates
            ))
        except ProjError:
            results.append(QueryProjectionQueryResult(success=False, crs=crs_from.to_string(), coordinates=[]))

    return QueryProjectionResponse(results=results)
