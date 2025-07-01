import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Set # Added Set

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
OAUTH2_SCHEME_TOKEN_URL = os.getenv("OAUTH2_SCHEME_TOKEN_URL", "/api/v1/token") # Default to a common path
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
# but the actual user lookup function (`get_user_from_db`) would be implemented by the main application
# or a user management service, and potentially injected or configured.

# Mock user database for demonstration within this common library (NOT FOR PRODUCTION USE as is)
# In a real scenario, this would be a proper database interaction.
MOCK_COMMON_USERS_DB: Dict[str, UserInDB] = {
    "common_user": UserInDB(username="common_user", email="common@example.com", roles=["viewer"], hashed_password="$2b$12$EixZaYVK1xLG.xX1xR2sAeVF3g5MSd20i8t9o.LwLKmAAzLswpD6q"), # pw: testpassword
    "common_analyst": UserInDB(username="common_analyst", email="analyst@example.com", roles=["analyst", "viewer"], hashed_password="$2b$12$EixZaYVK1xLG.xX1xR2sAeVF3g5MSd20i8t9o.LwLKmAAzLswpD6q"),
    "common_admin": UserInDB(username="common_admin", email="admin@example.com", roles=["admin", "analyst", "viewer"], disabled=False, hashed_password="$2b$12$EixZaYVK1xLG.xX1xR2sAeVF3g5MSd20i8t9o.LwLKmAAzLswpD6q")
}

async def get_user_from_db_mock(username: str) -> Optional[UserInDB]:
    """Mock function to retrieve a user from the mock DB."""
    if username in MOCK_COMMON_USERS_DB:
        return MOCK_COMMON_USERS_DB[username]
    return None

async def get_current_active_user(
    token: str = Depends(oauth2_scheme),
    # user_retriever: Callable[[str], Awaitable[Optional[UserInDB]]] = get_user_from_db_mock # Injectable user retriever
) -> UserAuth: # Returns UserAuth, a subset of UserInDB for security context
    """
    Decodes JWT token, validates it, and retrieves the active user.
    This is a dependency function for FastAPI endpoints.

    Args:
        token: The JWT token from the Authorization header.
        user_retriever: An async callable that takes a username and returns UserInDB or None.
                        This allows different parts of Aletheia to use their own user sources
                        while reusing the JWT decoding logic. (Currently using mock)

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

        # 'scopes' in TokenData corresponds to 'roles' in UserAuth/UserInDB
        # The token might store roles directly or scopes that map to roles.
        # Assuming roles are directly in the token for simplicity here.
        roles_from_token: List[str] = payload.get("roles", [])

        token_data = TokenData(username=username, scopes=roles_from_token) # scopes can be roles
    except JWTError as e:
        logger.warning(f"JWTError decoding token: {e}")
        raise credentials_exception

    # user_db_record = await user_retriever(token_data.username) # Using injected retriever
    user_db_record = await get_user_from_db_mock(token_data.username) # Using mock for now

    if user_db_record is None:
        logger.warning(f"User '{token_data.username}' from token not found in DB.")
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
