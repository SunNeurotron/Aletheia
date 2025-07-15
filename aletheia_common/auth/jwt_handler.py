# Copyright 2025 Alant
#
# Licensed under the Aletheia Unificada Ethical Public License (AUEPL);
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

"""
Common JWT (JSON Web Token) authentication and authorization utilities for Aletheia services.

This module provides:
- Configuration for JWT settings (secret key, algorithm, token expiry).
- Pydantic models for token data and user representations.
- Functions to create JWT access tokens.
- FastAPI dependencies for:
    - Retrieving the current authenticated user from a token.
    - Requiring specific roles for accessing endpoints.
- A pluggable mechanism for applications to provide their own user retrieval logic.

Key components:
- `oauth2_scheme`, `oauth2_scheme_optional`: FastAPI security schemes.
- `create_access_token()`: Generates new JWTs.
- `get_current_active_user()`: Dependency to get the authenticated user.
- `get_current_active_user_optional()`: Dependency for optional authentication.
- `require_roles()`: Dependency factory for role-based access control.
- `get_user_retriever_dependency_placeholder()`: Placeholder to be overridden by
  the main application with its actual user lookup function.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import (  # Added Callable, Awaitable
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Set,
)

from fastapi import Depends, HTTPException, status  # For exceptions and Depends
from fastapi.security import OAuth2PasswordBearer  # For dependency
from jose import JWTError, jwt
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# --- Configuration ---
# Use more generic environment variable names that can be shared across services
GLOBAL_JWT_SECRET_KEY_ENV_VAR = "GLOBAL_JWT_SECRET_KEY"
"""Environment variable name for the global JWT secret key."""

GLOBAL_JWT_ALGORITHM_ENV_VAR = "GLOBAL_JWT_ALGORITHM"
"""Environment variable name for the global JWT algorithm."""

ACCESS_TOKEN_EXPIRE_MINUTES_ENV_VAR = "ACCESS_TOKEN_EXPIRE_MINUTES"
"""Environment variable name for the access token expiry time in minutes."""


JWT_SECRET_KEY: str = os.getenv(
    GLOBAL_JWT_SECRET_KEY_ENV_VAR,
    "a-very-secure-default-secret-key-please-change-in-production-common",
)
"""Secret key used to sign and verify JWTs. Loaded from `GLOBAL_JWT_SECRET_KEY_ENV_VAR`."""

JWT_ALGORITHM: str = os.getenv(GLOBAL_JWT_ALGORITHM_ENV_VAR, "HS256")
"""Algorithm used for JWT signing and verification. Loaded from `GLOBAL_JWT_ALGORITHM_ENV_VAR`."""

JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
    os.getenv(ACCESS_TOKEN_EXPIRE_MINUTES_ENV_VAR, "30")
)
"""Default expiration time for access tokens in minutes. Loaded from `ACCESS_TOKEN_EXPIRE_MINUTES_ENV_VAR`."""

OAUTH2_SCHEME_TOKEN_URL: str = os.getenv("OAUTH2_SCHEME_TOKEN_URL", "/token")
"""Token URL for the OAuth2PasswordBearer scheme. This should point to the API's token endpoint.
Loaded from `OAUTH2_SCHEME_TOKEN_URL` environment variable, defaulting to `/token`.
"""

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=OAUTH2_SCHEME_TOKEN_URL)
"""FastAPI OAuth2PasswordBearer security scheme for required authentication.
Uses `OAUTH2_SCHEME_TOKEN_URL` for the token endpoint.
"""

# --- Pydantic Models for Authentication Data ---
# These models can be shared across modules.
class TokenData(BaseModel):
    """
    Pydantic model representing the data encoded within a JWT token.
    Typically includes username and scopes (roles/permissions).
    """
    username: Optional[str] = None
    scopes: List[str] = []


class UserInDB(BaseModel):
    """
    Pydantic model representing a user object as stored in or retrieved from the database.
    Includes sensitive information like hashed_password and status fields like 'disabled'.
    """
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    hashed_password: Optional[str] = None
    roles: List[str] = []
    disabled: bool = False


class UserAuth(BaseModel):
    """
    Pydantic model representing an authenticated user's identity.
    This model is typically what `get_current_active_user` returns and contains
    non-sensitive information safe to use in the application context after authentication.
    """
    username: str
    roles: List[str] = []
    email: Optional[str] = None
    full_name: Optional[str] = None


# --- JWT Creation ---
def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Creates a new JWT access token.

    :param data: Dictionary containing the claims to include in the token
                 (e.g., 'sub' for username, 'roles', 'email', 'full_name').
    :type data: Dict[str, Any]
    :param expires_delta: Optional timedelta object for token expiry.
                          If None, defaults to `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`.
    :type expires_delta: Optional[timedelta]
    :return: The encoded JWT string.
    :rtype: str
    :raises Exception: Propagates any exception during JWT encoding.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})

    try:
        encoded_jwt = jwt.encode(
            to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error encoding JWT: {e}", exc_info=True)
        raise  # Or handle more gracefully depending on policy


# --- JWT Verification and User Retrieval (Example) ---
# This part typically involves a user database lookup.
# For `aletheia_common`, we provide the decoding and a structure for user retrieval,
# but the actual user lookup function would be implemented by the main application
# or a user management service, and injected as a dependency.


# Placeholder dependency for the user retriever function.
# The consuming application (e.g., Aletheia_v3) MUST override this dependency.
async def get_user_retriever_dependency_placeholder() -> (
    Callable[[str], Awaitable[Optional[UserInDB]]]
):
    """
    Placeholder for the actual user retriever dependency.
    This function should be overridden in the main application (e.g., Aletheia_v3)
    to provide a concrete implementation of a user retriever function.
    The user retriever function itself should be an async callable that takes a username (str)
    and returns an Awaitable[Optional[UserInDB]].
    """
    logger.critical(
        "FATAL: `get_user_retriever_dependency_placeholder` was called. "
        "This means the application did not override this dependency to provide "
        "a real user retriever function. Authentication will fail."
    )

    # Default behavior: construct UserInDB from token payload if no DB lookup is performed.
    # This allows services that only validate tokens (like aletheia_stats) to function
    # without needing a DB connection to the identity provider (Aletheia_v3).
    # The 'hashed_password' will be None, and 'disabled' will be False by default.
    # Roles will be taken directly from the token if present.
    async def _default_user_retriever_from_token_payload(
        username_from_payload: str, roles_from_payload: List[str]
    ) -> Optional[UserInDB]:
        logger.debug(
            f"Using default user retriever: creating UserInDB for '{username_from_payload}' from token payload only."
        )
        return UserInDB(
            username=username_from_payload,
            roles=roles_from_payload,
            disabled=False,  # Cannot verify 'disabled' status without DB lookup; assume active.
            hashed_password=None,  # Not relevant for token-only validation
        )

    # This placeholder now needs to provide the roles from the token to the default retriever
    # However, the signature of user_retriever_func is Callable[[str], Awaitable[Optional[UserInDB]]]
    # It only takes username. This means the default retriever logic needs to be inside get_current_active_user.

    # Let's adjust: get_user_retriever_dependency_placeholder will provide a "mode" or a specific retriever.
    # Simpler: make user_retriever_func truly optional in get_current_active_user.
    # The placeholder will still be overridden by apps needing DB lookup.
    # If not overridden, get_current_active_user will handle it.
    # This requires get_current_active_user to change its signature slightly or how it uses the placeholder.

    # New strategy: The placeholder is just a signal. If it's NOT overridden,
    # get_current_active_user will know to use token-only data.
    # This is simpler than trying to make the placeholder return a complex function.
    pass  # Placeholder remains, but its non-override will be key.


async def get_current_active_user(
    token: str = Depends(oauth2_scheme),
    user_retriever_provider: Optional[
        Callable[[str], Awaitable[Optional[UserInDB]]]
    ] = Depends(get_user_retriever_dependency_placeholder),
) -> UserAuth:
    """
    Decodes JWT token, validates it.
    If user_retriever_provider is the placeholder (i.e., not overridden by an app like Aletheia_v3),
    it constructs UserAuth from token payload only.
    Otherwise, it uses the provided retriever to fetch user details from the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            logger.warning("Token payload missing 'sub' (username).")
            raise credentials_exception

        roles_from_token: List[str] = payload.get("roles", [])
        # token_data = TokenData(username=username, scopes=roles_from_token) # Not strictly needed here anymore

    except JWTError as e:
        logger.warning(f"JWTError decoding token: {e}")
        raise credentials_exception

    # Check if the dependency was overridden.
    # If user_retriever_provider is still the placeholder function, it means no DB lookup was configured.
    # This is a bit of a hacky way to check. A more robust way might involve a sentinel value or specific type.
    is_placeholder_active = (
        user_retriever_provider
        is get_user_retriever_dependency_placeholder.__wrapped__
    )  # Access the original function if placeholder is a Depends wrapper

    # Extract additional fields from token if present
    email_from_token: Optional[str] = payload.get("email")
    full_name_from_token: Optional[str] = payload.get("full_name")

    if (
        is_placeholder_active or user_retriever_provider is None
    ):  # If not overridden or explicitly None
        logger.debug(
            f"No DB user retriever provided (placeholder active or None). Using token payload for user '{username}'."
        )
        # Cannot check 'disabled' status without DB. Assume active.
        # Roles, email, full_name are taken directly from token.
        return UserAuth(
            username=username,
            roles=roles_from_token,
            email=email_from_token,
            full_name=full_name_from_token,
        )
    else:
        # A real user_retriever_func was provided (e.g., by Aletheia_v3)
        if not callable(user_retriever_provider):
            logger.error(
                "Provided user retriever is not callable. Check DI setup."
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Auth system misconfig.",
            )

        user_db_record = await user_retriever_provider(
            username
        )  # This returns UserInDB

        if user_db_record is None:
            logger.warning(
                f"User '{username}' (from token sub) not found by provided user_retriever."
            )
            raise credentials_exception
        if (
            user_db_record.disabled
        ):  # This 'disabled' is from the UserInDB model after DB lookup
            logger.warning(f"User '{username}' is disabled (checked from DB).")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user.",
            )

        # Populate UserAuth. If DB provides these, they are more authoritative.
        # If token had them and DB didn't, token's could be used as fallback or primary.
        # Current UserInDB from Aletheia_v3's get_researcher_for_auth provides email and full_name.
        return UserAuth(
            username=user_db_record.username,
            roles=user_db_record.roles,  # Roles from DB are preferred if lookup occurs
            email=user_db_record.email,  # Email from DB record
            full_name=user_db_record.full_name,  # Full name from DB record
        )


