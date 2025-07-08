# Copyright 2025 Alant
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# infrastructure/models.py
import uuid as uuid_pkg  # To avoid conflict with column name
from datetime import datetime

import sqlalchemy as sa  # Import for sa.false()
from sqlalchemy import Boolean, Column, DateTime, TypeDecorator
from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID  # For PostgreSQL UUID type
from sqlalchemy.orm import relationship, Mapped, mapped_column # Consolidated imports
from sqlalchemy.sql import func  # For server-side default timestamps if preferred

# Custom UUID type is now imported from aletheia_common.db.custom_types
# The local definition has been removed.

# Import Base from the common db module
from aletheia_common.db.base import Base
# Import custom UUID type from common db module
from aletheia_common.db.custom_types import UUID as CommonUUID # Alias to avoid conflict if local UUID is still temp present


import enum # Import Python's enum module

# --- Enum Types for choices ---
class ContributionTypeEnum(enum.Enum): # Inherit from Python's enum.Enum
    DISCOVERED_BY_JOB = "discovered_by_job"
    VERIFIED_BY_USER = "verified_by_user"
    ANALYZED_BY_USER = "analyzed_by_user"
    TAGGED_BY_USER = "tagged_by_user"


class ConjectureStatusEnum(enum.Enum): # Inherit from Python's enum.Enum
    PROPOSED = "proposed"
    UNDER_REVIEW = "under_review"
    VALIDATED = "validated"  # Meaning the conjecture statement is well-formed and interesting
    REFUTED = "refuted"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"


# --- Association Table for Many-to-Many: DerivedConjecture to HitDB ---
conjecture_hits_association = Table(
    "conjecture_hits_association",
    Base.metadata,
    Column(
        "conjecture_id",
        Integer,
        ForeignKey("derived_conjectures.id"),
        primary_key=True,
    ),
    Column(
        "hit_id", Integer, ForeignKey("discovery_hits.id"), primary_key=True
    ),
)


class ResearcherDB(Base):
    __tablename__ = "researchers"

    id: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    orcid: Mapped[Optional[str]] = mapped_column(
        String(50), unique=True, nullable=True, index=True
    )  # ORCID iDs are typically 19 chars like 0000-0002-1825-0097
    hashed_password: Mapped[str] = mapped_column(
        String, nullable=False
    )  # Store hashed passwords only
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False) # server_default=sa.false() could be added if needed
    disabled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default=sa.false()
    )  # Ensures field exists with Mapped syntax

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    submitted_jobs = relationship("JobDB", back_populates="submitter")
    attributions = relationship(
        "DiscoveryAttributionDB", back_populates="researcher"
    )
    proposed_conjectures = relationship(
        "DerivedConjectureDB", back_populates="proposer"
    )

    def __repr__(self):
        return (
            f"<ResearcherDB(username='{self.username}', email='{self.email}')>"
        )


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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Alternatively, for database server-side default:
    # created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Timestamp when the job was last updated.
    # Updates on every modification to the job record.
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    # Alternatively, for database server-side default:
    # updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship to HitDB: A job can have multiple hits.
    # `back_populates` creates a bidirectional relationship.
    # `cascade="all, delete-orphan"` means that when a JobDB is deleted,
    # all its associated HitDB records are also deleted.
    hits = relationship(
        "HitDB", back_populates="job", cascade="all, delete-orphan"
    )

    # Link to the researcher who submitted the job
    submitter_id = Column(
        UUID(as_uuid=True),
        ForeignKey("researchers.id"),
        nullable=True,
        index=True,
    )  # Nullable if jobs can be anonymous or system-generated
    submitter = relationship("ResearcherDB", back_populates="submitted_jobs")

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
    job_id = Column(
        String, ForeignKey("discovery_jobs.id"), nullable=False, index=True
    )  # This is UUID string from JobDB.id

    # The components of the abc-triple.
    # Consider using BigInteger if numbers can exceed standard integer limits (approx 2*10^9)
    # from sqlalchemy import BigInteger
    a = Column(Integer, nullable=False)  # Or BigInteger
    b = Column(Integer, nullable=False)
    c = Column(Integer, nullable=False)  # c = a + b

    # The calculated quality 'q' of the triple. Indexed for sorting/querying by quality.
    quality = Column(Float, nullable=False, index=True)

    # Timestamp when this hit was recorded.
    discovered_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    # Alternatively, for database server-side default:
    # discovered_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to JobDB: A hit belongs to one job.
    job = relationship("JobDB", back_populates="hits")

    # Relationships for collaboration
    attributions = relationship(
        "DiscoveryAttributionDB",
        back_populates="hit",
        cascade="all, delete-orphan",
    )
    conjectures_supported = relationship(
        "DerivedConjectureDB",
        secondary=conjecture_hits_association,
        back_populates="supporting_hits",
    )

    def __repr__(self):
        return f"<HitDB(job_id='{self.job_id}', a={self.a}, b={self.b}, c={self.c}, quality={self.quality:.4f})>"


class DiscoveryAttributionDB(Base):
    __tablename__ = "discovery_attributions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hit_id = Column(
        Integer, ForeignKey("discovery_hits.id"), nullable=False, index=True
    )
    researcher_id = Column(
        UUID(as_uuid=True),
        ForeignKey("researchers.id"),
        nullable=False,
        index=True,
    )

    contribution_type = Column(
        SAEnum(ContributionTypeEnum, name="contribution_type_enum"),
        nullable=False,
    )
    # Example values for contribution_type: 'discovered_by_job' (could link to job's submitter),
    # 'verified_by_user', 'analyzed_by_user', 'tagged_by_user'

    details = Column(
        Text, nullable=True
    )  # E.g., verification notes, analysis summary
    attributed_at = Column(DateTime(timezone=True), server_default=func.now())

    hit = relationship("HitDB", back_populates="attributions")
    researcher = relationship("ResearcherDB", back_populates="attributions")

    def __repr__(self):
        return f"<DiscoveryAttributionDB(hit_id={self.hit_id}, researcher_id='{self.researcher_id}', type='{self.contribution_type}')>"


