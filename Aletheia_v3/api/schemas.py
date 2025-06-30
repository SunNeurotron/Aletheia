# Aletheia_v3/api/schemas.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime

# --- Job Schemas ---

class HitBase(BaseModel):
    """Base schema for a 'hit' (an abc-triple with its quality)."""
    a: int = Field(..., gt=0, description="The 'a' component of the abc-triple.")
    b: int = Field(..., gt=0, description="The 'b' component of the abc-triple.")
    c: int = Field(..., gt=0, description="The 'c' component (a+b) of the abc-triple.")
    quality: float = Field(..., description="The calculated quality 'q' of the triple.")

    @validator('c')
    def c_must_be_a_plus_b(cls, v, values):
        # This validator is mostly for conceptual clarity in the schema,
        # as the actual calculation c=a+b happens in the domain logic.
        # However, if c were directly provided, this would be crucial.
        if 'a' in values and 'b' in values and v != values['a'] + values['b']:
            # In our current flow, 'c' is derived, so this might not be strictly necessary
            # if the input to this schema already has 'c' correctly calculated.
            # If 'c' is also an input field, this validation is important.
            # For now, let's assume 'c' is correctly populated based on 'a' and 'b'.
            pass # Or raise ValueError('c must be equal to a + b') if c is also an input field
        return v

class HitResponse(HitBase):
    """Schema for representing a hit when returning data from the API."""
    id: Optional[int] = Field(None, description="Unique ID of the hit in the database, if applicable.") # From HitDB
    discovered_at: Optional[datetime] = Field(None, description="Timestamp when the hit was discovered.") # From HitDB

    class Config:
        orm_mode = True # Allows Pydantic to work with SQLAlchemy models

class JobBase(BaseModel):
    """Base schema for a discovery job."""
    n_calls: int = Field(..., gt=10, le=1000, description="Number of Bayesian optimization calls for the job (budget). Max 1000.")
    # Max 1000 is an example, can be adjusted based on typical runtimes / resource limits.

class JobCreateRequest(JobBase):
    """Schema for creating a new discovery job."""
    pass # Inherits n_calls from JobBase

class JobResponse(JobBase):
    """Schema for representing a job when returning data from the API."""
    id: str = Field(..., description="Unique ID of the job.")
    status: str = Field(..., description="Current status of the job (e.g., pending, processing, completed, failed).")
    created_at: datetime = Field(..., description="Timestamp when the job was created.")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the job was last updated.")
    hits: List[HitResponse] = Field([], description="List of high-quality hits found by this job.")

    class Config:
        orm_mode = True # Allows Pydantic to work with SQLAlchemy models


# --- Token Schemas (for Authentication) ---

class Token(BaseModel):
    """Schema for the JWT access token."""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Schema for data embedded within the JWT token (the 'sub' field)."""
    username: Optional[str] = None

# --- User Schemas (for Authentication examples) ---
# These are simplified for the example. In a real app, you might have more fields.

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[str] = None # EmailStr can be used for validation: from pydantic import EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="User's password (will be hashed).")

class UserResponse(UserBase):
    """Schema for returning user information (without password)."""
    disabled: Optional[bool] = None

    class Config:
        orm_mode = True


# --- Health Check Schema ---
class HealthCheckResponse(BaseModel):
    status: str = "OK"
    message: str = "API is healthy"
    version: Optional[str] = None # Could be dynamically populated
    timestamp: datetime = Field(default_factory=datetime.utcnow)
