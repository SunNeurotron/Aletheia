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

from typing import Awaitable, Callable, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from aletheia_common.auth.jwt_handler import UserInDB
from aletheia_common.auth.models import ResearcherDB
from ..infrastructure.database import get_db_session

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)


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
        user_roles = ["researcher"]
        if researcher.is_admin:
            if "admin" not in user_roles:
                user_roles.append("admin")

        is_disabled = researcher.disabled

        return UserInDB(
            username=researcher.username,
            email=researcher.email,
            full_name=researcher.full_name,
            hashed_password=researcher.hashed_password,
            roles=sorted(list(set(user_roles))),
            disabled=is_disabled,
        )
    return None


def get_user_retriever() -> Callable[[str], Awaitable[Optional[UserInDB]]]:
    """
    Returns the actual user retriever function.
    """
    return get_researcher_for_auth


async def authenticate_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db_session),
) -> UserInDB:
    """
    Authenticates a researcher from ResearcherDB.
    Used by the /token endpoint.
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
    if user_in_db.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return user_in_db
