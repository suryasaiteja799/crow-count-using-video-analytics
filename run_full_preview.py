import os, json
from datetime import datetime

from app import create_app
from models import db, User, VideoRecord
from analyzer import analyze_video_with_yolo, _HAVE_YOLO

app = create_app()
UPLOADS = os.path.join(os.path.dirname(__file__), 'uploads')

with app.app_context():
    print('HAVE_YOLO=', _HAVE_YOLO)
    # ensure DB tables were created by create_app
    admin = User.query.filter_by(is_super_admin=True).first()
    if not admin:
        # create a fallback user
        admin = User(name='ScriptAdmin', email='script@local', password_hash='x', is_admin=True, is_super_admin=True)
        db.session.add(admin)
        db.session.commit()
    # find a video file
    candidates = ['synthetic_test.avi', 'test.mp4']
    video_path = None
    for c in candidates:
        p = os.path.join(UPLOADS, c)
        if os.path.exists(p):
            video_path = p
            break
    if not video_path:
        for f in os.listdir(UPLOADS):
            if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                video_path = os.path.join(UPLOADS, f)
                break
    if not video_path:
        print('No video found in uploads/')
        raise SystemExit(1)
    filename = os.path.basename(video_path)
    # create DB record
    vr = VideoRecord(user_id=admin.id, filename=filename, status='pending')
    db.session.add(vr)
    db.session.commit()
    print('Created VideoRecord id=', vr.id, 'file=', filename)

    # run analyzer
    out_dir = os.path.join(UPLOADS, 'detections', str(vr.id))
    os.makedirs(out_dir, exist_ok=True)

    try:
        res = analyze_video_with_yolo(video_path, zones=[], grid_size={'x':4,'y':3}, max_frames=10, sample_rate=5, save_frames=True, out_dir=out_dir)
        print(json.dumps(res, indent=2))
        # update DB
        vr.total_count = res.get('total_count', 0)
        vr.processed_at = datetime.utcnow()
        vr.status = 'completed'
        db.session.commit()
        # print saved image URLs (relative to uploads)
        images = res.get('images', [])
        for img in images:
            try:
                rel = os.path.relpath(img, UPLOADS)
                print('image url: /uploads/' + rel.replace('\\\\','/'))
            except Exception:
                print('image path:', img)
    except Exception as e:
        print('ERROR during analysis:', e)
        vr.status = 'error'
        vr.error_message = str(e)
        db.session.commit()
        raise
