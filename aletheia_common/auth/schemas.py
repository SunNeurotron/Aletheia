# aletheia_common/auth/schemas.py
import uuid as uuid_pkg
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field # Add EmailStr if/when email validation is desired

# --- Token Schemas ---
class Token(BaseModel):
    """Schema for the JWT access token."""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """
    Pydantic model representing the data encoded within a JWT token.
    Typically includes username and scopes (roles/permissions).
    """
    username: Optional[str] = None
    scopes: List[str] = [] # Kept from jwt_handler.py version, Aletheia_v3.api.schemas had only username

# --- User Schemas ---
# These are primarily for API interaction (request/response).

class UserBase(BaseModel): # From Aletheia_v3/api/schemas.py
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[str] = None
    full_name: Optional[str] = None

class UserCreate(UserBase): # From Aletheia_v3/api/schemas.py
    password: str = Field(
        ..., min_length=8, description="User's password (will be hashed)."
    )

class UserResponse(UserBase): # From Aletheia_v3/api/schemas.py
    """Schema for returning user information (without password)."""
    # Note: The 'disabled' field was in Aletheia_v3's UserResponse.
    # It's also in UserInDB. For a public UserResponse, it might be relevant.
    # Keeping it consistent with UserInDB for now.
    disabled: bool = False

    class Config:
        orm_mode = True

# --- Researcher Schemas (specific to Aletheia_v3's concept of Researcher) ---
# These are kept separate from generic User schemas if Researcher has more specific fields

class ResearcherBase(BaseModel): # From Aletheia_v3/api/schemas.py
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    email: str = Field(..., max_length=255)
    orcid: Optional[str] = Field(
        None, max_length=50, description="ORCID iD, e.g., 0000-0000-0000-0000"
    )

class ResearcherCreate(ResearcherBase): # From Aletheia_v3/api/schemas.py
    password: str = Field(
        ...,
        min_length=8,
        description="Researcher's password (will be hashed upon creation)",
    )

class ResearcherUpdate(BaseModel): # From Aletheia_v3/api/schemas.py
    full_name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    orcid: Optional[str] = Field(None, max_length=50)

class ResearcherResponse(ResearcherBase): # From Aletheia_v3/api/schemas.py
    id: uuid_pkg.UUID
    created_at: datetime
    updated_at: datetime
    disabled: bool = False # Added to be consistent with UserInDB and common UserResponse

    class Config:
        orm_mode = True

# --- Internal Authentication User Models ---
# These were originally in aletheia_common.auth.jwt_handler

class UserInDB(BaseModel):
    """
    Pydantic model representing a user object as stored in or retrieved from the database.
    Includes sensitive information like hashed_password and status fields like 'disabled'.
    This is used internally by the authentication logic.
    """
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    hashed_password: Optional[str] = None # Should be str if present, Optional if user might not have a password (e.g. external OAuth)
    roles: List[str] = Field(default_factory=list)
    disabled: bool = False

class UserAuth(BaseModel):
    """
    Pydantic model representing an authenticated user's identity.
    This model is typically what `get_current_active_user` returns and contains
    non-sensitive information safe to use in the application context after authentication.
    """
    username: str
    roles: List[str] = Field(default_factory=list)
    email: Optional[str] = None
    full_name: Optional[str] = None
    # No 'disabled' field here, as get_current_active_user should not return disabled users.
    # No 'hashed_password'.
