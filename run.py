"""NINJA VISION entry point.

Run from the project root:

    .venv/bin/python run.py                  # live preview, Q quits, H toggles HUD
    .venv/bin/python run.py --no-effects     # start with the visual effects off
    .venv/bin/python run.py --no-sound       # start with the sound effects off
    .venv/bin/python run.py --no-face        # keep the (now unused) FaceMesh stage off
    .venv/bin/python run.py --no-hud         # start with the HUD hidden
    .venv/bin/python run.py --hud-details    # full status panel instead of the clean card
    .venv/bin/python run.py --seconds 5      # auto-stop after 5 s (smoke test)
    .venv/bin/python run.py --export-on-exit # write outputs/signals_<stamp>.png at the end
    .venv/bin/python run.py --record         # guided gesture recording, then live testing
    .venv/bin/python run.py --record --attempts 8
    .venv/bin/python run.py --record-neutral     # NEUTRAL only (always 5 attempts)
    .venv/bin/python run.py --record-chidori     # CHIDORI only
    .venv/bin/python run.py --record-rasengan    # RASENGAN only
    .venv/bin/python run.py --record-chidori --record-rasengan
    .venv/bin/python run.py --evaluate outputs/gesture_recordings/<stamp>
    .venv/bin/python run.py --evaluate outputs/gesture_recordings/<stamp> --no-save

``G`` exports the signal graph at any time during a session. ``R`` starts a
full guided recording in the running session (``P`` pauses it). ``1``..``5``
force Rasengan, Chidori, Fire Wall, Water Wall or Lightning Storm as
clearly-labelled keyboard SIMULATION, and ``0`` returns to LIVE detection. ``E``
toggles the visual effects and ``S`` the sound (``+`` / ``-`` change the
volume); both are painted/played as pure output and never feed the recogniser.

``H`` hides/shows everything the HUD draws. By default that is the clean
recording view - the LIVE/SIMULATION badge, the recording prompt and the jutsu
card in the bottom-right corner - because the point of the window is to be
filmed. ``--hud-details`` swaps in the old full panel (FPS, palm coordinates,
every gate of every recogniser, the key hints), which is what calibration and
debugging still need.

``--evaluate`` re-scores a recorded session with the
current config.py, without opening the camera; ``--no-save`` makes it print the
report without writing ``evaluation_<stamp>.txt`` into the session folder.

The project is deliberately not an installed package (no pyproject.toml - see
requirements.txt), so this file puts ``src/`` and the project root on sys.path
before importing ``ninja``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"

for _path in (str(PROJECT_ROOT), str(SRC_DIR)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from ninja.app import App  # noqa: E402  (must follow the sys.path setup above)
from ninja.effects.sound import SoundManager  # noqa: E402
from ninja.face_tracker import FaceTracker  # noqa: E402

import config  # noqa: E402
from ninja.gesture_recorder import LABELS  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="run.py",
        description=("NINJA VISION - Phase 9: five jutsu gesture recognition, "
                     "Fire Wall + cinematic Lightning Storm effects and sound"),
    )
    parser.add_argument(
        "--seconds", type=float, default=None, metavar="N",
        help="stop automatically after N seconds (used for smoke tests)",
    )
    parser.add_argument(
        "--no-hud", action="store_true",
        help="start with the HUD hidden",
    )
    parser.add_argument(
        "--hud-details", action="store_true",
        help=("draw the full status panel (FPS, palm, every gate, key hints) "
              "instead of the clean badge + jutsu card"),
    )
    parser.add_argument(
        "--export-on-exit", action="store_true",
        help="write the raw-vs-filtered signal graph to outputs/ when the session ends",
    )
    parser.add_argument(
        "--no-effects", action="store_true",
        help="start with the Phase 4 visual effects disabled (E toggles them live)",
    )
    parser.add_argument(
        "--no-sound", action="store_true",
        help="start with the Phase 5 sound disabled (S toggles it live; no audio "
             "device is opened at all)",
    )
    parser.add_argument(
        "--no-face", action="store_true",
        help="keep the MediaPipe FaceMesh stage off; Phase 9 no jutsu reads a "
             "mouth, so this is already the default (kept for compatibility)",
    )
    parser.add_argument(
        "--record", action="store_true",
        help="start a guided NEUTRAL / CHIDORI / RASENGAN recording immediately "
             "(saved to outputs/gesture_recordings/<stamp>/), then keep testing live",
    )
    parser.add_argument(
        "--record-neutral", action="store_true",
        help="record only NEUTRAL attempts (%d, fixed)" % config.RECORD_NEUTRAL_ATTEMPTS,
    )
    parser.add_argument(
        "--record-chidori", action="store_true",
        help="record only CHIDORI attempts (--attempts controls how many)",
    )
    parser.add_argument(
        "--record-rasengan", action="store_true",
        help="record only RASENGAN attempts (--attempts controls how many)",
    )
    parser.add_argument(
        "--attempts", type=int, default=None, metavar="N",
        help=f"CHIDORI and RASENGAN attempts each "
             f"({config.RECORD_ATTEMPTS_MIN}..{config.RECORD_ATTEMPTS_MAX}, "
             f"default {config.RECORD_ATTEMPTS_DEFAULT}); NEUTRAL is always "
             f"{config.RECORD_NEUTRAL_ATTEMPTS}",
    )
    parser.add_argument(
        "--evaluate", type=Path, default=None, metavar="DIR",
        help="re-score a recorded session with the current config.py (no camera)",
    )
    parser.add_argument(
        "--no-save", action="store_true",
        help="with --evaluate: print the report but write no file into the session",
    )
    args = parser.parse_args(argv)

    chosen = tuple(
        label for flag, label in (
            (args.record_neutral, "NEUTRAL"),
            (args.record_chidori, "CHIDORI"),
            (args.record_rasengan, "RASENGAN"),
        ) if flag
    )
    if chosen and args.record:
        parser.error("--record already records all three gestures; use either "
                     "--record or the individual --record-* flags")

    attempts = config.RECORD_ATTEMPTS_DEFAULT if args.attempts is None else args.attempts
    if args.attempts is not None and not (
        config.RECORD_ATTEMPTS_MIN <= attempts <= config.RECORD_ATTEMPTS_MAX
    ):
        parser.error(f"--attempts must be between {config.RECORD_ATTEMPTS_MIN} "
                     f"and {config.RECORD_ATTEMPTS_MAX}")
    if chosen == ("NEUTRAL",) and args.attempts is not None:
        parser.error(f"--attempts does not apply to --record-neutral; NEUTRAL is "
                     f"always {config.RECORD_NEUTRAL_ATTEMPTS} attempts")
    if args.no_save and args.evaluate is None:
        parser.error("--no-save only applies together with --evaluate")

    if args.evaluate is not None:
        if chosen or args.record:
            parser.error("--evaluate cannot be combined with recording")
        from ninja.gesture_recorder import evaluation_report

        if not (args.evaluate / "attempts.csv").is_file():
            parser.error(f"{args.evaluate} is not a recording session folder")
        print(evaluation_report(args.evaluate, save=not args.no_save))
        return 0

    return App(
        start_with_hud=not args.no_hud,
        hud_details=args.hud_details,
        export_on_exit=args.export_on_exit,
        record=args.record or bool(chosen),
        record_attempts=attempts,
        record_labels=chosen or LABELS,
        effects=not args.no_effects,
        # Sound is on unless --no-sound: this is the only place a real output
        # device is created, which is what keeps the test suite headless.
        sound=SoundManager(enabled=not args.no_sound),
        # Phase 9: no jutsu reads a face any more (the Fire Wall needs no mouth),
        # so the mesh is never wanted. The tracker is still constructed so the
        # --no-face flag, the shutdown timings and FaceTracker keep working.
        face=FaceTracker(enabled=not args.no_face),
    ).run(max_seconds=args.seconds)


if __name__ == "__main__":
    sys.exit(main())
