import os, json
from analyzer import analyze_video_with_yolo, _HAVE_YOLO

print('HAVE_YOLO=', _HAVE_YOLO)
img = os.path.join(os.path.dirname(__file__), 'pexels-jopwell-2422290.jpg')
if not os.path.exists(img):
    print('Image not found:', img)
    raise SystemExit(1)

out_dir = os.path.join(os.path.dirname(__file__), 'uploads', 'detections_preview', 'pexels')
os.makedirs(out_dir, exist_ok=True)

res = analyze_video_with_yolo(img, zones=[], grid_size={'x':4,'y':3}, max_frames=1, sample_rate=1, save_frames=True, out_dir=out_dir)
print(json.dumps(res, indent=2))
print('Saved images:')
for p in res.get('images', []):
    print(' -', p)
