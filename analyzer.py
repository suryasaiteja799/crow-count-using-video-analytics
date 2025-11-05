import cv2
import math
from datetime import datetime
import os

# Try importing ultralytics YOLO if available
try:
    from ultralytics import YOLO
    _HAVE_YOLO = True
except Exception:
    _HAVE_YOLO = False


def point_in_poly(x, y, poly):
    # Ray-casting algorithm for point in polygon
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]['x'], poly[i]['y']
        xj, yj = poly[j]['x'], poly[j]['y']
        intersect = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi)
        if intersect:
            inside = not inside
        j = i
    return inside


def analyze_video_file(video_path, zones=None, grid_size=None, max_frames=1000, sample_rate=3, min_area=400):
    """Simple motion-based analyzer.

    - zones: list of polygons where each polygon is a list of {x, y} points in pixel coordinates
    - grid_size: dict {x: cols, y: rows}
    - returns dict with zone_counts, grid_counts, total_count and timestamp
    """
    zones = zones or []
    grid_size = grid_size or {'x': 4, 'y': 3}

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError('Unable to open video: ' + str(video_path))

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Prepare counters
    zone_counts = {i: 0 for i in range(len(zones))}
    grid_counts = {}
    for gy in range(grid_size['y']):
        for gx in range(grid_size['x']):
            cell_id = f"{chr(65+gy)}{gx+1}"
            grid_counts[cell_id] = 0

    fgbg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=25, detectShadows=True)

    frame_idx = 0
    processed = 0
    total_detections = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1
        if frame_idx % sample_rate != 0:
            continue

        processed += 1
        fgmask = fgbg.apply(frame)

        # Morphological operations to clean mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel, iterations=1)
        fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_DILATE, kernel, iterations=2)

        contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # For each detected contour, compute centroid and categorize
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area:
                continue
            M = cv2.moments(cnt)
            if M['m00'] == 0:
                continue
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])

            total_detections += 1

            # Check zones
            for zi, zone in enumerate(zones):
                if point_in_poly(cx, cy, zone['points'] if 'points' in zone else zone):
                    zone_counts[zi] += 1

            # Check grid cell
            gx = min(grid_size['x'] - 1, int(cx / (width / grid_size['x'])))
            gy = min(grid_size['y'] - 1, int(cy / (height / grid_size['y'])))
            cell_id = f"{chr(65+gy)}{gx+1}"
            grid_counts[cell_id] = grid_counts.get(cell_id, 0) + 1

        # stop early if processed too many frames
        if processed >= max_frames:
            break

    cap.release()

    # Convert counts to expected output structure
    zone_counts_out = {i: {'count': int(zone_counts[i])} for i in zone_counts}
    grid_counts_out = {k: {'count': int(v)} for k, v in grid_counts.items()}

    total_count = sum(v['count'] for v in zone_counts_out.values()) if len(zone_counts_out) else sum(v['count'] for v in grid_counts_out.values())

    results = {
        'timestamp': datetime.utcnow().isoformat(),
        'zone_counts': zone_counts_out,
        'grid_counts': grid_counts_out,
        'total_count': int(total_count),
        'meta': {
            'frames_processed': processed,
            'sample_rate': sample_rate,
            'min_area': min_area
        }
    }

    return results


