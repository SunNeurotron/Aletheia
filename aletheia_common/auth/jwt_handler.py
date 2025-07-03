import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Set, Callable, Awaitable # Added Callable, Awaitable

from fastapi import Depends, HTTPException, status # For exceptions and Depends
from fastapi.security import OAuth2PasswordBearer # For dependency
from jose import JWTError, jwt
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# --- Configuration ---
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "a-very-secure-default-secret-key-please-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")) # Consistent name

# OAuth2PasswordBearer needs a tokenUrl. This should point to the actual token endpoint in the main API.
# This might need to be configurable if different modules have different token URLs or if there's one central one.
# For now, assume a central token URL. This will be used by FastAPI's Depends(oauth2_scheme).
# Defaulting to "/token" as it's a common pattern for non-versioned auth endpoints.
OAUTH2_SCHEME_TOKEN_URL = os.getenv("OAUTH2_SCHEME_TOKEN_URL", "/token")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=OAUTH2_SCHEME_TOKEN_URL)

# --- Pydantic Models for Authentication Data ---
# These models can be shared across modules.
class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: List[str] = [] # Using 'scopes' as it's common in OAuth2, can represent roles or permissions

class UserInDB(BaseModel): # More complete User model, potentially from DB
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    hashed_password: Optional[str] = None # Store hashed passwords, not plaintext
    roles: List[str] = []
    disabled: bool = False

class UserAuth(BaseModel): # User model for authentication context (e.g. in current_user)
    username: str
    roles: List[str] = []
    # email: Optional[str] = None # Add other fields if needed by application logic after auth
    # full_name: Optional[str] = None


# --- JWT Creation ---
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a new JWT access token.

    Args:
        data: Dictionary containing the claims to include in the token (e.g., 'sub' for username, 'roles').
        expires_delta: Optional timedelta object for token expiry. Defaults to JWT_ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        The encoded JWT string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    try:
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error encoding JWT: {e}", exc_info=True)
        raise # Or handle more gracefully depending on policy


# --- JWT Verification and User Retrieval (Example) ---
# This part typically involves a user database lookup.
# For `aletheia_common`, we provide the decoding and a structure for user retrieval,
# but the actual user lookup function would be implemented by the main application
# or a user management service, and injected as a dependency.

# Placeholder dependency for the user retriever function.
# The consuming application (e.g., Aletheia_v3) MUST override this dependency.
async def get_user_retriever_dependency_placeholder() -> Callable[[str], Awaitable[Optional[UserInDB]]]:
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
    raise NotImplementedError(
        "User retriever function not implemented or provided by the application. "
        "Override `get_user_retriever_dependency_placeholder` using app.dependency_overrides "
        "or by providing a direct dependency to `get_current_active_user`."
    )


async def get_current_active_user(
    token: str = Depends(oauth2_scheme),
    # The user_retriever_func is now a dependency that must be provided by the app
    # It's a callable that itself returns an awaitable (the actual user lookup function).
    user_retriever_func: Callable[[str], Awaitable[Optional[UserInDB]]] = Depends(get_user_retriever_dependency_placeholder)
) -> UserAuth:
    """
    Decodes JWT token, validates it, and retrieves the active user using an injected user retriever.
    This is a dependency function for FastAPI endpoints.

    Args:
        token: The JWT token from the Authorization header.
        user_retriever_func: An async callable (obtained via FastAPI's Depends)
                             that takes a username (str) and returns an Awaitable[Optional[UserInDB]].
                             This function is responsible for fetching user details from the database.
    Returns:
        A UserAuth object representing the authenticated user.
    Raises:
        HTTPException (401): If authentication fails (invalid token, user not found, or disabled).
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

        roles_from_token: List[str] = payload.get("roles", []) # Roles can also be in token
        token_data = TokenData(username=username, scopes=roles_from_token)

    except JWTError as e:
        logger.warning(f"JWTError decoding token: {e}")
        raise credentials_exception

    if not callable(user_retriever_func):
        # This should ideally not happen if FastAPI's dependency injection works as expected
        # and get_user_retriever_dependency_placeholder is overridden correctly.
        logger.error("User retriever function is not callable. Check dependency injection setup.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Authentication system misconfiguration.")

    user_db_record = await user_retriever_func(token_data.username)

    if user_db_record is None:
        logger.warning(f"User '{token_data.username}' (from token sub) not found by user_retriever_func.")
        raise credentials_exception
    if user_db_record.disabled:
        logger.warning(f"User '{token_data.username}' is disabled.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user.")

    # Check if roles in token match roles in DB (optional, depends on trust model for token)
    # For now, trust roles from DB after validating username.
    # Or, could assert token_data.scopes == user_db_record.roles

    return UserAuth(username=user_db_record.username, roles=user_db_record.roles)


# --- Role/Scope Based Authorization Dependency ---
def require_roles(required_roles: Set[str]):
    """
    FastAPI dependency that checks if the current user has ALL the required roles.
    """
    async def role_checker(current_user: UserAuth = Depends(get_current_active_user)) -> UserAuth:
        user_roles = set(current_user.roles)
        if not required_roles.issubset(user_roles):
            logger.warning(
                f"Authorization failed for user '{current_user.username}'. "
                f"Required roles: {required_roles}, User roles: {user_roles}."
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. User lacks one or more required roles: {', '.join(required_roles - user_roles)}."
            )
        return current_user
    return role_checker

def require_any_role(any_of_roles: Set[str]):
    """
    FastAPI dependency that checks if the current user has AT LEAST ONE of the specified roles.
    """
    async def role_checker(current_user: UserAuth = Depends(get_current_active_user)) -> UserAuth:
        user_roles = set(current_user.roles)
        if not any(role in user_roles for role in any_of_roles):
            logger.warning(
                f"Authorization failed for user '{current_user.username}'. "
                f"Required at least one of: {any_of_roles}, User roles: {user_roles}."
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. User does not have any of the required roles: {', '.join(any_of_roles)}."
            )
        return current_user
    return role_checker # Return the inner function


# Need an optional OAuth2 scheme that doesn't raise an error if token is missing
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl=OAUTH2_SCHEME_TOKEN_URL, auto_error=False)

async def get_current_active_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    user_retriever_func: Callable[[str], Awaitable[Optional[UserInDB]]] = Depends(get_user_retriever_dependency_placeholder)
) -> Optional[UserAuth]:
    """
    Attempts to get the current active user from a JWT token, but returns None if token is missing or invalid.
    This is useful for endpoints that are public but can have enhanced behavior for authenticated users.
    """
    if token is None:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            logger.warning("Token payload missing 'sub' (username) in optional auth.")
            return None

        roles_from_token: List[str] = payload.get("roles", [])
        # Not using TokenData here explicitly as we handle missing username by returning None

        if not callable(user_retriever_func):
            logger.error("User retriever function is not callable in optional auth. Check DI setup.")
            return None # System misconfiguration, treat as unauthenticated

        user_db_record = await user_retriever_func(username)

        if user_db_record is None:
            logger.info(f"User '{username}' (from token sub) not found by user_retriever_func in optional auth.")
            return None

        if user_db_record.disabled:
            logger.info(f"User '{username}' is disabled in optional auth.")
            return None

        return UserAuth(username=user_db_record.username, roles=user_db_record.roles)
    except JWTError as e:
        logger.info(f"JWTError decoding token in optional auth: {e}") # Info level, not a warning for optional
        return None
    except Exception as e: # Catch any other unexpected error during optional auth
        logger.error(f"Unexpected error in get_current_active_user_optional: {e}", exc_info=True)
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
