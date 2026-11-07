#!/usr/bin/env python3
"""Step 4 — the overnight logger. Runs unattended on the Pi as a service.

    python log_night.py                 # Pi camera, the real thing
    python log_night.py --source 0      # laptop webcam, for the rehearsal
    python log_night.py --source x.mp4  # replay a file through the whole path
    python log_night.py --now           # ignore the night window and start

It is calibrate.py with the human removed: no window, no keyboard labels, no
video of the whole night. It logs the same columns, saves a short clip only
when the detector fires, and sends one summary in the morning.

It does not ring anything. Enabling the trigger is step 7 and is one line.

The failure this file is built against is not a missed exit. It is the process
dying at 01:30 and nobody noticing until Friday. Hence: systemd with
Restart=always, a restart counter that survives the restart, a heartbeat that
proves the night happened, and a camera-moved check, because a knocked camera
invalidates every threshold in the project and is otherwise completely silent.
"""
import argparse, csv, json, math, os, shutil, signal, subprocess, sys, time
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path

import cv2
import numpy as np
import detector as D          # thresholds and the subject rule live there, not here

# ---- configuration: this block and detector.py are the only things you edit ----
NIGHT_START   = 22           # hour it starts watching
NIGHT_END     = 8            # hour it stops and sends the summary
FPS           = 5            # the plan's budget; the Pi manages 6-12
SIZE          = (1280, 720)
MODEL         = "yolo11n-pose_ncnn_model"   # falls back to the .pt if absent

DATA          = Path.home() / "bedexit-data"
CLIP_PRE_S    = 5            # seconds of context kept before a fire
CLIP_POST_S   = 10
CLIP_WIDTH    = 640
MIN_FREE_MB   = 1000         # prune oldest clips below this, before the card fills

# public topic: the name is the password, so it lives outside git.
# Set NTFY_TOPIC in the environment, or put it in ntfy_topic.txt next to this file.
_TOPIC_FILE   = Path(__file__).with_name("ntfy_topic.txt")
NTFY_TOPIC    = os.environ.get("NTFY_TOPIC") or (_TOPIC_FILE.read_text().strip() if _TOPIC_FILE.exists() else "")
MOVE_ALERT    = 12.0         # mean abs pixel difference vs the reference still
# -------------------------------------------------------------------------------

STATE = DATA / "state.json"
REF   = DATA / "reference.jpg"

COLUMNS = ["t", "torso_angle", "sh_x", "sh_y", "hip_x", "hip_y",
           "ankle_l_x", "ankle_l_y", "ankle_r_x", "ankle_r_y",
           "core_conf", "ankle_conf", "sh_conf", "hip_conf", "core_min",
           "nose_conf", "head_conf", "n_people", "track_id", "fired"]

CORE, SHOULDER, HIP, ANKLES, HEAD = [5, 6, 11, 12], [5, 6], [11, 12], [15, 16], [0, 1, 2, 3, 4]

running = True


def stop(signum, frame):
    """systemd stops us with SIGTERM. Finish the row, close the file, exit clean."""
    global running
    running = False


def load_state():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text())
        except json.JSONDecodeError:
            pass                      # corrupt state is not worth dying over
    return {"restarts": -1, "last_heartbeat": ""}


def save_state(st):
    STATE.write_text(json.dumps(st))


def in_night(now=None):
    h = (now or datetime.now()).hour
    if NIGHT_START > NIGHT_END:          # the normal case: 22:00 through 08:00
        return h >= NIGHT_START or h < NIGHT_END
    return NIGHT_START <= h < NIGHT_END


def free_mb(path):
    return shutil.disk_usage(path).free / 1e6


def prune(log):
    """Delete oldest clips until there is room. Clips go first: the CSVs are the
    evidence every threshold is derived from, the clips are a convenience."""
    while free_mb(DATA) < MIN_FREE_MB:
        clips = sorted(DATA.glob("clip_*.mp4"), key=lambda p: p.stat().st_mtime)
        if not clips:
            log(f"disk low ({free_mb(DATA):.0f}MB free) and no clips left to delete")
            return
        log(f"disk low, deleting {clips[0].name}")
        clips[0].unlink()


def notify(text, log):
    """Never let the notifier take the logger down with it."""
    log(text.replace("\n", " | "))
    if not NTFY_TOPIC:
        return
    try:
        import requests
        requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=text.encode(), timeout=10)
    except Exception as e:
        log(f"heartbeat send failed, night still logged: {e}")


def throttled():
    """Undervoltage corrupts SD cards silently. 0x0 is the answer you want."""
    try:
        out = subprocess.run(["vcgencmd", "get_throttled"], capture_output=True,
                             text=True, timeout=5).stdout.strip()
        return out.split("=")[-1] or "?"
    except Exception:
        return "n/a"          # not a Pi, or vcgencmd missing


