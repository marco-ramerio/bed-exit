"""Step 1 — does pose estimation run at all.

Stand in front of the camera. You should see a skeleton drawn on you.
Press q to quit.

macOS will ask for camera permission the first time. The prompt attaches to the
terminal app, not to Python. If it cannot show a prompt you get black frames
rather than an error.
"""
from ultralytics import YOLO
import cv2

model = YOLO("yolo11n-pose.pt")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    raise SystemExit("Camera did not open. Check terminal camera permission in System Settings.")

while True:
    ok, frame = cap.read()
    if not ok:
        break
    r = model(frame, verbose=False)[0]
    cv2.imshow("pose", r.plot())
    if cv2.waitKey(1) == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