class DerivedConjectureDB(Base):
    __tablename__ = "derived_conjectures"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)  # Can include LaTeX, markdown

    status = Column(
        SAEnum(ConjectureStatusEnum, name="conjecture_status_enum"),
        nullable=False,
        default=ConjectureStatusEnum.PROPOSED,
        index=True,
    )

    proposer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("researchers.id"),
        nullable=False,
        index=True,
    )
    proposer = relationship(
        "ResearcherDB", back_populates="proposed_conjectures"
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Many-to-many relationship with HitDB for supporting evidence
    supporting_hits = relationship(
        "HitDB",
        secondary=conjecture_hits_association,
        back_populates="conjectures_supported",
    )

    # Potentially, a self-referential relationship for related conjectures (e.g., parent/child conjectures)
    # parent_conjecture_id = Column(Integer, ForeignKey('derived_conjectures.id'), nullable=True)
    # related_conjectures = relationship("DerivedConjectureDB", remote_side=[id])

    def __repr__(self):
        return f"<DerivedConjectureDB(title='{self.title[:50]}...', proposer_id='{self.proposer_id}', status='{self.status}')>"


# Ensure Enums are created in the database if not automatically handled by SQLAlchemy for all DBs
# For PostgreSQL, SAEnum(..., name="my_enum_type_name") handles this.
# from sqlalchemy import event
# from .database import engine
# ContributionTypeEnum.create(engine, checkfirst=True)
# ConjectureStatusEnum.create(engine, checkfirst=True)
# This is typically done via migrations (Alembic) in production.
# For `create_all`, ensure the enums are defined before tables using them.

# --- Nuevos Modelos para Conceptos y Relaciones ---
from sqlalchemy.dialects.postgresql import JSONB # Para el tipo JSONB específico de PostgreSQL
from ..core.domain_models import ConceptType as DomainConceptType # Importar el Enum de dominio
# Nota: uuid_pkg ya está importado arriba. func, DateTime, Text, String, ForeignKey, relationship, SAEnum, Column también.
# La clase UUID personalizada también está definida arriba.

# Modelo SQLAlchemy para ScientificConcept
class ScientificConceptDB(Base):
    __tablename__ = "scientific_concepts"

    id: Mapped[uuid_pkg.UUID] = mapped_column(CommonUUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    concept_type: Mapped[DomainConceptType] = mapped_column(SAEnum(DomainConceptType, name="concept_type_enum_v2", create_constraint=True, inherit_schema=False), nullable=False, index=True)
    properties: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships will be defined here for SQLAlchemy ORM to understand connections
    # Even if the other side (e.g. DirectedRelationshipDB) defines the foreign key
    relationships_as_source: Mapped[List["DirectedRelationshipDB"]] = relationship(foreign_keys="DirectedRelationshipDB.source_concept_id", back_populates="source_concept")
    relationships_as_target: Mapped[List["DirectedRelationshipDB"]] = relationship(foreign_keys="DirectedRelationshipDB.target_concept_id", back_populates="target_concept")


    def __repr__(self):
        return f"<ScientificConceptDB(id='{self.id}', name='{self.name}', type='{self.concept_type.value if self.concept_type else None}')>"

# Modelo SQLAlchemy para DirectedRelationship
class DirectedRelationshipDB(Base):
    __tablename__ = "directed_relationships"

    id: Mapped[uuid_pkg.UUID] = mapped_column(CommonUUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    source_concept_id: Mapped[uuid_pkg.UUID] = mapped_column(CommonUUID(as_uuid=True), ForeignKey("scientific_concepts.id", name="fk_relationship_source_concept"), nullable=False, index=True)
    target_concept_id: Mapped[uuid_pkg.UUID] = mapped_column(CommonUUID(as_uuid=True), ForeignKey("scientific_concepts.id", name="fk_relationship_target_concept"), nullable=False, index=True)

    type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    properties: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones ORM con ScientificConceptDB
    source_concept: Mapped["ScientificConceptDB"] = relationship(
        foreign_keys=[source_concept_id], back_populates="relationships_as_source"
    )
    target_concept: Mapped["ScientificConceptDB"] = relationship(
        foreign_keys=[target_concept_id], back_populates="relationships_as_target"
    )

    def __repr__(self):
        return f"<DirectedRelationshipDB(id='{self.id}', type='{self.type}', source='{self.source_concept_id}', target='{self.target_concept_id}')>"


# --- Modelo ORM para AnalysisData ---
# Ensure Mapped, mapped_column are available (already imported at the top)
# uuid_pkg, DateTime, func, JSONB, String, Base ya están importados y definidos.
from typing import Dict, Any, List # Para tipado de JSONB y List para Mapped[List[...]]

class AnalysisModel(Base):
    __tablename__ = 'analyses'

    id: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    session_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False) # String con longitud
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    model_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=True)
    metrics: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(100), nullable=False) # String con longitud

    def __repr__(self):
        return f"<AnalysisModel(id='{self.id}', session_id='{self.session_id}', status='{self.status}')>"
