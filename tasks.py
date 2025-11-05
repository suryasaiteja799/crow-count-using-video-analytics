import os
from celery import Celery
from datetime import datetime

from models import db, VideoRecord

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', CELERY_BROKER_URL)

celery = Celery('tasks', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)


@celery.task(bind=True, acks_late=True)
def process_video_task(self, record_id, filepath):
    # import here to avoid circular imports on module load
    from video_process import process_video
    from sqlalchemy import create_engine
    from sqlalchemy.orm import scoped_session, sessionmaker

    # Setup a DB session using environment DATABASE_URL if set, else sqlite file
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///data.db')
    engine = create_engine(database_url)
    Session = scoped_session(sessionmaker(bind=engine))
    session = Session()
    try:
        rec = session.query(VideoRecord).get(record_id)
        if not rec:
            raise RuntimeError('Record not found')
        rec.status = 'processing'
        session.commit()

        total_count = process_video(filepath)

        rec.total_count = int(total_count)
        rec.status = 'completed'
        rec.processed_at = datetime.utcnow()
        session.commit()
        return {'total_count': rec.total_count}
    except Exception as exc:
        # mark failure
        if rec:
            rec.status = 'failed'
            rec.error_message = str(exc)
            session.commit()
        raise
    finally:
        Session.remove()
