from fastapi import FastAPI, status
from models import TransformRequest, TransformResponse, TransformErrorResponse
from pyproj import CRS, Transformer
from pyproj.exceptions import CRSError
from starlette.responses import JSONResponse

app = FastAPI()


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


