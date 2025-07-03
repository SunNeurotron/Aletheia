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
# Use more generic environment variable names that can be shared across services
GLOBAL_JWT_SECRET_KEY_ENV_VAR = "GLOBAL_JWT_SECRET_KEY"
GLOBAL_JWT_ALGORITHM_ENV_VAR = "GLOBAL_JWT_ALGORITHM"
ACCESS_TOKEN_EXPIRE_MINUTES_ENV_VAR = "ACCESS_TOKEN_EXPIRE_MINUTES" # Keep this as it might be app-specific

JWT_SECRET_KEY = os.getenv(GLOBAL_JWT_SECRET_KEY_ENV_VAR, "a-very-secure-default-secret-key-please-change-in-production-common")
JWT_ALGORITHM = os.getenv(GLOBAL_JWT_ALGORITHM_ENV_VAR, "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv(ACCESS_TOKEN_EXPIRE_MINUTES_ENV_VAR, "30"))

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
    # Default behavior: construct UserInDB from token payload if no DB lookup is performed.
    # This allows services that only validate tokens (like aletheia_stats) to function
    # without needing a DB connection to the identity provider (Aletheia_v3).
    # The 'hashed_password' will be None, and 'disabled' will be False by default.
    # Roles will be taken directly from the token if present.
    async def _default_user_retriever_from_token_payload(username_from_payload: str, roles_from_payload: List[str]) -> Optional[UserInDB]:
        logger.debug(f"Using default user retriever: creating UserInDB for '{username_from_payload}' from token payload only.")
        return UserInDB(
            username=username_from_payload,
            roles=roles_from_payload,
            disabled=False, # Cannot verify 'disabled' status without DB lookup; assume active.
            hashed_password=None # Not relevant for token-only validation
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
    pass # Placeholder remains, but its non-override will be key.


async def get_current_active_user(
    token: str = Depends(oauth2_scheme),
    user_retriever_provider: Optional[Callable[[str], Awaitable[Optional[UserInDB]]]] = Depends(get_user_retriever_dependency_placeholder)
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
    is_placeholder_active = user_retriever_provider is get_user_retriever_dependency_placeholder.__wrapped__ # Access the original function if placeholder is a Depends wrapper

    if is_placeholder_active or user_retriever_provider is None: # If not overridden or explicitly None
        logger.debug(f"No DB user retriever provided (placeholder active or None). Using token payload for user '{username}'.")
        # Cannot check 'disabled' status without DB. Assume active.
        # Roles are taken directly from token.
        return UserAuth(username=username, roles=roles_from_token)
    else:
        # A real user_retriever_func was provided (e.g., by Aletheia_v3)
        if not callable(user_retriever_provider):
             logger.error("Provided user retriever is not callable. Check DI setup.")
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Auth system misconfig.")

        user_db_record = await user_retriever_provider(username)

        if user_db_record is None:
            logger.warning(f"User '{username}' (from token sub) not found by provided user_retriever.")
            raise credentials_exception
        if user_db_record.disabled:
            logger.warning(f"User '{username}' is disabled (checked from DB).")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user.")

        # Trust roles from DB if available and different from token, or merge, or use token roles.
        # For now, using roles from DB as they are more authoritative if DB lookup occurs.
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
