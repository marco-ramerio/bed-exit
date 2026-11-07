"""Smoke test: picamera2 -> NCNN YOLO11n-pose -> the features detector.py reads.

Run on the Pi, inside the bedexit venv, with the camera connected and a person
in shot:

    python ~/pi_smoke.py

Answers three things the build plan flags as unverifiable without the board:
whether NCNN inference runs on a live picamera2 frame at all, what confidences
NCNN reports against the PyTorch numbers MIN_CORE_CONF was tuned on, and what
frame rate the Pi actually manages. Nothing here is deployed; it prints and exits.
"""
import math
import time

from picamera2 import Picamera2
from ultralytics import YOLO

MODEL = "yolo11n-pose_ncnn_model"
FRAMES = 10

NOSE = 0
SHOULDER = [5, 6]
HIP = [11, 12]
CORE = SHOULDER + HIP


def midpoint(k, a, b):
    return ((k[a][0] + k[b][0]) / 2, (k[a][1] + k[b][1]) / 2)


picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(
    main={"size": (1280, 720), "format": "RGB888"}))
picam2.start()
time.sleep(1)                      # let auto-exposure settle

model = YOLO(MODEL, task="pose")

for n in range(FRAMES):
    frame = picam2.capture_array()

    t0 = time.time()
    r = model(frame, conf=0.25, verbose=False)[0]
    dt = time.time() - t0

    people = 0 if r.keypoints is None else len(r.keypoints.xy)
    line = f"{n:2d}  {dt * 1000:6.0f} ms  {1 / dt:4.1f} fps  people {people}"

    if people:
        # Largest box, for the smoke test only. The real rule is pick_subject,
        # which needs BED_BOX and therefore the install visit.
        b = r.boxes.xyxy.tolist()
        i = max(range(people),
                key=lambda j: (b[j][2] - b[j][0]) * (b[j][3] - b[j][1]))
        k = r.keypoints.xy[i].tolist()
        c = r.keypoints.conf[i].tolist()

        sh = midpoint(k, 5, 6)
        hip = midpoint(k, 11, 12)
        dy = hip[1] - sh[1]
        dx = abs(sh[0] - hip[0])
        angle = math.degrees(math.atan2(dy, dx if dx > 1 else 1))

        core_conf = sum(c[j] for j in CORE) / len(CORE)
        core_min = min(c[j] for j in CORE)
        sh_conf = sum(c[j] for j in SHOULDER) / len(SHOULDER)
        hip_conf = sum(c[j] for j in HIP) / len(HIP)

        line += (f"   angle {angle:5.1f}  core {core_conf:.2f}"
                 f"  core_min {core_min:.2f}  sh {sh_conf:.2f}"
                 f"  hip {hip_conf:.2f}  nose {c[NOSE]:.2f}")

    print(line)

picam2.stop()
