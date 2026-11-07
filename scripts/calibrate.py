"""Step 2 — calibration session.

Log keypoints with a ground-truth label set by keypress.

    l = lying    s = sitting    u = standing    q = quit

Writes session_<timestamp>.csv next to this script's working directory.

Three things that matter later:
  - picks the person lying in the bed rectangle, not the largest person in
    frame. The carer stands BETWEEN the camera and the bed, so they are the
    nearest thing in shot and the largest-box rule picked them. See pick_person.
  - logs confidence split into core (shoulders, hips) and ankles, because a
    duvet hides ankles while the face keeps an all-17 average looking fine
  - and splits core again into shoulders and hips, because the same trick works
    one level down: a duvet hides hips while two confident shoulders keep the
    core mean above the gate. Logged, not acted on. The firing rule is unchanged.
"""
from detector import pick_subject, MIN_NOSE_CONF, BED_BOX
from ultralytics import YOLO
import cv2, csv, math, time, datetime, argparse

ap = argparse.ArgumentParser()
ap.add_argument("--source", default="0", help="camera index, or a video file to replay")
ap.add_argument("--no-video", action="store_true", help="skip the .mp4, for long overnight runs")
ap.add_argument("--no-window", action="store_true", help="no display; for unattended or headless runs")
ap.add_argument("--width", type=int, default=960, help="width of the recorded video")
args = ap.parse_args()

NOSE     = 0
HEAD     = [0, 1, 2, 3, 4]   # nose, eyes, ears
CORE     = [5, 6, 11, 12]    # shoulders, hips
SHOULDER = [5, 6]
HIP      = [11, 12]
ANKLES   = [15, 16]



model = YOLO("yolo11n-pose.pt")
src = int(args.source) if args.source.isdigit() else args.source
cap = cv2.VideoCapture(src)

if not cap.isOpened():
    raise SystemExit("Camera did not open. Check terminal camera permission in System Settings.")

state = "lying"
counts = {"lying": 0, "sitting": 0, "standing": 0}
stamp = f"{datetime.datetime.now():%Y%m%d_%H%M%S}"
path = f"session_{stamp}.csv"
video_path = None if args.no_video else f"session_{stamp}.mp4"

# The writer opens late, once the real frame rate has been measured over the
# first frames. Guessing the fps writes a file that plays back at the wrong
# speed, which matters when the question is how quickly the skeleton reacts.
writer, t_first, n_frames, out_size = None, None, 0, None

f = open(path, "w", newline="")
w = csv.writer(f)
w.writerow(["t", "label", "torso_angle",
            "sh_x", "sh_y", "hip_x", "hip_y",
            "ankle_l_x", "ankle_l_y", "ankle_r_x", "ankle_r_y",
            "core_conf", "ankle_conf",
            "sh_conf", "hip_conf", "core_min",
            "nose_conf", "head_conf", "n_people", "track_id"])

def midpoint(k, a, b):
    return ((k[a][0] + k[b][0]) / 2, (k[a][1] + k[b][1]) / 2)

def box_area(b):
    return (b[2] - b[0]) * (b[3] - b[1])

def pick_person(r):
    """Adapter: unwrap the Results object, defer the rule to detector.py."""
    if r.keypoints is None or len(r.keypoints.xy) == 0:
        return None
    if r.boxes is None or len(r.boxes) == 0:
        return None
    return pick_subject(r.boxes.xyxy.tolist(), r.keypoints.conf.tolist())

print(f"logging to {path}" + (f" and {video_path}" if video_path else "") + "   keys: l lying / s sitting / u standing / q quit")

while True:
    ok, frame = cap.read()
    if not ok:
        break

    # track(), not the plain call: identical detections, plus a persistent id
    # per person. Nothing fires on the id yet. It is logged so that step 4's
    # overnight CSVs can be replayed against the occupant rule later without
    # having to record another week of nights. See scenarios-and-decisions.md.
    # conf=0.25 is not optional. Tracking runs at a lower confidence floor than
    # plain inference, and ByteTrack's second association stage keeps weak
    # detections that predict() discards. Left at its default this turned one
    # fire into ten on the 22 Aug replay. Pinned to predict()'s threshold it
    # matches frame for frame: 1703 rows against 1707, same single fire.
    r = model.track(frame, persist=True, conf=0.25, verbose=False)[0]
    i = pick_person(r)
    shown = r.plot()          # frame with the skeleton drawn on it

    if i is not None:
        k = r.keypoints.xy[i].tolist()
        c = r.keypoints.conf[i].tolist()

        sh  = midpoint(k, 5, 6)
        hip = midpoint(k, 11, 12)

        # 90 = fully upright, 0 = flat. Image y increases downward.
        dy = hip[1] - sh[1]
        dx = abs(sh[0] - hip[0])
        torso_angle = math.degrees(math.atan2(dy, dx if dx > 1 else 1))

        core_conf  = sum(c[j] for j in CORE) / len(CORE)
        ankle_conf = sum(c[j] for j in ANKLES) / len(ANKLES)
        sh_conf    = sum(c[j] for j in SHOULDER) / len(SHOULDER)
        hip_conf   = sum(c[j] for j in HIP) / len(HIP)
        core_min   = min(c[j] for j in CORE)
        nose_conf  = c[NOSE]
        head_conf  = max(c[j] for j in HEAD)
        n_people   = len(r.keypoints.xy)
        tids       = r.boxes.id if r.boxes is not None else None
        track_id   = int(tids[i]) if tids is not None else -1   # -1: tracker gave none

        w.writerow([time.time(), state, round(torso_angle, 1),
                    *[round(v, 1) for v in sh], *[round(v, 1) for v in hip],
                    *[round(v, 1) for v in k[15]], *[round(v, 1) for v in k[16]],
                    round(core_conf, 2), round(ankle_conf, 2),
                    round(sh_conf, 2), round(hip_conf, 2), round(core_min, 2),
                    round(nose_conf, 2), round(head_conf, 2), n_people, track_id])
        counts[state] += 1

        cv2.putText(shown,
                    f"{state}  angle {torso_angle:.0f}  core {core_conf:.2f}  nose {nose_conf:.2f}  ank {ankle_conf:.2f}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    else:
        cv2.putText(shown, f"{state}  NO PERSON IN BED", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    if BED_BOX is not None:
        cv2.rectangle(shown, (BED_BOX[0], BED_BOX[1]), (BED_BOX[2], BED_BOX[3]),
                      (255, 200, 0), 2)

    if video_path:
        n_frames += 1
        if t_first is None:
            t_first = time.time()
        elif writer is None and n_frames >= 20:
            fps = n_frames / max(time.time() - t_first, 1e-6)
            fh, fw = shown.shape[:2]        # not h, w: w is the CSV writer
            out_size = (args.width, int(fh * args.width / fw) // 2 * 2)   # even height
            writer = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*"mp4v"),
                                     round(fps, 2), out_size)
            print(f"recording video at {fps:.1f} fps, {out_size[0]}x{out_size[1]}")
        if writer is not None:
            writer.write(cv2.resize(shown, out_size))

    if not args.no_window:
        cv2.imshow("calibration", shown)
    key = cv2.waitKey(1)
    if key == ord("l"): state = "lying"
    if key == ord("s"): state = "sitting"
    if key == ord("u"): state = "standing"
    if key == ord("q"): break

f.close()
cap.release()
if writer is not None:
    writer.release()
cv2.destroyAllWindows()
print(f"\nwrote {path}")
if video_path:
    print(f"wrote {video_path}")
print("frames logged:", counts)
