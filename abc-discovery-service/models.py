from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class JobDB(Base):
    __tablename__ = "discovery_jobs"
    id = Column(String, primary_key=True, index=True)
    status = Column(String, default="pending")
    n_calls = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    hits = relationship("HitDB", back_populates="job")

class HitDB(Base):
    __tablename__ = "discovery_hits"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("discovery_jobs.id"))
    a = Column(Integer)
    b = Column(Integer)
    c = Column(Integer)
    quality = Column(Float)
    job = relationship("JobDB", back_populates="hits")
