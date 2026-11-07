"""Is the camera actually giving us pixels? Run this before any session.

Prints one plain verdict line. No window, no keypresses, two seconds.
Exists because a camera that is not authorised produces a silent black
recording rather than an error, and you only find that out afterwards.
"""
import cv2

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise SystemExit("VERDICT: NOT AUTHORISED — macOS is blocking this app's camera access.")

frame = None
for _ in range(10):          # first frames off a webcam are often junk
    ok, frame = cap.read()
cap.release()

if not ok or frame is None:
    raise SystemExit("VERDICT: NO FRAMES — camera opened but returned nothing.")

print(f"resolution {frame.shape[1]}x{frame.shape[0]}, brightness {frame.mean():.0f}, variation {frame.std():.0f}")
print("VERDICT: BLACK FRAMES — opened, but the image is blank." if frame.std() < 3
      else "VERDICT: LIVE IMAGE — camera is working, go ahead and run calibrate.py")