def camera_moved(frame, log):
    """A knocked camera silently invalidates BED_BOX and every threshold. Compare
    the night's first frame against the reference still saved at install."""
    if not REF.exists():
        cv2.imwrite(str(REF), frame)
        log("no reference still, saved this frame as the reference")
        return None
    ref = cv2.imread(str(REF))
    if ref is None or ref.shape != frame.shape:
        return None
    a = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY).astype("float32")
    b = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype("float32")
    return float(abs(a - b).mean())


class LiveDetector:
    """The streaming twin of detector.run_detector.

    Same constants, same sustain logic, same arming behaviour, so a night
    replayed offline gives the same answer as the night gave live. If you change
    one, change the other, and check them against the same CSV.
    """

    def __init__(self):
        self.run_start = None
        self.armed = True
        self.last_good = None
        self.last_fire = None

    def update(self, row):
        s = D.frame_score(row)
        t = row["t"]

        if s is None:
            if (self.run_start is not None and self.last_good is not None
                    and t - self.last_good > D.MAX_GAP_SECONDS):
                self.run_start, self.armed = None, True
            return False

        if self.last_good is not None and t - self.last_good > D.MAX_GAP_SECONDS:
            self.run_start, self.armed = None, True
        self.last_good = t

        if s >= 1:
            if self.run_start is None:
                self.run_start = t
            elif self.armed and t - self.run_start >= D.SUSTAIN_SECONDS:
                self.armed = False
                if self.last_fire is None or t - self.last_fire >= D.REFIRE_LOCKOUT_S:
                    self.last_fire = t
                    return True
        else:
            self.run_start, self.armed = None, True
        return False


