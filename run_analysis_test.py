import os
import json
import sys

from analyzer import analyze_video_file

BASE = os.path.dirname(__file__)
UPLOADS = os.path.join(BASE, 'uploads')

if not os.path.isdir(UPLOADS):
    print('NO_UPLOADS_DIR')
    sys.exit(2)

candidates = [f for f in os.listdir(UPLOADS) if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]
if not candidates:
    print('NO_VIDEO_FILES')
    sys.exit(3)

video_file = os.path.join(UPLOADS, candidates[0])
print('ANALYZING', video_file)
try:
    results = analyze_video_file(video_file, max_frames=200, sample_rate=5, min_area=400)
    print(json.dumps(results, indent=2))
except Exception as e:
    print('ANALYSIS_ERROR:', str(e))
    sys.exit(1)
