import cv2
import os
import math

OUT_DIR = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(OUT_DIR, exist_ok=True)

out_path = os.path.join(OUT_DIR, 'synthetic_test.avi')
width, height = 640, 480
fps = 20
frames = 200

fourcc = cv2.VideoWriter_fourcc(*'XVID')
writer = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

# Create some moving blobs
blobs = [
    {'cx': 50, 'cy': 60, 'vx': 2.5, 'vy': 1.8, 'r': 12},
    {'cx': 120, 'cy': 300, 'vx': 1.8, 'vy': -2.2, 'r': 14},
    {'cx': 500, 'cy': 200, 'vx': -2.0, 'vy': 1.2, 'r': 10}
]

for f in range(frames):
    frame = 30 * (np.ones((height, width, 3), dtype='uint8')) if False else None
    import numpy as np
    frame = np.zeros((height, width, 3), dtype='uint8')

    # background gradient
    for y in range(height):
        color = 40 + int(80 * (y / height))
        frame[y, :, :] = (color, color, color)

    # draw blobs
    for b in blobs:
        cv2.circle(frame, (int(b['cx']), int(b['cy'])), b['r'], (255, 255, 255), -1)
        b['cx'] += b['vx']
        b['cy'] += b['vy']
        # bounce on edges
        if b['cx'] < 0 or b['cx'] > width:
            b['vx'] *= -1
        if b['cy'] < 0 or b['cy'] > height:
            b['vy'] *= -1

    # occasionally add a small random blob (simulate appearance)
    if f % 50 == 0:
        rx = np.random.randint(50, width-50)
        ry = np.random.randint(50, height-50)
        rr = np.random.randint(8, 16)
        cv2.circle(frame, (rx, ry), rr, (255,255,255), -1)

    writer.write(frame)

writer.release()
print('SYNTHETIC_VIDEO_CREATED', out_path)
