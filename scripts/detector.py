"""Step 3 — the detection rule, and a replay harness over logged CSVs.

Tuning means editing the constants below. Nothing else.
"""
import pandas as pd

# ---- tuning constants: this is the only block you edit ----
# Set from the 21 Aug 2026 calibration sessions. 5 exits out of 5 detected,
# zero spurious fires across 3 minutes of labelled lying. See the build plan.
TORSO_UPRIGHT_DEG   = 60      # above this, torso counts as rising
SUSTAIN_SECONDS     = 2.5     # how long the condition must hold
MIN_CORE_CONF       = 0.4     # ignore frames where shoulders/hips are guessed

# Which confidence column the gate reads. "core_conf" is the mean of the four
# core keypoints and is what the night run deploys. It has a known blind spot:
# two confident shoulders at 0.85 and two duvet-guessed hips at 0.10 average to
# 0.475 and pass a 0.4 gate, so a hip the model invented can still set the
# torso angle. Sessions from 22 Aug 2026 onward also log "core_min", so that
# blind spot can be tested by replaying with this set to "core_min". Older CSVs
# do not have the column and fall back to core_conf automatically.
CORE_CONF_FIELD     = "core_conf"
MAX_GAP_SECONDS     = 1.0     # a longer blind gap resets the sustain window

# One exit should be one alarm. Without this, a pause partway up drops the
# score, re-arms the detector, and fires a second time when she resumes:
# observed on the 22 Aug footage, where she crossed the threshold at 4.6s,
# fired at 7.2s, dipped to 49 degrees at 9s, and fired again at 11.7s. Two
# rings for one exit is harmless at 3am but it inflates the fire count that a
# week of nights gets judged on.
REFIRE_LOCKOUT_S    = 60.0

# The ankle test is OFF, and this is a finding rather than a default.
# In the calibration data her ankles sat FURTHER from the camera axis while
# lying (median x 1277) than while sitting (1122) or standing (1063), because
# of where the camera ended up relative to the bed. No value of BED_EDGE_X
# separates the two, and every value fires constantly while she sleeps.
# Do not re-enable this without new data from the Pi's actual mounted angle.
# Reject frames whose subject has no visible head. Anyone upright and close to
# a bedside camera has their head out of shot, and the model invents one at
# ~0.01 confidence while reporting a convincing 90-degree torso. Her nose reads
# 0.99 lying and sitting alike. Applied here as well as in calibrate.py so a
# replay of an old CSV is judged by the same rule as the live system.
# Skipped silently for CSVs recorded before nose_conf existed.
MIN_NOSE_CONF       = 0.5
NOSE                = 0       # COCO keypoint index

# (x1, y1, x2, y2) of the bed in pixels, or None to disable. Far-field backstop
# only: perspective puts a near person inside this box, so it never substitutes
# for the head test. Measure it on the final mount.
BED_BOX             = None

ANKLE_TEST          = False
ANKLE_OUT_MARGIN    = 20      # px beyond bed edge before ankles count as out
MIN_ANKLE_CONF      = 0.4     # below this, don't score the ankle test at all
BED_EDGE_X          = 900     # unused while ANKLE_TEST is False
# -----------------------------------------------------------


def pick_subject(boxes, kp_confs):
    """Which detected person is her. Returns an index, or None for nobody.

    Two layers, order matters. See scenarios-and-decisions.md, entries 2 and 3.

    1. Head visible. A camera at mattress height cannot see the head of anyone
       standing beside it, so the model invents one at ~0.01 confidence while
       reporting a convincing 90-degree torso. This removes everyone close to
       the lens, which is exactly where a positional test fails.
    2. In the bed. Only meaningful once BED_BOX is measured on the final mount.
       Catches the far case layer 1 lets through: someone upright at the door,
       head in frame, small in the picture.

    Takes plain lists rather than a Results object so this module stays free of
    ultralytics and can be unit tested and replayed without it.
    """
    cand = [i for i in range(len(boxes)) if kp_confs[i][NOSE] >= MIN_NOSE_CONF]

    if BED_BOX is not None:
        x1, y1, x2, y2 = BED_BOX
        cand = [i for i in cand
                if x1 <= (boxes[i][0] + boxes[i][2]) / 2 <= x2
                and y1 <= (boxes[i][1] + boxes[i][3]) / 2 <= y2]

    if not cand:
        return None
    return max(cand, key=lambda i: (boxes[i][2] - boxes[i][0]) * (boxes[i][3] - boxes[i][1]))


def frame_score(row):
    """Return 0..2, or None if the frame is unusable. Higher means more likely getting up."""
    conf = row.get(CORE_CONF_FIELD, row["core_conf"])
    if pd.isna(conf):
        conf = row["core_conf"]
    if conf < MIN_CORE_CONF:
        return None                      # unusable frame, not a negative

    score = 0
    if row["torso_angle"] > TORSO_UPRIGHT_DEG:
        score += 1
    # Gated on ankle confidence: under a duvet the model invents ankle
    # positions, and an invented ankle past the bed edge is a false alarm
    # generated from nothing.
    if ANKLE_TEST and row["ankle_conf"] >= MIN_ANKLE_CONF and (
            row["ankle_l_x"] > BED_EDGE_X + ANKLE_OUT_MARGIN or
            row["ankle_r_x"] > BED_EDGE_X + ANKLE_OUT_MARGIN):
        score += 1
    return score


def run_detector(df, fire_at=1):
    """Replay over a logged CSV. Returns list of fire timestamps."""
    fires, run_start, armed, last_good_t = [], None, True, None
    last_fire = None

    for _, row in df.iterrows():
        s = frame_score(row)

        if s is None:
            # Unusable frame. If we've been blind too long, the sustain window is void.
            if (run_start is not None and last_good_t is not None
                    and row["t"] - last_good_t > MAX_GAP_SECONDS):
                run_start, armed = None, True
            continue

        # Resuming after a long gap is not a continuation.
        if last_good_t is not None and row["t"] - last_good_t > MAX_GAP_SECONDS:
            run_start, armed = None, True
        last_good_t = row["t"]

        if s >= fire_at:
            if run_start is None:
                run_start = row["t"]
            elif armed and row["t"] - run_start >= SUSTAIN_SECONDS:
                if last_fire is None or row["t"] - last_fire >= REFIRE_LOCKOUT_S:
                    fires.append(row["t"])
                    last_fire = row["t"]
                armed = False            # don't re-fire continuously
        else:
            run_start, armed = None, True

    return fires


def label_changes(df, to=("sitting", "standing")):
    """Timestamps where the ground-truth label changed into one of `to`."""
    events, prev = [], None
    for _, row in df.iterrows():
        if row["label"] != prev and row["label"] in to:
            events.append(row["t"])
        prev = row["label"]
    return events
