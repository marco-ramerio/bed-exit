"""Step 3 — read thresholds off a session, then score the detector against it.

    python analyse.py session_20260819_221500.csv [more.csv ...]

Prints two numbers that must never be collapsed into one:
missed events, and false alarms.
"""
import sys
import pandas as pd
from detector import run_detector, label_changes, SUSTAIN_SECONDS

MATCH_WINDOW = 10.0     # seconds either side of a labelled event to count as a hit


def separation(df):
    print("\n--- torso angle by label ---")
    print(df.groupby("label")["torso_angle"].describe()[["count", "min", "mean", "max"]])
    print("\n--- confidence by label ---")
    print(df.groupby("label")[["core_conf", "ankle_conf"]].mean())

    lying = df[df.label == "lying"]["torso_angle"]
    up = df[df.label.isin(["sitting", "standing"])]["torso_angle"]
    if len(lying) and len(up):
        gap = up.min() - lying.max()
        print(f"\nseparation: max(lying)={lying.max():.1f}  min(up)={up.min():.1f}  gap={gap:+.1f} deg")
        if gap > 0:
            print("  clean separation. a single threshold between them will work.")
        else:
            print("  OVERLAP. the feature is weak on its own, you need a second one.")


def score(df, name):
    fires = run_detector(df)
    events = label_changes(df)

    matched = set()
    hits = 0
    for f in fires:
        near = [e for e in events if abs(f - e) <= MATCH_WINDOW]
        if near:
            hits += 1
            matched.add(near[0])

    duration = (df["t"].max() - df["t"].min()) / 3600 if len(df) else 0
    false_alarms = len(fires) - hits
    missed = len(events) - len(matched)

    print(f"\n--- {name} ---")
    print(f"  duration          {duration*60:.1f} min")
    print(f"  labelled events   {len(events)}")
    print(f"  fires             {len(fires)}")
    print(f"  MISSED events     {missed}")
    print(f"  FALSE alarms      {false_alarms}"
          + (f"   ({false_alarms/duration:.1f}/hour)" if duration > 0.01 else ""))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    for path in sys.argv[1:]:
        df = pd.read_csv(path).sort_values("t").reset_index(drop=True)
        print(f"\n{'='*60}\n{path}  ({len(df)} frames)\n{'='*60}")
        separation(df)
        score(df, path)
