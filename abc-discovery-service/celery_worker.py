from celery import Celery
from sqlalchemy.orm import Session
from database import SessionLocal
from models import JobDB, HitDB
from intelligent_search import IntelligentSearchUseCase

celery_app = Celery('tasks', broker='redis://redis:6379/0')

@celery_app.task
def intelligent_discovery_task(job_id: str, n_calls: int):
    db: Session = SessionLocal()
    try:
        job = db.query(JobDB).filter(JobDB.id == job_id).first()
        if not job: return
        job.status = "processing"
        db.commit()

        use_case = IntelligentSearchUseCase()
        hits = use_case.search(n_calls=n_calls)

        for hit in hits:
            db_hit = HitDB(job_id=job_id, a=hit.triple.a, b=hit.triple.b, c=hit.triple.c, quality=hit.quality)
            db.add(db_hit)

        job.status = "completed"
        db.commit()
    finally:
        db.close()