# --- Role/Scope Based Authorization Dependency ---
def require_roles(required_roles: Set[str]):
    """
    FastAPI dependency that checks if the current user has ALL the required roles.
    """

    async def role_checker(
        current_user: UserAuth = Depends(get_current_active_user),
    ) -> UserAuth:
        user_roles = set(current_user.roles)
        if not required_roles.issubset(user_roles):
            logger.warning(
                f"Authorization failed for user '{current_user.username}'. "
                f"Required roles: {required_roles}, User roles: {user_roles}."
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. User lacks one or more required roles: {', '.join(required_roles - user_roles)}.",
            )
        return current_user

    return role_checker


def require_any_role(any_of_roles: Set[str]):
    """
    FastAPI dependency that checks if the current user has AT LEAST ONE of the specified roles.
    """

    async def role_checker(
        current_user: UserAuth = Depends(get_current_active_user),
    ) -> UserAuth:
        user_roles = set(current_user.roles)
        if not any(role in user_roles for role in any_of_roles):
            logger.warning(
                f"Authorization failed for user '{current_user.username}'. "
                f"Required at least one of: {any_of_roles}, User roles: {user_roles}."
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. User does not have any of the required roles: {', '.join(any_of_roles)}.",
            )
        return current_user

    return role_checker  # Return the inner function


