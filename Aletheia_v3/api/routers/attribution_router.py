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

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from aletheia_common.auth.jwt_handler import UserAuth as CommonUserAuth
from aletheia_common.auth.jwt_handler import require_roles

from ...infrastructure.database import get_db_session
from ...infrastructure.models import (
    ContributionTypeEnum,
    DiscoveryAttributionDB,
    HitDB,
    ResearcherDB,
)
from .. import schemas as main_schemas

router = APIRouter(
    prefix="/hits/{hit_id}/attributions",  # Common prefix for these routes
    tags=["Attributions"],
)

logger = logging.getLogger(__name__)


@router.post(
    "",
    response_model=main_schemas.AttributionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_attribution_to_hit(
    hit_id: int,  # Path parameter from prefix
    attribution_in: main_schemas.AttributionCreate,
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

    db_hit = db.query(HitDB).filter(HitDB.id == hit_id).first()
    if not db_hit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Hit not found."
        )

    try:
        contribution_type_enum = ContributionTypeEnum(
            attribution_in.contribution_type
        )
    except (
        ValueError
    ):  # Handles if the string value is not a valid enum member
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid contribution_type. Allowed values are: {[e.value for e in ContributionTypeEnum]}",
        )

    db_attribution = DiscoveryAttributionDB(
        hit_id=db_hit.id,
        researcher_id=researcher.id,
        contribution_type=contribution_type_enum,
        details=attribution_in.details,
    )
    db.add(db_attribution)
    db.commit()
    db.refresh(db_attribution)
    return db_attribution
