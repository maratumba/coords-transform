from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from pyproj import CRS
from pyproj.database import query_crs_info
from pyproj.enums import PJType

from models.db_models import CRSCache


class CRSService:
    @staticmethod
    def populate_cache(db: Session):
        """Populate cache with EPSG CRS data"""
        if db.query(CRSCache).count() > 0:
            return  # Already populated

        crs_list = query_crs_info()

        for crs_info in crs_list:
            try:
                crs = CRS.from_epsg(crs_info.code)
                cache_entry = CRSCache(
                    code=str(crs_info.code),
                    auth_name=crs_info.auth_name,
                    name=crs_info.name,
                    type=crs_info.type.name,
                    area_name=crs_info.area_of_use.name,
                    west_lon=crs_info.area_of_use.west,
                    south_lat=crs_info.area_of_use.south,
                    east_lon=crs_info.area_of_use.east,
                    north_lat=crs_info.area_of_use.north,
                    proj_string=crs.to_proj4(),
                    wkt=crs.to_wkt(),
                    deprecated=crs_info.deprecated
                )
                db.add(cache_entry)
            except Exception as e:
                continue

        db.commit()

    @staticmethod
    def query_crs(
            db: Session,
            query: Optional[str] = None,
            code: Optional[str] = None,
            west_lon: Optional[float] = None,
            south_lat: Optional[float] = None,
            east_lon: Optional[float] = None,
            north_lat: Optional[float] = None,
            limit: Optional[int] = None,
            offset: Optional[int] = None
    ) -> tuple[List[CRSCache], int]:
        """Query CRS from cache with pagination"""
        filters = [CRSCache.deprecated == False]

        if code:
            filters.append(CRSCache.code == code)

        if query:
            filters.append(
                or_(
                    CRSCache.name.ilike(f"%{query}%"),
                    CRSCache.proj_string.ilike(f"%{query}%")
                )
            )

        if all(v is not None for v in [west_lon, south_lat, east_lon, north_lat]):
            filters.append(
                and_(
                    CRSCache.west_lon <= east_lon,
                    CRSCache.east_lon >= west_lon,
                    CRSCache.south_lat <= north_lat,
                    CRSCache.north_lat >= south_lat
                )
            )

        base_query = db.query(CRSCache).filter(and_(*filters))

        total_count = base_query.count()
        results = base_query.offset(offset).limit(limit).all() if limit else base_query.all()

        return results, total_count