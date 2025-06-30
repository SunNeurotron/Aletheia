# Aletheia_v3/api/auth.py
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

# --- Configuration ---
# In a production environment, these should come from environment variables or a config service.
SECRET_KEY = os.getenv("SECRET_KEY", "a-very-secret-key-that-should-be-changed-and-be-very-long")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token dependency
# tokenUrl should point to the endpoint that issues tokens (e.g., /api/v1/token)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # Relative to the router prefix

# --- Mock User Database ---
# In a real application, this would interact with a database (e.g., a User model in SQLAlchemy).
# For simplicity, using an in-memory dictionary.
# Passwords should be stored hashed. The "hashed_password" here is what you'd store.
# To generate: pwd_context.hash("testpassword")
# Default user: username="testuser", password="testpassword"
# Hashed "testpassword": $2b$12$EixZaYVK1xKIx74SAhN7PueE91.qg2vNn2jXRcOB2kK8sUMS83CUm
MOCK_USERS_DB = {
    "testuser": {
        "username": "testuser",
        "full_name": "Test User",
        "email": "testuser@example.com",
        "hashed_password": "$2b$12$EixZaYVK1xKIx74SAhN7PueE91.qg2vNn2jXRcOB2kK8sUMS83CUm",
        "disabled": False,
    },
    "anotheruser": {
        "username": "anotheruser",
        "full_name": "Another User",
        "email": "anotheruser@example.com",
        "hashed_password": pwd_context.hash("securepass123"), # Example of hashing on the fly
        "disabled": False,
    }
}

# --- Utility Functions ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- User Model (Pydantic for response) ---
# This is a simplified User model for what get_current_user might return.
# In a real app, this would likely come from your database models and Pydantic schemas.
class User:
    def __init__(self, username: str, full_name: Optional[str] = None, email: Optional[str] = None, disabled: bool = False):
        self.username = username
        self.full_name = full_name
        self.email = email
        self.disabled = disabled


# --- Dependency for Getting Current User ---

async def get_current_user_from_db(username: str) -> Optional[User]:
    """Simulates fetching a user from the database."""
    if username in MOCK_USERS_DB:
        user_dict = MOCK_USERS_DB[username]
        return User(**user_dict) # type: ignore
    return None

async def get_current_active_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Dependency to get the current active user from a JWT token.
    Validates the token, decodes it, and retrieves the user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await get_current_user_from_db(username) # In a real app, this would query the DB
    if user is None:
        raise credentials_exception
    if user.disabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return user


# --- Authentication Logic for Token Endpoint ---

async def authenticate_user(form_data: OAuth2PasswordRequestForm = Depends()) -> User:
    """
    Authenticates a user based on username and password from form data.
    This is typically used by the /token endpoint.
    """
    user = await get_current_user_from_db(form_data.username) # Check if user exists
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Verify the password
    if not verify_password(form_data.password, MOCK_USERS_DB[user.username]["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.disabled:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return user

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
