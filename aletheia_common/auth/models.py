# aletheia_common/auth/models.py
import uuid as uuid_pkg
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Boolean, DateTime, String, ForeignKey # ForeignKey might not be needed if relationships are removed
from sqlalchemy.orm import Mapped, mapped_column, relationship # relationship might not be needed

from ..db.base import Base # Import shared Base
from ..db.custom_types import UUID # Import custom UUID type
from sqlalchemy.sql import func

class ResearcherDB(Base):
    __tablename__ = "researchers"

    id: Mapped[uuid_pkg.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    orcid: Mapped[Optional[str]] = mapped_column(
        String(50), unique=True, nullable=True, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    disabled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default=sa.false()
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships to Aletheia_v3 models are removed from here.
    # They will be defined in Aletheia_v3 models pointing to this common ResearcherDB.
    # e.g., in Aletheia_v3.infrastructure.models.JobDB:
    # submitter = relationship("aletheia_common.auth.models.ResearcherDB", back_populates="submitted_jobs_placeholder")
    # And ResearcherDB would need a placeholder if back_populates is used, or relationships are one-way from Aletheia_v3.
    # For now, keeping it simple by removing them from the common model.
    # If back_populates are needed, they'd be like:
    # submitted_jobs = relationship("Aletheia_v3.infrastructure.models.JobDB", back_populates="submitter") # This is an anti-pattern for common lib
    # A better way is for JobDB in Aletheia_v3 to define the full relationship.

    def __repr__(self):
        return (
            f"<ResearcherDB(username='{self.username}', email='{self.email}')>"
        )
