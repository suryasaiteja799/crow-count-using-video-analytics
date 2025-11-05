import cv2

def process_video(path: str) -> int:
    """
    Very simple moving-object counter using background subtraction.
    This is a heuristic demo and not a production-ready crow detector.
    Returns an estimated total number of moving objects seen across frames.
    """
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError('Cannot open video')

    backSub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=False)
    total = 0
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1
        fgMask = backSub.apply(frame)
        # threshold and find contours
        _, thresh = cv2.threshold(fgMask, 200, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        count = 0
        for cnt in contours:
            if cv2.contourArea(cnt) > 500:  # filter small noise
                count += 1
        total = max(total, count)  # keep max concurrent count as estimate

    cap.release()
    return total
