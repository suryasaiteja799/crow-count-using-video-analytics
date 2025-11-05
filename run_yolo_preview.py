import os, json
from datetime import datetime

from analyzer import analyze_video_with_yolo, _HAVE_YOLO

print('HAVE_YOLO=', _HAVE_YOLO)

uploads = os.path.join(os.path.dirname(__file__), 'uploads')
# try to find a test video
candidates = ['synthetic_test.avi', 'test.mp4']
video_path = None
for c in candidates:
    p = os.path.join(uploads, c)
    if os.path.exists(p):
        video_path = p
        break

if not video_path:
    # fallback: pick any video file in uploads
    for f in os.listdir(uploads):
        if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            video_path = os.path.join(uploads, f)
            break

if not video_path:
    print('NO_VIDEO_FOUND in uploads/')
    raise SystemExit(1)

print('Using video:', video_path)

out_dir = os.path.join(uploads, 'detections_preview')
os.makedirs(out_dir, exist_ok=True)

try:
    res = analyze_video_with_yolo(video_path, zones=[], grid_size={'x':4,'y':3}, max_frames=6, sample_rate=5, save_frames=True, out_dir=out_dir)
    print(json.dumps(res, indent=2))
    print('Saved images:')
    for img in res.get('images', []):
        print(' -', img)
except Exception as e:
    print('ERROR:', str(e))
    raise
