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
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from aletheia_common.auth.jwt_handler import UserAuth as CommonUserAuth
from aletheia_common.auth.jwt_handler import (
    get_current_active_user_optional,
    require_roles,
)

from ...infrastructure.database import get_db_session
from ...infrastructure.models import (
    ConjectureStatusEnum,
    DerivedConjectureDB,
    HitDB,
    ResearcherDB,
)
from .. import schemas as main_schemas

router = APIRouter(
    prefix="/conjectures",
    tags=["Conjectures"],
)

logger = logging.getLogger(__name__)


@router.post(
    "",
    response_model=main_schemas.ConjectureResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_derived_conjecture(
    conjecture_in: main_schemas.ConjectureCreate,
    db: Session = Depends(get_db_session),
    current_user: CommonUserAuth = Depends(require_roles({"researcher"})),
):
    researcher = (
        db.query(ResearcherDB)
        .filter(ResearcherDB.username == current_user.username)
        .first()
    )
    if not researcher:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authenticated researcher could not be retrieved from database.",
        )

    db_conjecture = DerivedConjectureDB(
        title=conjecture_in.title,
        description=conjecture_in.description,
        proposer_id=researcher.id,
        status=ConjectureStatusEnum.PROPOSED,
    )

    if conjecture_in.supporting_hit_ids:
        hits = (
            db.query(HitDB)
            .filter(HitDB.id.in_(conjecture_in.supporting_hit_ids))
            .all()
        )
        if len(hits) != len(set(conjecture_in.supporting_hit_ids)):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more supporting hit IDs not found.",
            )
        db_conjecture.supporting_hits.extend(hits)

    db.add(db_conjecture)
    db.commit()
    db.refresh(db_conjecture)
    # Eager load proposer for response schema if needed by Pydantic model (using .proposer)
    # db.refresh(db_conjecture.proposer)
    # The model_validate should handle relationships based on schema definition
    # and @computed_field for supporting_hits_count
    response_data = main_schemas.ConjectureResponse.model_validate(
        db_conjecture
    )
    return response_data


@router.get("", response_model=List[main_schemas.ConjectureResponse])
async def list_derived_conjectures(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_session),
    current_user: Optional[CommonUserAuth] = Depends(
        get_current_active_user_optional  # Use the correctly imported name
    ),
):
    # For list views, eager loading supporting_hits might be important to avoid N+1 if @computed_field accesses it.
    # from sqlalchemy.orm import joinedload
    # conjectures_db = db.query(DerivedConjectureDB).options(joinedload(DerivedConjectureDB.supporting_hits)).order_by(DerivedConjectureDB.created_at.desc()).offset(skip).limit(limit).all()
    # However, if only the count is needed and the Pydantic model can get it efficiently (e.g. if the relationship is already loaded or count is a separate column),
    # then joinedload might not be necessary or could even be less performant if hits are numerous and not all data is needed.
    # For now, keeping it simple. If N+1 becomes an issue, optimize with eager loading.
    conjectures_db = (
        db.query(DerivedConjectureDB)
        .order_by(DerivedConjectureDB.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Pydantic will automatically call the @computed_field when serializing each item.
    return [
        main_schemas.ConjectureResponse.model_validate(conj)
        for conj in conjectures_db
    ]


@router.get("/{conjecture_id}", response_model=main_schemas.ConjectureResponse)
async def get_derived_conjecture(
    conjecture_id: int,
    db: Session = Depends(get_db_session),
    current_user: Optional[CommonUserAuth] = Depends(
        get_current_active_user_optional  # Use the correctly imported name
    ),
):
    # For a single object, lazy loading of `supporting_hits` by the @computed_field is generally fine.
    db_conjecture = (
        db.query(DerivedConjectureDB)
        .filter(DerivedConjectureDB.id == conjecture_id)
        .first()
    )
    if db_conjecture is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conjecture not found",
        )

    response_data = main_schemas.ConjectureResponse.model_validate(
        db_conjecture
    )
    return response_data
