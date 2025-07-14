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
from datetime import timedelta

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from aletheia_common.auth.jwt_handler import (
    UserAuth,
    create_access_token,
    get_current_active_user,
)
from aletheia_common.auth.schemas import Token, UserResponse
from ..auth import ACCESS_TOKEN_EXPIRE_MINUTES, authenticate_user
from ...infrastructure.database import get_db_session

router = APIRouter(
    tags=["Authentication", "Users"],
)

logger = logging.getLogger(__name__)


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db_session),
) -> Token:
    user_in_db = await authenticate_user(form_data=form_data, db=db)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    token_data = {
        "sub": user_in_db.username,
        "roles": user_in_db.roles,
        "email": user_in_db.email,
        "full_name": user_in_db.full_name,
    }

    access_token = create_access_token(
        data=token_data, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=UserResponse)
async def read_users_me(
    current_user: UserAuth = Depends(get_current_active_user),
) -> UserResponse:
    return UserResponse(
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        disabled=False,
    )
