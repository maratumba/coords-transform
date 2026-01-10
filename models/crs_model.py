from pydantic import BaseModel, Field
from typing import Optional, List, Union, Literal, Any
from enum import Enum

from pyproj import CRS


class UnitType(str, Enum):
    ANGULAR = "angularUnit"
    LINEAR = "linearUnit"
    SCALE = "scaleUnit"
    PARAMETRIC = "parametricUnit"
    TEMPORAL = "temporalUnit"


class Unit(BaseModel):
    type: Optional[UnitType] = None
    name: str
    conversion_factor: Optional[float] = Field(None, alias="conversionFactor")
    id: Optional[Any] = None


class Identifier(BaseModel):
    authority: str
    code: Union[str, int]
    version: Optional[str] = None
    authority_citation: Optional[str] = Field(None, alias="authorityCitation")
    uri: Optional[str] = None


class Axis(BaseModel):
    name: str
    abbreviation: str
    direction: str
    unit: Optional[Unit] = None


class CoordinateSystem(BaseModel):
    subtype: str
    axis: List[Axis]
    id: Optional[Identifier] = None


class PrimeMeridian(BaseModel):
    name: str
    longitude: float
    id: Optional[Identifier] = None


class Ellipsoid(BaseModel):
    name: str
    semi_major_axis: float = Field(alias="semiMajorAxis")
    inverse_flattening: Optional[float] = Field(None, alias="inverseFlattening")
    semi_minor_axis: Optional[float] = Field(None, alias="semiMinorAxis")
    id: Optional[Identifier] = None


class Datum(BaseModel):
    type: str
    name: str
    ellipsoid: Optional[Ellipsoid] = None
    prime_meridian: Optional[PrimeMeridian] = Field(None, alias="primeMeridian")
    id: Optional[Identifier] = None
    scope: Optional[str] = None
    area: Optional[str] = None
    bbox: Optional[Any] = None


class Conversion(BaseModel):
    name: str
    method: Any
    parameters: Optional[List[Any]] = None
    id: Optional[Identifier] = None


class BoundCRS(BaseModel):
    source_crs: Any = Field(alias="sourceCRS")
    target_crs: Any = Field(alias="targetCRS")
    transformation: Any


class PROJJSONModel(BaseModel):
    schema_: str = Field(alias="$schema")
    type: Literal[
        "GeographicCRS",
        "ProjectedCRS",
        "VerticalCRS",
        "CompoundCRS",
        "BoundCRS",
        "EngineeringCRS",
        "TemporalCRS",
        "DerivedProjectedCRS"
    ]
    name: str
    datum: Optional[Datum] = None
    coordinate_system: CoordinateSystem = Field(alias="coordinateSystem")
    scope: Optional[str] = None
    area: Optional[str] = None
    bbox: Optional[Any] = None
    id: Optional[Identifier] = None
    remarks: Optional[str] = None
    base_crs: Optional[Any] = Field(None, alias="baseCRS")
    conversion: Optional[Conversion] = None
    components: Optional[List[Any]] = None

    class Config:
        populate_by_name = True

class SimpleDatum(BaseModel):
    type: str
    name: str
    id: Optional[Identifier] = None
    scope: Optional[str] = None
    area: Optional[str] = None
    bbox: Optional[Any] = None

class BBox(BaseModel):
    west: float
    south: float
    east: float
    north: float

class AreaOfUse(BaseModel):
    name: str
    bbox: Optional[BBox] = None

class SimpleCrsModel(BaseModel):
    name: str
    remarks: Optional[str] = None
    datum: Optional[str] = None
    area: Optional[AreaOfUse] = None
    datum_scope: Optional[str] = None
    scope: Optional[str] = None
    srs: Optional[str] = None
    crs_type: str

    @staticmethod
    def from_crs(crs: CRS) -> "SimpleCrsModel":
        area_of_use = AreaOfUse(
            name=crs.area_of_use.name,
            bbox=BBox(
                west=crs.area_of_use.west,
                south=crs.area_of_use.south,
                east=crs.area_of_use.east,
                north=crs.area_of_use.north,
            ) if crs.area_of_use.west is not None else None
        )
        return SimpleCrsModel(
            name=crs.name,
            area=area_of_use,
            srs=crs.to_string(),
            remarks=crs.remarks,
            datum=crs.datum.name if crs.datum else None,
            datum_scope=crs.datum.scope if crs.datum else None,
            scope=crs.scope,
            crs_type=crs.type_name,
        )