# Need an optional OAuth2 scheme that doesn't raise an error if token is missing
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl=OAUTH2_SCHEME_TOKEN_URL, auto_error=False
)
"""FastAPI OAuth2PasswordBearer security scheme for optional authentication.
If a token is provided, it's validated; if not, proceeds as anonymous.
`auto_error=False` prevents FastAPI from automatically raising an error if the token is missing.
"""


async def get_current_active_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    user_retriever_func: Callable[
        [str], Awaitable[Optional[UserInDB]]
    ] = Depends(get_user_retriever_dependency_placeholder),
) -> Optional[UserAuth]:
    """
    Attempts to get the current active user from a JWT token, but returns None
    if the token is missing, invalid, or the user is not active.

    This dependency is useful for endpoints that are publicly accessible but can
    provide enhanced functionality or data if a valid authenticated user is present.

    It uses the same pluggable user retrieval mechanism as `get_current_active_user`.
    If the `user_retriever_func` is not overridden by the application, this function
    will attempt to construct `UserAuth` from token claims only (username, roles, email, full_name)
    and will not be able to verify the 'disabled' status from a database.

    :param token: Optional token string provided by `oauth2_scheme_optional`.
    :type token: Optional[str]
    :param user_retriever_func: The (potentially overridden) function to retrieve
                                user details from the database.
    :type user_retriever_func: Callable[[str], Awaitable[Optional[UserInDB]]]
    :return: A `UserAuth` object if authentication is successful and user is active,
             otherwise `None`.
    :rtype: Optional[UserAuth]
    """
    if token is None:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            logger.warning(
                "Token payload missing 'sub' (username) in optional auth."
            )
            return None

        roles_from_token: List[str] = payload.get("roles", [])
        # Not using TokenData here explicitly as we handle missing username by returning None

        if not callable(user_retriever_func):
            logger.error(
                "User retriever function is not callable in optional auth. Check DI setup."
            )
            return None  # System misconfiguration, treat as unauthenticated

        user_db_record = await user_retriever_func(username)

        if user_db_record is None:
            logger.info(
                f"User '{username}' (from token sub) not found by user_retriever_func in optional auth."
            )
            return None

        if user_db_record.disabled:
            logger.info(f"User '{username}' is disabled in optional auth.")
            return None

        return UserAuth(
            username=user_db_record.username, roles=user_db_record.roles
        )
    except JWTError as e:
        logger.info(
            f"JWTError decoding token in optional auth: {e}"
        )  # Info level, not a warning for optional
        return None
    except (
        Exception
    ) as e:  # Catch any other unexpected error during optional auth
        logger.error(
            f"Unexpected error in get_current_active_user_optional: {e}",
            exc_info=True,
        )
        return None


# Example usage (typically in an API endpoint):
# from fastapi import APIRouter
# router = APIRouter()
# @router.get("/users/me", response_model=UserAuth)
# async def read_users_me(current_user: UserAuth = Depends(get_current_active_user)):
#     return current_user
#
# @router.get("/admin/dashboard")
# async def admin_dashboard(_: UserAuth = Depends(require_roles({"admin"}))):
#     return {"message": "Welcome to the Admin Dashboard!"}

# Note: Password hashing and user management (registration, password reset, etc.)
# are not part of this JWT handler but would be part of a complete authentication system,
# likely interacting with the `UserInDB` model and a password hashing library like passlib.
# The `/token` endpoint itself would also be part of that system, using these JWT functions.
