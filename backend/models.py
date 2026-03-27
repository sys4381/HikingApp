from sqlalchemy import Boolean, Column, Float, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class TrailGroup(Base):
    __tablename__ = "trail_groups"

    id = Column(Integer, primary_key=True, index=True)
    center_lat = Column(Float, nullable=False)
    center_lon = Column(Float, nullable=False)
    radius_km = Column(Float, default=20.0)
    name = Column(String, index=True)

    trails = relationship("Trail", back_populates="group")


class Trail(Base):
    __tablename__ = "trails"

    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, index=True)
    
    country = Column(String, index=True)
    nearest_town = Column(String, index=True)
    
    length_km = Column(Float)
    is_loop = Column(Boolean, default=False)
    
    start_lat = Column(Float)
    start_lon = Column(Float)
    end_lat = Column(Float)
    end_lon = Column(Float)
    
    elevation_gain_m = Column(Float)
    difficulty_score = Column(Float)
    difficulty_category = Column(String)  # Easy, Moderate, Strenuous
    
    polyline = Column(String)  # JSON string of [[lat, lon], ...]
    
    group_id = Column(Integer, ForeignKey("trail_groups.id"), nullable=True)
    
    group = relationship("TrailGroup", back_populates="trails")
