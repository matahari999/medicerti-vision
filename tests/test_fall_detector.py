import sys; sys.path.insert(0, '.')
import numpy as np
from src.detector.fall_detector import FallDetector

detector = FallDetector(velocity_threshold=100.0, angle_threshold=60.0)

standing = [{'x': 320, 'y': 100, 'z': 0, 'visibility': 0.9}] * 33
standing[11] = {'x': 280, 'y': 120, 'z': 0, 'visibility': 0.9}
standing[12] = {'x': 360, 'y': 120, 'z': 0, 'visibility': 0.9}
standing[23] = {'x': 290, 'y': 250, 'z': 0, 'visibility': 0.9}
standing[24] = {'x': 350, 'y': 250, 'z': 0, 'visibility': 0.9}
standing[27] = {'x': 300, 'y': 400, 'z': 0, 'visibility': 0.9}
standing[28] = {'x': 340, 'y': 400, 'z': 0, 'visibility': 0.9}
standing[0] = {'x': 320, 'y': 80, 'z': 0, 'visibility': 0.9}

r1 = detector.detect(standing)
print("Standing: fall={} conf={:.2f} reasons={}".format(r1["fall"], r1["confidence"], r1["reasons"]))

falling = [{'x': 320, 'y': 100, 'z': 0, 'visibility': 0.9}] * 33
for i in range(5):
    falling[23] = {'x': 280, 'y': 150 + i * 30, 'z': 0, 'visibility': 0.9}
    falling[24] = {'x': 360, 'y': 155 + i * 30, 'z': 0, 'visibility': 0.9}
    falling[11] = {'x': 260, 'y': 130 + i * 25, 'z': 0, 'visibility': 0.9}
    falling[12] = {'x': 380, 'y': 135 + i * 25, 'z': 0, 'visibility': 0.9}
    falling[27] = {'x': 290, 'y': 400, 'z': 0, 'visibility': 0.9}
    falling[28] = {'x': 350, 'y': 400, 'z': 0, 'visibility': 0.9}
    falling[0] = {'x': 310, 'y': 120 + i * 22, 'z': 0, 'visibility': 0.9}
    r = detector.detect(falling)
    print("  Frame {}: fall={} conf={:.2f} reasons={}".format(i+1, r["fall"], r["confidence"], r["reasons"]))
