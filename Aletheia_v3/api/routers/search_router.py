# Copyright 2025 Alant
#
# Licensed under the Apache License, Version 2.0 (the "License");
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
API router for managing and monitoring intelligent search jobs for abc-triples.

Provides endpoints to:
- Create new search jobs (which are processed asynchronously via Celery).
- Retrieve the status and results of existing search jobs.
"""

import logging
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from aletheia_common.auth.jwt_handler import (
    UserAuth as CommonUserAuth,  # Common auth components
)
from aletheia_common.auth.jwt_handler import require_roles

from ...infrastructure.celery_worker import (  # Relative import
    intelligent_discovery_task,
)
from ...infrastructure.database import (  # Relative import from grandparent package
    get_db_session,
)
from ...infrastructure.models import JobDB  # Relative import
from .. import schemas as main_schemas  # Relative import from parent package

router = APIRouter(
    tags=["ABC Discovery"],
)

logger = logging.getLogger(__name__)


@router.post(
    "/searches",
    response_model=main_schemas.JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_new_search_job(
    request: main_schemas.JobCreateRequest,
    db: Session = Depends(get_db_session),
    current_user: CommonUserAuth = Depends(require_roles({"researcher"})),
):
    """
    Creates a new intelligent search job for abc-triples.

    The job is added to the database and a Celery task is enqueued for
    asynchronous processing of the Bayesian optimization search.

    - **n_calls** (in request body): The budget (number of evaluations) for
      the Bayesian optimization.

    :param request: The job creation request containing parameters like `n_calls`.
    :type request: main_schemas.JobCreateRequest
    :param db: Database session dependency.
    :type db: sqlalchemy.orm.Session
    :param current_user: Authenticated user, must have the 'researcher' role.
    :type current_user: aletheia_common.auth.jwt_handler.UserAuth
    :raises HTTPException:
        - 401 if unauthorized.
        - 403 if user lacks the 'researcher' role.
        - 500 if the Celery task fails to be enqueued.
    :return: Details of the initialized job, including its ID and initial status.
    :rtype: main_schemas.JobResponse
    """
    job_id = str(uuid.uuid4())

    db_job = JobDB(id=job_id, n_calls=request.n_calls, status="pending")
    db.add(db_job)
    db.commit()
    db.refresh(db_job)

    try:
        task_result = intelligent_discovery_task.delay(
            job_id=db_job.id, n_calls=request.n_calls
        )
        logger.info(
            f"Celery task enqueued with ID: {task_result.id} for job_id: {db_job.id}"
        )
    except Exception as e:
        logger.exception(
            f"Failed to queue Celery discovery task for job_id: {db_job.id}"
        )
        db_job.status = "failed_queuing"
        db.commit()
        db.refresh(db_job)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue discovery task: {str(e)}",  # Return string representation of error
        )
    return db_job


@router.get("/searches/{job_id}", response_model=main_schemas.JobResponse)
async def get_search_job_status_and_results(
    job_id: str,
    db: Session = Depends(get_db_session),
    current_user: CommonUserAuth = Depends(require_roles({"researcher"})),
):
    """
    Retrieves the status and results of a specific search job by its ID.

    :param job_id: The unique identifier of the search job.
    :type job_id: str
    :param db: Database session dependency.
    :type db: sqlalchemy.orm.Session
    :param current_user: Authenticated user, must have the 'researcher' role.
    :type current_user: aletheia_common.auth.jwt_handler.UserAuth
    :raises HTTPException:
        - 401 if unauthorized.
        - 403 if user lacks the 'researcher' role.
        - 404 if the job with the specified ID is not found.
    :return: The details of the search job, including its status and any results if completed.
    :rtype: main_schemas.JobResponse
    """
    db_job = db.query(JobDB).filter(JobDB.id == job_id).first()
    if db_job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    return db_job
