from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
from database import get_db
from models import JobDB, HitDB
from celery_worker import intelligent_discovery_task

class IntelligentSearchRequest(BaseModel):
    n_calls: int = Field(50, gt=10, le=500)

class Hit(BaseModel):
    a: int; b: int; c: int; quality: float
    class Config: orm_mode = True

class Job(BaseModel):
    id: str; status: str; n_calls: int; created_at: datetime; hits: list[Hit] = []
    class Config: orm_mode = True

app = FastAPI(title="ABC Discovery Service", version="2.2")

@app.post("/searches", status_code=202)
def create_search_job(request: IntelligentSearchRequest, db: Session = Depends(get_db)):
    job_id = str(uuid.uuid4())
    db_job = JobDB(id=job_id, n_calls=request.n_calls)
    db.add(db_job)
    db.commit()
    intelligent_discovery_task.delay(db_job.id, request.n_calls)
    return {"job_id": db_job.id, "status": "pending"}

@app.get("/searches/{job_id}", response_model=Job)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    db_job = db.query(JobDB).filter(JobDB.id == job_id).first()
    if db_job is None: raise HTTPException(status_code=404, detail="Job not found")
    return db_job
