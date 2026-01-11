from sqlalchemy import Column, Integer, String, Float, Boolean, Text, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class CRSCache(Base):
    __tablename__ = "crs_cache"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, index=True, nullable=False)
    auth_name = Column(String, default="EPSG", nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    area_name = Column(String)
    west_lon = Column(Float)
    south_lat = Column(Float)
    east_lon = Column(Float)
    north_lat = Column(Float)
    proj_string = Column(Text)
    wkt = Column(Text)
    deprecated = Column(Boolean, default=False)

    __table_args__ = (
        Index('idx_crs_name', 'name'),
        Index('idx_crs_area', 'west_lon', 'south_lat', 'east_lon', 'north_lat'),
    )