import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

# No direct model usage here beyond what auth module handles, but good to have for context
# from ...infrastructure.models import ResearcherDB
from aletheia_common.auth.jwt_handler import UserAuth as CommonUserAuth
from aletheia_common.auth.jwt_handler import (
    get_current_active_user as common_get_current_active_user,
)

from ...infrastructure.database import get_db_session
from .. import auth as main_auth
from .. import schemas as main_schemas

router = APIRouter(
    tags=[
        "Authentication",
        "Users",
    ],  # Combined tags as they are user/auth related
)

logger = logging.getLogger(__name__)


@router.post("/token", response_model=main_schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db_session),  # Pass db to authenticate_user
):
    user_in_db = await main_auth.authenticate_user(form_data=form_data, db=db)
    # user_in_db is of type UserInDB from aletheia_common.auth.jwt_handler
    # which includes username, email, full_name, roles, disabled, hashed_password.

    access_token_expires = timedelta(
        minutes=main_auth.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    # Prepare data for the token, including new fields
    token_data = {
        "sub": user_in_db.username,
        "roles": user_in_db.roles,
        "email": user_in_db.email,
        "full_name": user_in_db.full_name,
        # Do not include 'disabled' or 'hashed_password' in the token directly unless essential for other services
        # and if security implications are understood. 'disabled' status is checked by get_current_active_user.
    }

    access_token = main_auth.create_access_token(
        data=token_data, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=main_schemas.UserResponse)
async def read_users_me(
    current_user: CommonUserAuth = Depends(common_get_current_active_user),
    # No longer need db Session here if all info comes from token via CommonUserAuth
):
    # current_user (CommonUserAuth) should now have email and full_name if populated by get_current_active_user
    # The main_schemas.UserResponse model expects username, email, full_name, disabled.
    # 'disabled' status is not typically stored in the token for /users/me endpoint,
    # as it's an active session. If UserResponse needs to show 'disabled' status,
    # it would still require a DB lookup or for UserAuth to also carry it (less common).
    # For now, assume UserResponse's 'disabled' field can be omitted or defaulted if not in UserAuth.
    # Let's make UserResponse's disabled field optional or fetch it if truly needed.
    # For this step, we'll populate from current_user (CommonUserAuth) which now has email and full_name.

    # Check if UserResponse schema needs to be adjusted for 'disabled' or if it's optional.
    # Assuming main_schemas.UserResponse can handle missing 'disabled' or has a default.
    # The CommonUserAuth model now contains email and full_name.
    # The disabled status is checked during get_current_active_user from DB record, not usually passed in UserAuth.

    return main_schemas.UserResponse(
        username=current_user.username,
        email=current_user.email,  # Now from token via CommonUserAuth
        full_name=current_user.full_name,  # Now from token via CommonUserAuth
        disabled=False,  # Placeholder: disabled status is checked on token validation, not usually returned here.
        # If UserResponse schema requires it, it should be made Optional or fetched.
        # For now, assuming it's not critical for this response or can be defaulted.
    )