def analyze_video_with_yolo(video_path, zones=None, grid_size=None, max_frames=1000, sample_rate=3, classes=None, save_frames=False, out_dir=None):
    """Run YOLO detection over a video or image.

    - classes: list of class names (e.g. ['person']) or integer class ids; default is ['person']
    - save_frames: if True, annotated frames (sampled) will be written to out_dir (or uploads/detections/<uuid>) and returned as file paths
    - returns a dict with zone_counts, grid_counts, total_count, meta and optionally 'images' list
    """
    if not _HAVE_YOLO:
        raise RuntimeError('YOLO (ultralytics) not available in this environment')

    zones = zones or []
    grid_size = grid_size or {'x': 4, 'y': 3}

    model = YOLO(os.environ.get('YOLO_MODEL', 'yolov8n.pt'))

    # Normalize classes: support names -> ids
    try:
        names = model.names if hasattr(model, 'names') else None
    except Exception:
        names = None

    class_ids = None
    if classes:
        class_ids = []
        for c in classes:
            if isinstance(c, int):
                class_ids.append(c)
            else:
                if names and c in names:
                    if isinstance(names, dict):
                        for k, v in names.items():
                            if v == c:
                                class_ids.append(int(k))
                                break
                    else:
                        try:
                            idx = names.index(c)
                            class_ids.append(int(idx))
                        except Exception:
                            pass
    else:
        class_ids = []
        try:
            if names:
                if isinstance(names, dict):
                    for k, v in names.items():
                        if v.lower() == 'person':
                            class_ids = [int(k)]
                            break
                else:
                    for idx, nm in enumerate(names):
                        if nm.lower() == 'person':
                            class_ids = [int(idx)]
                            break
        except Exception:
            class_ids = None

    # Detect whether input is image or video
    is_image = False
    lower = str(video_path).lower()
    if lower.endswith(('.jpg', '.jpeg', '.png', '.bmp')):
        is_image = True

    # Prepare counters
    zone_counts = {i: 0 for i in range(len(zones))}
    grid_counts = {}
    for gy in range(grid_size['y']):
        for gx in range(grid_size['x']):
            cell_id = f"{chr(65+gy)}{gx+1}"
            grid_counts[cell_id] = 0

    images_out = []
    processed = 0
    total_detections = 0

    # prepare output dir
    if save_frames:
        import uuid
        run_id = uuid.uuid4().hex
        if out_dir:
            save_dir = out_dir
        else:
            save_dir = os.path.join(os.path.dirname(__file__), 'uploads', 'detections', run_id)
        os.makedirs(save_dir, exist_ok=True)

    def handle_detection_frame(frame, frame_number):
        nonlocal total_detections
        # run model on frame
        res = model(frame)
        boxes = []
        try:
            r0 = res[0]
            b = getattr(r0, 'boxes', None)
            if b is not None:
                for box in b:
                    try:
                        cls_val = int(box.cls.cpu().numpy()[0]) if hasattr(box, 'cls') else int(box.cls)
                    except Exception:
                        cls_val = None
                    if class_ids and cls_val is not None and cls_val not in class_ids:
                        continue
                    xy = box.xyxy.cpu().numpy()[0] if hasattr(box, 'xyxy') else box.xyxy
                    x1, y1, x2, y2 = map(int, xy)
                    boxes.append((x1, y1, x2, y2, cls_val))
        except Exception:
            try:
                for r in res:
                    b = getattr(r, 'boxes', None)
                    if not b:
                        continue
                    for box in b:
                        cls_val = int(box.cls.cpu().numpy()[0]) if hasattr(box, 'cls') else int(box.cls)
                        if class_ids and cls_val is not None and cls_val not in class_ids:
                            continue
                        xy = box.xyxy.cpu().numpy()[0]
                        x1, y1, x2, y2 = map(int, xy)
                        boxes.append((x1, y1, x2, y2, cls_val))
            except Exception:
                boxes = []

        # count boxes into zones/grid
        for (x1, y1, x2, y2, cls_val) in boxes:
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            total_detections += 1
            for zi, zone in enumerate(zones):
                if point_in_poly(cx, cy, zone.get('points', zone)):
                    zone_counts[zi] += 1
            gx = min(grid_size['x'] - 1, int(cx / (frame.shape[1] / grid_size['x'])))
            gy = min(grid_size['y'] - 1, int(cy / (frame.shape[0] / grid_size['y'])))
            cell_id = f"{chr(65+gy)}{gx+1}"
            grid_counts[cell_id] = grid_counts.get(cell_id, 0) + 1

        # annotate and optionally save frame
        if save_frames:
            vis = frame.copy()
            for (x1, y1, x2, y2, cls_val) in boxes:
                cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 0), 2)
                label = str(cls_val) if cls_val is not None else ''
                cv2.putText(vis, label, (x1, max(10, y1-6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
            fname = os.path.join(save_dir, f'frame_{frame_number:05d}.jpg')
            cv2.imwrite(fname, vis)
            images_out.append(fname)

    # If it's an image, just run once
    if is_image:
        img = cv2.imread(video_path)
        if img is None:
            raise RuntimeError('Unable to read image: ' + str(video_path))
        handle_detection_frame(img, 0)
        processed = 1
    else:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError('Unable to open video: ' + str(video_path))
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame_idx += 1
            if frame_idx % sample_rate != 0:
                continue
            handle_detection_frame(frame, frame_idx)
            processed += 1
            if processed >= max_frames:
                break
        cap.release()

    zone_counts_out = {i: {'count': int(zone_counts[i])} for i in zone_counts}
    grid_counts_out = {k: {'count': int(v)} for k, v in grid_counts.items()}

    total_count = sum(v['count'] for v in zone_counts_out.values()) if len(zone_counts_out) else sum(v['count'] for v in grid_counts_out.values())

    results = {
        'timestamp': datetime.utcnow().isoformat(),
        'zone_counts': zone_counts_out,
        'grid_counts': grid_counts_out,
        'total_count': int(total_count),
        'meta': {'frames_processed': processed, 'sample_rate': sample_rate, 'class_ids': class_ids}
    }

    if save_frames:
        results['images'] = images_out

    return results
