# infrastructure/models.py
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func # For server-side default timestamps if preferred
from datetime import datetime

# Import Base from the database module in the same directory
from .database import Base

class JobDB(Base):
    """
    SQLAlchemy model representing a discovery job.
    Each job corresponds to an execution of the IntelligentSearchUseCase.
    """
    __tablename__ = "discovery_jobs"

    # Job identifier, typically a UUID string. Primary key.
    id = Column(String, primary_key=True, index=True)

    # Status of the job (e.g., "pending", "processing", "completed", "failed").
    # Indexed for faster querying by status.
    status = Column(String, default="pending", index=True)

    # Number of Bayesian optimization calls requested for this job.
    n_calls = Column(Integer, nullable=False)

    # Timestamp when the job was created. Defaults to current UTC time.
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    # Alternatively, for database server-side default:
    # created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Timestamp when the job was last updated.
    # Updates on every modification to the job record.
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    # Alternatively, for database server-side default:
    # updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship to HitDB: A job can have multiple hits.
    # `back_populates` creates a bidirectional relationship.
    # `cascade="all, delete-orphan"` means that when a JobDB is deleted,
    # all its associated HitDB records are also deleted.
    hits = relationship("HitDB", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<JobDB(id='{self.id}', status='{self.status}', n_calls={self.n_calls})>"

class HitDB(Base):
    """
    SQLAlchemy model representing a high-quality abc-triple found during a discovery job.
    """
    __tablename__ = "discovery_hits"

    # Auto-incrementing primary key for the hit.
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign key linking this hit to its parent job. Indexed for faster lookups.
    job_id = Column(String, ForeignKey("discovery_jobs.id"), nullable=False, index=True)

    # The components of the abc-triple.
    a = Column(Integer, nullable=False)
    b = Column(Integer, nullable=False)
    c = Column(Integer, nullable=False) # c = a + b

    # The calculated quality 'q' of the triple. Indexed for sorting/querying by quality.
    quality = Column(Float, nullable=False, index=True)

    # Timestamp when this hit was recorded.
    discovered_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    # Alternatively, for database server-side default:
    # discovered_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to JobDB: A hit belongs to one job.
    job = relationship("JobDB", back_populates="hits")

    def __repr__(self):
        return f"<HitDB(job_id='{self.job_id}', a={self.a}, b={self.b}, c={self.c}, quality={self.quality:.4f})>"

# Potential future additions:
# - User model if authentication is extended beyond a single test user.
# - Model for MLflow experiment tracking if not relying solely on MLflow's own DB schema.
#   (Though MLflow is configured to use the same DB instance, it manages its own tables.)
