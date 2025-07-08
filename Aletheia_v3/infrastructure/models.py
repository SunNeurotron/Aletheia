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
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func  # For server-side default timestamps if preferred

# Custom UUID type for SQLite compatibility
class UUID(TypeDecorator):
    """Platform-independent UUID type.

    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32), storing as string.
    """
    impl = String(32) # Default implementation for non-PG dialects
    cache_ok = True

    def __init__(self, as_uuid=True, *args, **kwargs):
        # as_uuid is relevant for PG, and for our Python-side processing
        self.as_uuid = as_uuid
        # Pass only relevant args to String, or none if String(32) is fixed.
        # String type itself doesn't take *args, **kwargs in its __init__ beyond length.
        # The TypeDecorator's impl is already String(32).
        super(UUID, self).__init__()


    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=self.as_uuid))
        else:
            # For other dialects, we've already set self.impl to String(32)
            return dialect.type_descriptor(String(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        # For PG, PG_UUID handles UUID objects directly if as_uuid=True at type creation.
        # If we pass a string, it's fine. If we pass UUID, it's fine.
        if dialect.name != 'postgresql':
            if isinstance(value, uuid_pkg.UUID):
                return str(value) # Store as string for non-PG
        return value # Return UUID object for PG, string for others

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            # PG_UUID with as_uuid=True should return UUID objects.
            # If it returns string, convert it (though it should handle it).
            if self.as_uuid and isinstance(value, str): return uuid_pkg.UUID(value)
            return value
        else: # For SQLite (String(32))
            if self.as_uuid:
                if isinstance(value, uuid_pkg.UUID): return value
                try:
                    return uuid_pkg.UUID(value) # value is a string from DB
                except (TypeError, ValueError):
                    return value # Or handle error
            return value # Return as string if as_uuid is False (though our default is True)

# Import Base from the database module in the same directory
from .database import Base


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

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    orcid = Column(
        String(50), unique=True, nullable=True, index=True
    )  # ORCID iDs are typically 19 chars like 0000-0002-1825-0097
    hashed_password = Column(
        String, nullable=False
    )  # Store hashed passwords only
    is_admin = Column(Boolean, default=False, nullable=False)
    disabled = Column(
        Boolean, default=False, nullable=False, server_default=sa.false()
    )  # New field for disabling accounts

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
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

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    name = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    # Usar el Enum de dominio con SAEnum para crear un tipo ENUM en la BD (para PG)
    # create_constraint=True es importante para que Alembic lo maneje bien.
    concept_type = Column(SAEnum(DomainConceptType, name="concept_type_enum_v2", create_constraint=True, inherit_schema=False), nullable=False, index=True)
    properties = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<ScientificConceptDB(id='{self.id}', name='{self.name}', type='{self.concept_type.value if self.concept_type else None}')>"

# Modelo SQLAlchemy para DirectedRelationship
class DirectedRelationshipDB(Base):
    __tablename__ = "directed_relationships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    source_concept_id = Column(UUID(as_uuid=True), ForeignKey("scientific_concepts.id", name="fk_relationship_source_concept"), nullable=False, index=True)
    target_concept_id = Column(UUID(as_uuid=True), ForeignKey("scientific_concepts.id", name="fk_relationship_target_concept"), nullable=False, index=True)

    type = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    properties = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones ORM con ScientificConceptDB
    source_concept = relationship(
        "ScientificConceptDB",
        foreign_keys=[source_concept_id],
        backref="relationships_as_source" # Nombre para la colección en ScientificConceptDB
    )
    target_concept = relationship(
        "ScientificConceptDB",
        foreign_keys=[target_concept_id],
        backref="relationships_as_target" # Nombre para la colección en ScientificConceptDB
    )

    def __repr__(self):
        return f"<DirectedRelationshipDB(id='{self.id}', type='{self.type}', source='{self.source_concept_id}', target='{self.target_concept_id}')>"


# --- Modelo ORM para AnalysisData ---
from sqlalchemy.orm import Mapped, mapped_column # Asegurar mapped_column y Mapped
# uuid_pkg, DateTime, func, JSONB, String, Base ya están importados y definidos.
from typing import Dict, Any # Para tipado de JSONB

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