def open_camera(source):
    """Returns a read() -> (ok, frame) callable and a close().

    The Camera Module 3 is a CSI device and on Bookworm that goes through
    libcamera and picamera2, not the V4L2 path cv2.VideoCapture expects. The
    --source flag exists so the whole file can be rehearsed on the laptop
    webcam before the board arrives.
    """
    if source is None:
        from picamera2 import Picamera2
        cam = Picamera2()
        cam.configure(cam.create_video_configuration(
            main={"size": SIZE, "format": "RGB888"}))
        cam.start()
        time.sleep(2)                     # let exposure settle before the first frame
        # picamera2's "RGB888" hands back channels in BGR order, which is what
        # OpenCV and ultralytics already expect. No conversion. Do not "fix" this.
        return (lambda: (True, cam.capture_array()), cam.stop, time.time, True)

    cap = cv2.VideoCapture(int(source) if str(source).isdigit() else source)
    if not cap.isOpened():
        raise SystemExit(f"could not open source {source}")

    if str(source).isdigit():                 # a webcam is live, pace it like one
        return (lambda: cap.read(), cap.release, time.time, True)

    # A file is not live. Run it as fast as the model manages, and take the
    # clock from the frame index rather than the wall, so the sustain window is
    # measured against the video's own time. Replaying a night offline has to
    # give the same answer the night gave live, or the replay is worthless.
    file_fps = cap.get(cv2.CAP_PROP_FPS) or FPS
    base, n = time.time(), [0]

    def read():
        ok, fr = cap.read()
        n[0] += 1
        return ok, fr

    return (read, cap.release, lambda: base + n[0] / file_fps, False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=None,
                    help="camera index or video file; omit for the Pi camera")
    ap.add_argument("--now", action="store_true", help="ignore the night window")
    args = ap.parse_args()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    DATA.mkdir(parents=True, exist_ok=True)
    logfile = open(DATA / "log_night.log", "a", buffering=1)

    def log(msg):
        line = f"{datetime.now():%Y-%m-%d %H:%M:%S}  {msg}"
        print(line, flush=True)
        logfile.write(line + "\n")

    st = load_state()
    st["restarts"] = st.get("restarts", -1) + 1
    save_state(st)
    log(f"started (restart #{st['restarts']}, throttled={throttled()})")

    from ultralytics import YOLO
    model_path = Path(__file__).parent / MODEL
    if not model_path.exists():
        log(f"{MODEL} not found, falling back to yolo11n-pose.pt (slower on ARM)")
        model_path = Path(__file__).parent / "yolo11n-pose.pt"
    model = YOLO(str(model_path))

    read, close, clock, pace = open_camera(args.source)
    interval = 1.0 / FPS

    night_id = None
    f = writer = None
    frames = fires = 0
    ring = deque(maxlen=CLIP_PRE_S * FPS)   # jpeg bytes: cheap to hold, cheap to drop
    clip = None
    first_frame_checked = False
    moved = None
    blind = 0                # consecutive failed reads

    try:
        while running:
            if not (args.now or in_night()):
                if f is not None:                       # night just ended
                    f.close(); f = None
                    hours = f"{NIGHT_START:02d}:00 to {NIGHT_END:02d}:00"
                    msg = (f"bedcam {night_id}: ran {hours}, {frames} frames, "
                           f"{fires} fires, {st['restarts']} restarts, "
                           f"throttled={throttled()}, {free_mb(DATA):.0f}MB free")
                    if moved is not None:
                        msg += f", frame diff {moved:.1f}"
                        if moved > MOVE_ALERT:
                            msg += "  ** CAMERA MAY HAVE MOVED **"
                    notify(msg, log)
                    st["restarts"] = 0
                    st["last_heartbeat"] = night_id
                    save_state(st)
                    night_id = None
                time.sleep(30)
                continue

            if f is None:                               # night starting
                night_id = datetime.now().strftime("%Y%m%d")
                if datetime.now().hour < NIGHT_END:     # after midnight: it is last night's
                    night_id = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
                prune(log)
                path = DATA / f"night_{night_id}.csv"
                new = not path.exists()
                f = open(path, "a", newline="")
                writer = csv.writer(f)
                if new:
                    writer.writerow(COLUMNS)
                frames = fires = 0
                first_frame_checked = False
                det = LiveDetector()
                log(f"night {night_id} started -> {path.name}")

            t0 = time.time()
            ok, frame = read()
            if not ok:
                if not pace:                 # a file simply ended
                    log("end of source")
                    break
                blind += 1
                if blind == 1 or blind % 30 == 0:
                    log(f"no frame from camera ({blind} in a row)")
                if blind >= 30:
                    # Do not sit here logging politely. Exit non-zero and let
                    # systemd restart us, which reopens the camera. A process
                    # that stays alive with a dead camera is the silent failure
                    # this whole file exists to prevent: the service looks
                    # healthy and the morning heartbeat reports a night that
                    # never happened.
                    log("camera gone, exiting for systemd to restart")
                    if f is not None:
                        f.close()
                    close()
                    sys.exit(1)
                time.sleep(1)
                continue
            blind = 0

            if not first_frame_checked:
                moved = camera_moved(frame, log)
                first_frame_checked = True

            frames += 1
            r = model.track(frame, persist=True, conf=0.25, verbose=False)[0]

            i = None
            if r.boxes is not None and len(r.boxes) and r.keypoints is not None:
                i = D.pick_subject(r.boxes.xyxy.tolist(), r.keypoints.conf.tolist())

            fired = False
            if i is not None:
                k = r.keypoints.xy[i].tolist()
                c = r.keypoints.conf[i].tolist()
                sh  = ((k[5][0] + k[6][0]) / 2, (k[5][1] + k[6][1]) / 2)
                hip = ((k[11][0] + k[12][0]) / 2, (k[11][1] + k[12][1]) / 2)
                dy, dx = hip[1] - sh[1], abs(sh[0] - hip[0])
                angle = math.degrees(math.atan2(dy, dx if dx > 1 else 1))
                ids = r.boxes.id

                row = {"t": clock(), "torso_angle": angle,
                       "hip_x": hip[0], "hip_y": hip[1],
                       "core_conf": sum(c[j] for j in CORE) / 4,
                       "ankle_conf": (c[15] + c[16]) / 2,
                       "nose_conf": c[0]}
                fired = det.update(row)

                writer.writerow([round(row["t"], 3), round(angle, 1),
                                 *[round(v, 1) for v in sh], *[round(v, 1) for v in hip],
                                 *[round(v, 1) for v in k[15]], *[round(v, 1) for v in k[16]],
                                 round(row["core_conf"], 2), round(row["ankle_conf"], 2),
                                 round(sum(c[j] for j in SHOULDER) / 2, 2),
                                 round(sum(c[j] for j in HIP) / 2, 2),
                                 round(min(c[j] for j in CORE), 2),
                                 round(c[0], 2), round(max(c[j] for j in HEAD), 2),
                                 len(r.keypoints.xy),
                                 int(ids[i]) if ids is not None else -1,
                                 int(fired)])

            small = cv2.resize(frame, (CLIP_WIDTH,
                                       int(frame.shape[0] * CLIP_WIDTH / frame.shape[1]) // 2 * 2))
            ring.append(cv2.imencode(".jpg", small)[1].tobytes())

            if fired:
                fires += 1
                log(f"FIRE #{fires}")
                if clip is None:
                    clip = {"frames": [cv2.imdecode(np.frombuffer(b, np.uint8), 1)
                                       for b in ring],
                            "until": clock() + CLIP_POST_S,
                            "name": DATA / f"clip_{datetime.now():%Y%m%d_%H%M%S}.mp4"}
                else:
                    clip["until"] = clock() + CLIP_POST_S   # extend, don't start a second

            if clip is not None:
                clip["frames"].append(small)
                if clock() >= clip["until"]:
                    h, w = clip["frames"][0].shape[:2]
                    vw = cv2.VideoWriter(str(clip["name"]),
                                         cv2.VideoWriter_fourcc(*"mp4v"), FPS, (w, h))
                    for fr in clip["frames"]:
                        vw.write(fr)
                    vw.release()
                    log(f"wrote {clip['name'].name} ({len(clip['frames'])} frames)")
                    clip = None
                    prune(log)

            if pace:
                time.sleep(max(0.0, interval - (time.time() - t0)))

    finally:
        if f is not None:
            f.close()
        close()
        log("stopped")


if __name__ == "__main__":
    main()
