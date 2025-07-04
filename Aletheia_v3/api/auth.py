# Aletheia_v3/api/auth.py
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, Optional  # Added Awaitable, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import (  # OAuth2PasswordRequestForm for /token endpoint
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
from jose import (  # Keep these from original Aletheia_v3/api/auth.py; Removed JWTError
    jwt,
)
from passlib.context import CryptContext  # Keep for password hashing

# Import DB session and Researcher model
from sqlalchemy.orm import Session

# Import UserInDB from aletheia_common to be returned by the user_retriever
from aletheia_common.auth.jwt_handler import UserInDB

from ..infrastructure.database import get_db_session  # Renamed to avoid clash
from ..infrastructure.models import ResearcherDB

# Removed: from aletheia_common.auth.jwt_handler import oauth2_scheme as common_oauth2_scheme


# Note: SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES are used by aletheia_common.create_access_token
# We can remove them here if aletheia_common.create_access_token is used directly.
# For now, Aletheia_v3's create_access_token is distinct.


# --- Configuration ---
# Ensure these use the global environment variable names for consistency if they are to be shared.
# These are used by the local create_access_token function in this file.
# If aletheia_common.create_access_token were used, these wouldn't be needed here.
GLOBAL_JWT_SECRET_KEY_ENV_VAR = (
    "GLOBAL_JWT_SECRET_KEY"  # Defined in aletheia_common
)
GLOBAL_JWT_ALGORITHM_ENV_VAR = (
    "GLOBAL_JWT_ALGORITHM"  # Defined in aletheia_common
)
ACCESS_TOKEN_EXPIRE_MINUTES_ENV_VAR = (
    "ACCESS_TOKEN_EXPIRE_MINUTES"  # Defined in aletheia_common
)

SECRET_KEY = os.getenv(
    GLOBAL_JWT_SECRET_KEY_ENV_VAR,
    "a-very-secure-default-secret-key-please-change-in-production-v3",
)
ALGORITHM = os.getenv(GLOBAL_JWT_ALGORITHM_ENV_VAR, "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(ACCESS_TOKEN_EXPIRE_MINUTES_ENV_VAR, "30")
)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token dependency for THIS auth module.
# The tokenUrl should point to the /token endpoint defined in this Aletheia_v3 app.
# `common_oauth2_scheme` from `aletheia_common` might have a different `tokenUrl` if not configured.
# It's important that the `tokenUrl` used by `OAuth2PasswordBearer` matches the actual token endpoint.
# If Aletheia_v3's /token is the source of truth, this is correct.
# The `oauth2_scheme` used by `get_current_active_user` in `aletheia_common`
# will also need to point to this same `/token` endpoint. This is usually configured
# by the application setting `OAUTH2_SCHEME_TOKEN_URL` env var that `aletheia_common` reads.
aletheia_v3_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token"
)  # "token" is relative to API root

# --- Utility Functions (Password Hashing, Token Creation) ---
# These are specific to Aletheia_v3's auth flow if it differs from aletheia_common.
# If they are identical, prefer using the ones from aletheia_common.


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)


def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """Creates a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# --- User Model (Pydantic for response) ---
# This is a simplified User model for what get_current_user might return in THIS module.
# aletheia_common.UserAuth is the standard for user context after authentication.
# This User class can be deprecated if UserAuth from common is sufficient.
class User:  # TODO: Review if this class is still needed or if UserAuth from common is enough.
    def __init__(
        self,
        username: str,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        disabled: bool = False,
        roles: Optional[list[str]] = None,
    ):
        self.username = username
        self.full_name = full_name
        self.email = email
        self.disabled = disabled
        self.roles = roles or []


# --- User Retriever Implementation for Aletheia_v3 ---
async def get_researcher_for_auth(
    username: str, db: Session = Depends(get_db_session)
) -> Optional[UserInDB]:
    """
    Retrieves a researcher from the database and maps it to the UserInDB model
    expected by aletheia_common.auth.jwt_handler.
    """
    researcher = (
        db.query(ResearcherDB)
        .filter(ResearcherDB.username == username)
        .first()
    )
    if researcher:
        user_roles = ["researcher"]  # Default role for any researcher
        if researcher.is_admin:
            if (
                "admin" not in user_roles
            ):  # Asegurar que no se duplique si ya estuviera por otra lógica
                user_roles.append("admin")

        # Map the 'disabled' field from ResearcherDB to UserInDB.disabled
        # The ResearcherDB model now has a 'disabled' field.
        is_disabled = researcher.disabled

        return UserInDB(
            username=researcher.username,
            email=researcher.email,
            full_name=researcher.full_name,
            hashed_password=researcher.hashed_password,
            roles=sorted(
                list(set(user_roles))
            ),  # Ordenar y asegurar unicidad de roles
            disabled=is_disabled,
        )
    return None


# This function will be provided to aletheia_common's get_current_active_user
# via app.dependency_overrides in api_server.py
def get_user_retriever() -> Callable[[str], Awaitable[Optional[UserInDB]]]:
    # This wrapper is needed because Depends() in get_current_active_user expects
    # the dependency itself (get_researcher_for_auth) to be injected, not its result.
    # However, get_researcher_for_auth itself needs `db: Session = Depends(get_db_session)`.
    # FastAPI handles nested Depends, so we can return the function directly.
    # The dependency system will resolve get_db_session when get_researcher_for_auth is called.
    return get_researcher_for_auth


# --- Authentication Logic for Token Endpoint (using ResearcherDB) ---


async def authenticate_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db_session),
) -> UserInDB:
    """
    Authenticates a researcher from ResearcherDB.
    Used by the /token endpoint in api_server.py.
    Returns UserInDB which includes hashed_password and roles.
    """
    user_in_db = await get_researcher_for_auth(
        username=form_data.username, db=db
    )
    if not user_in_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user_in_db.hashed_password or not verify_password(
        form_data.password, user_in_db.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user_in_db.disabled:  # UserInDB model from common now has 'disabled'
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return user_in_db  # Return the UserInDB object, as it contains all necessary info including roles


# Example of how to use get_password_hash (e.g., when creating a new user)
if __name__ == "__main__":
    # This would not typically be in auth.py but in a user management script/service
    # new_user_password = "a_strong_password"
    # hashed = get_password_hash(new_user_password)
    # print(f"Hashed password for '{new_user_password}': {hashed}")
    #
    # print(f"Hashed password for 'testpassword': {get_password_hash('testpassword')}")
    # Should be: $2b$12$EixZaYVK1xKIx74SAhN7PueE91.qg2vNn2jXRcOB2kK8sUMS83CUm
    pass
