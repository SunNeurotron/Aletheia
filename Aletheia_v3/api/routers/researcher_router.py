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

import logging
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from aletheia_common.auth.jwt_handler import UserAuth as CommonUserAuth
from aletheia_common.auth.jwt_handler import (
    get_current_active_user as common_get_current_active_user,
)
from aletheia_common.auth.jwt_handler import require_roles

from ...infrastructure.database import get_db_session
from ...infrastructure.models import ResearcherDB
from .. import auth as main_auth  # For get_password_hash
from .. import schemas as main_schemas

router = APIRouter(
    prefix="/researchers",  # Adding prefix here as all routes start with /researchers
    tags=["Researchers"],
)

logger = logging.getLogger(__name__)


@router.post(
    "",
    response_model=main_schemas.ResearcherResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_researcher(
    researcher_in: main_schemas.ResearcherCreate,
    db: Session = Depends(get_db_session),
    current_admin: CommonUserAuth = Depends(require_roles({"admin"})),
):
    existing_researcher_username = (
        db.query(ResearcherDB)
        .filter(ResearcherDB.username == researcher_in.username)
        .first()
    )
    if existing_researcher_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    existing_researcher_email = (
        db.query(ResearcherDB)
        .filter(ResearcherDB.email == researcher_in.email)
        .first()
    )
    if existing_researcher_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    hashed_password = main_auth.get_password_hash(researcher_in.password)
    db_researcher = ResearcherDB(
        username=researcher_in.username,
        full_name=researcher_in.full_name,
        email=researcher_in.email,
        orcid=researcher_in.orcid,
        hashed_password=hashed_password,
        # is_admin default is False in model
    )
    db.add(db_researcher)
    db.commit()
    db.refresh(db_researcher)
    return db_researcher


@router.get("", response_model=List[main_schemas.ResearcherResponse])
async def list_researchers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_session),
    current_user: CommonUserAuth = Depends(require_roles({"researcher"})),
):
    researchers = db.query(ResearcherDB).offset(skip).limit(limit).all()
    return researchers


@router.get("/{researcher_id}", response_model=main_schemas.ResearcherResponse)
async def get_researcher(
    researcher_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user: CommonUserAuth = Depends(require_roles({"researcher"})),
):
    db_researcher = (
        db.query(ResearcherDB).filter(ResearcherDB.id == researcher_id).first()
    )
    if db_researcher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Researcher not found",
        )
    return db_researcher


@router.put("/{researcher_id}", response_model=main_schemas.ResearcherResponse)
async def update_researcher_info(
    researcher_id: uuid.UUID,
    researcher_update: main_schemas.ResearcherUpdate,
    db: Session = Depends(get_db_session),
    current_user: CommonUserAuth = Depends(
        common_get_current_active_user
    ),  # Using common_get_current_active_user for self-update logic
):
    db_researcher = (
        db.query(ResearcherDB).filter(ResearcherDB.id == researcher_id).first()
    )
    if db_researcher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Researcher not found",
        )

    is_self = db_researcher.username == current_user.username
    is_admin_user = "admin" in current_user.roles

    if not (is_self or is_admin_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this researcher's information.",
        )

    update_data = researcher_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_researcher, key, value)

    # updated_at will be handled by SQLAlchemy model if configured with onupdate,
    # otherwise, if manual update is needed:
    # db_researcher.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_researcher)
    return db_researcher
