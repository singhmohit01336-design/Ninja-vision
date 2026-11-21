"""Tunables for NINJA VISION (Phases 1-9).

Flat module-level constants on purpose: no dataclass, no YAML, no pydantic. The
whole program is one desktop capture loop on an 8 GB Intel MacBook, and this
module is imported by both the app and the smoke tests, so it must stay cheap
and free of heavy third-party imports.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------- camera ------
CAMERA_INDEX = 0
FRAME_WIDTH = 640          # 480p: leaves the CPU budget for hand tracking in Phase 2
FRAME_HEIGHT = 480
TARGET_FPS = 30

# Phase 0 measured that AVFoundation on this machine only delivers a live stream
# on roughly one open in three; the rest hand back a "mute" capture object that
# reports isOpened() == True but never yields a frame. So the *first* open is
# retried inside this budget, then the validated handle is kept for the whole
# session (see ninja/camera.py).
CAMERA_OPEN_BUDGET_S = 25.0

# A healthy handle returns its first frame in ~0.02 s; a mute one costs a full
# blocking read (~1 s) per try. Keeping this tight fits more reopen attempts
# into the same budget, which is what actually raises the odds of a live stream.
FIRST_FRAME_TIMEOUT_S = 1.0

# A read() that blocks ~1 s and fails means the device went mute mid-session.
# Abandon the session after this much silence rather than hanging forever.
READ_SILENCE_TIMEOUT_S = 2.0

# Selfie view. AVFoundation hands back the raw sensor frame, which reads as
# left-right reversed on screen (move right, the hand on screen goes left), and
# MediaPipe labels handedness assuming a mirrored/selfie input. One horizontal
# flip in Camera.read() serves both. That method is the single point every
# consumer reads from - tracker, recorder, effects, HUD - so the correction is
# applied exactly once. Never add a second flip: two cancel out, and a vertical
# or 180-degree flip would break the HUD, the effects and the landmark drawing.
CAMERA_MIRROR = True

# ------------------------------------------------------------ window / loop ---
WINDOW_NAME = "NINJA VISION"

# ---------------------------------------------------------------- HUD ---------
# Phase 8: the default screen is *clean* - mode badge, recording indicator and
# one small jutsu card. The old full status panel (FPS, every gate, the key
# hints) is still built by ninja/hud.py, but only when asked for with
# --hud-details, so tuning the recognisers never got harder.
HUD_ENABLED_AT_START = True
HUD_DETAILED_AT_START = False

# The jutsu card, as fractions of the frame so it holds at any camera size.
HUD_CARD_MARGIN_RATIO = 0.020     # gap between the card and the frame edges
HUD_CARD_MAX_WIDTH_RATIO = 0.46   # never wider than this share of the frame
HUD_CARD_HOLD_S = 0.90            # stay solid this long after the pose is lost
HUD_CARD_FADE_S = 0.30            # then fade out over this long, then hide
HUD_CARD_KEEP = 0.34              # background brightness left under the card

# ------------------------------------------------------- hand tracking --------
MAX_HANDS = 2              # Phase 9: the Fire Wall sign needs both hands
MODEL_COMPLEXITY = 0       # 0 = fastest model; 1 costs far more CPU for little gain at 480p
MIN_DETECTION_CONFIDENCE = 0.6
MIN_TRACKING_CONFIDENCE = 0.6

# ---------------------------------------------------------------- signals -----
FILTER_WINDOW = 5          # moving-average window in frames (Phase 2 default)
SIGNAL_BUFFER_SIZE = 900   # ~30 s at 30 fps; bounded so a long session cannot grow

# ------------------------------------------------- gesture recognition (P3) ---
# Every threshold below is a dimensionless ratio or an angle, measured in pixel
# space (square units), so it holds for any hand size, any distance and either
# hand. To calibrate: record a session (run.py --record), edit a value here, and
# re-score the same recordings offline with run.py --evaluate <session dir>.

# A finger (index..pinky) is EXTENDED when the PIP joint is nearly straight and
# the tip reaches clearly further from the wrist than the PIP joint does.
# Anything else counts as FOLDED.
FINGER_PIP_ANGLE_MIN = 140.0     # deg, angle MCP-PIP-DIP; 180 = straight
FINGER_REACH_RATIO = 1.10        # dist(tip, wrist) / dist(pip, wrist)

# The thumb is EXTENDED when its IP joint is straight and the tip points away
# from the palm (further from the pinky knuckle than its own IP joint).
THUMB_IP_ANGLE_MIN = 140.0       # deg, angle MCP-IP-TIP
THUMB_REACH_RATIO = 1.08         # dist(tip, pinky MCP) / dist(IP, pinky MCP)

# Palm orientation: signed sine of the angle between wrist->index MCP and
# wrist->pinky MCP, sign-corrected with MediaPipe's handedness label. Positive
# means the palm faces the camera, near 0 means the hand is edge-on.
PALM_FACING_MIN = 0.20
RASENGAN_REQUIRE_PALM_FACING = True
RASENGAN_REQUIRE_THUMB = True    # "all five fingers"; False accepts 4 + any thumb

# A pose may flicker off for this long (one or two bad frames) without
# resetting its hold timer or circle trail, and an active gesture survives
# this long after its pose disappears.
GESTURE_GRACE_S = 0.25

# CHIDORI: index + middle extended, ring + pinky folded, thumb ignored, held
# continuously for this long.
CHIDORI_HOLD_S = 0.50

# RASENGAN: open palm, then at least one full revolution of the palm centre
# completed inside the time window. Samples are only added once the palm has
# moved a minimum step, so a still hand cannot pile up jitter.
#
# Window length is measured, not guessed: in the recorded sessions a steady
# circle takes 3.1-4.2 s per loop, so a 3.0 s window could never hold a whole
# revolution (attempts saturated at 0.72-0.96 rev). 4.5 s fits one loop with
# ~30 % margin while MIN_REVOLUTIONS stays at a full 360 degrees.
RASENGAN_WINDOW_S = 4.5          # a full loop has to fit in this many seconds
RASENGAN_MIN_REVOLUTIONS = 1.0   # one complete loop - never reduced as a fix
RASENGAN_MIN_SAMPLES = 10
RASENGAN_MIN_RADIUS_RATIO = 0.25 # mean loop radius / palm size
RASENGAN_MIN_STEP_RATIO = 0.04   # palm displacement / palm size to add a sample
RASENGAN_MAX_STEP_DEG = 90.0     # larger angular jumps are tracking glitches
RASENGAN_CENTER_DEADZONE = 0.35  # x mean radius; ignore points near the centre
RASENGAN_MIN_CONSISTENCY = 0.75  # |net angle| / total angle; 1.0 = one-way loop

# Trail sampling excludes the thumb: every dropped sample in the recorded
# sessions was a thumb misread while index..pinky stayed extended, wiping 2+
# seconds of revolutions. The strict open-palm pose (all five fingers +
# PALM_FACING_MIN) is still required to FIRE, so a fist can never pre-load a
# loop into the trail.
RASENGAN_TRAIL_FACING_MIN = 0.0  # palm at least side-on toward the camera
# A longer window must not fire on a loop that finished seconds ago: the newest
# motion-gated sample has to be this recent.
RASENGAN_STALE_S = 0.60

# ------------------------------------------------- guided recording (P3) ------
RECORD_ATTEMPTS_DEFAULT = 6      # CHIDORI and RASENGAN attempts each (5..10)
RECORD_ATTEMPTS_MIN = 5
RECORD_ATTEMPTS_MAX = 10
RECORD_NEUTRAL_ATTEMPTS = 5
RECORD_COUNTDOWN_S = 3.0         # instructions + countdown before each attempt
RECORD_REVIEW_S = 1.5            # SUCCESS / FAILED banner after each attempt
RECORD_CAPTURE_S = {             # recording length per attempt, by label
    "NEUTRAL": 3.0,
    "CHIDORI": 3.0,
    # 6 s: with a 4.5 s window a 3-4 s loop needs room even if circling starts
    # late (one recorded failure only began at ~3 s into the capture).
    "RASENGAN": 6.0,
}

# A NEUTRAL attempt is only meaningful if a hand was actually in view - an
# empty frame can never produce a false positive. All 15 NEUTRAL attempts of
# the first sessions had 0 % hand frames and were wrongly scored SUCCESS.
RECORD_NEUTRAL_MIN_HAND_RATE = 0.50
# Hold the countdown at its last second until MediaPipe sees a hand, so a
# capture cannot start on an empty frame. Capped so it can never hang.
RECORD_HOLD_COUNTDOWN_WITHOUT_HAND = True
RECORD_COUNTDOWN_MAX_WAIT_S = 10.0

# ---------------------------------------------------------------- outputs -----
# Absolute, so exports land in the project's outputs/ no matter the cwd.
OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"
# Phase 3 recordings: one fresh, timestamped sub-folder per session.
GESTURE_RECORDINGS_DIR = OUTPUT_DIR / "gesture_recordings"

# ------------------------------------------------------ visual effects (P4) ---
# Effects are painted onto the frame and never fed back into recognition: the
# gesture state machine in ninja/gestures.py stays the only source of truth.
# Nothing in this section is read by Phase 0-3 code.
EFFECTS_ENABLED_AT_START = True
EFFECT_SEED = 20261118          # every animation is reproducible from this seed
EFFECT_MAX_DT_S = 0.05          # a stalled frame must not explode the animation
EFFECT_FADE_OUT_S = 0.30        # effects linger this long after the pose is lost
EFFECT_ANCHOR_TAU_S = 0.08      # one-pole smoothing of the anchor (seconds)
# Palm units per frame: a tracking jump (1.19 palm was measured in the Chidori
# recordings) cannot teleport the effect.
EFFECT_ANCHOR_MAX_STEP_RATIO = 0.35
EFFECT_PALM_FALLBACK_PX = 90.0  # palm size assumed before a hand was measured
EFFECT_MIN_INTENSITY = 0.01     # below this the frame is left completely alone

# Fixed-capacity spark pools, allocated once and reused for the whole session.
# Phase 6/7 add one or two pools per jutsu; the storm's rain is not a particle
# pool (it is drawn as vector streaks on the full frame, see lightning_storm.py).
EFFECT_PARTICLES = {
    "rasengan": 90, "chidori": 70,
    "fire_wall": 150, "fire_wall_smoke": 36,
    "water_drops": 60, "water_bubbles": 24,
    "storm_dust": 120, "storm_leaves": 34,
}

# Adaptive quality: step down while the measured FPS stays low, step back up
# once it is comfortably high. The frame counts are the hysteresis that stops
# the picture from oscillating between levels.
EFFECT_QUALITY_LEVELS = (1.0, 0.6, 0.35)   # particle/glow budget multipliers
EFFECT_FPS_LOW = 26.0
EFFECT_FPS_HIGH = 29.0
EFFECT_QUALITY_DOWN_FRAMES = 30
EFFECT_QUALITY_UP_FRAMES = 120

# RASENGAN orb, as multiples of the measured palm size (wrist -> middle MCP).
RASENGAN_ORB_RADIUS_RATIO = 0.85
# Half-width of the composite box: the outer aura sprite is 5.2 radii across,
# so 2.6 radii keeps the additively-blended ROI from clipping its own glow.
RASENGAN_GLOW_RADIUS_RATIO = 2.6
RASENGAN_CORE_RADIUS_RATIO = 0.52
RASENGAN_RING_COUNT = 3
RASENGAN_ARC_COUNT = 3
RASENGAN_ARC_REFRESH_S = 0.07
RASENGAN_SPIN_BASE = 2.2        # rad/s with no validated revolution
RASENGAN_SPIN_PER_REV = 1.6     # extra rad/s per measured revolution
RASENGAN_RAMP_IN_S = 0.18

# CHIDORI bolts, measured outward from the fingertips.
CHIDORI_CORE_RADIUS_RATIO = 0.45
CHIDORI_BOLT_COUNT = 4
CHIDORI_BRANCH_COUNT = 2
CHIDORI_BOLT_REACH_RATIO = 2.2
CHIDORI_BOLT_REFRESH_S = 0.06
CHIDORI_CHARGE_FLOOR = 0.30     # dim glow as soon as the shape is held
CHIDORI_CHARGE_MAX = 0.55       # never looks fully fired before the 0.50 s hold
CHIDORI_RAMP_IN_S = 0.12

# ------------------------------------------------------------------ sound (P5) ---
# Audio is output only, exactly like the effects: the mixer reads the gesture
# state and the *visible* effect intensity, and never feeds anything back. Every
# audio failure (no device, no file) degrades to silence, never to a crash.
SOUND_ENABLED_AT_START = True
SOUND_VOLUME_DEFAULT = 0.70
SOUND_VOLUME_STEP = 0.10
SOUND_SAMPLERATE = 44100
SOUND_BLOCK_FRAMES = 512         # ~12 ms per callback: the audio thread never waits
SOUND_DIR = Path(__file__).resolve().parent / "assets" / "sounds"

# Crossfades. One-shots run to their own end; loops fade in and out so a pose
# that drops out mid-crackle cannot click.
SOUND_FADE_IN_S = 0.15
SOUND_FADE_OUT_S = 0.30
SOUND_STOP_ALL_S = 0.10

# A loop only plays while the *visible* effect is above this intensity, which is
# what makes it fade out with the glow instead of with the key press. It must
# stay above CHIDORI_CHARGE_MAX so charging never triggers the fired ambience.
SOUND_LOOP_FLOOR = 0.62
# The Rasengan has no charge phase in the picture, so its charge sound follows
# the gesture: an open palm with a partly drawn circle (0.5 = half a lap).
SOUND_RASENGAN_CHARGE_REV = 0.15
# The Lightning Storm has no pose to hold either: its charge cue starts once the
# index fingertip is part-way around a loop, before the loop is complete.
SOUND_STORM_CHARGE_REV = 0.25
# Thunder is played *after* a strike, with a realistic delay (sound travels) and
# a per-strike jitter so no two claps land on the same beat.
SOUND_THUNDER_DELAY_MIN_S = 0.18
SOUND_THUNDER_DELAY_MAX_S = 0.55
# A tiny flicker is not a strike: below this gain the bolt gets no thunder.
SOUND_THUNDER_MIN_GAIN = 0.45
SOUND_THUNDER_MAX_PENDING = 4     # bounded queue: loud cues never pile up

# ------------------------------------------------- new jutsu (P6/P7/P9) --------
# WATER WALL (Phase 6), FIRE WALL and LIGHTNING STORM (Phase 9). Same rules
# as every other threshold in this file: ratios of the measured palm size or
# angles in pixel space, so they hold at any distance, hand size or in-plane
# rotation. Recognition lives in ninja/gestures.py, the pictures in
# ninja/effects/, the audio in ninja/effects/sound.py; nothing here is read by
# Phase 0-5 code paths.
#
# Speed and distance units below are PALM SIZES (wrist -> middle knuckle) and
# palm sizes per second, measured from real frame timestamps - never frames.

# WATER WALL: an upright open palm, held still, without circling.
WATER_HOLD_S = 0.80
WATER_UPRIGHT_MAX_DEG = 40.0     # palm axis (wrist -> middle knuckle) off vertical
WATER_STABLE_RATIO = 0.55        # allowed drift from the hold point, in palms
WATER_CANCEL_WINDOW_S = 0.70     # circular motion is measured over this window
WATER_CANCEL_REVOLUTIONS = 0.25  # ~90 degrees of winding cancels the hold
WATER_CANCEL_CONSISTENCY = 0.60  # one-way winding, i.e. a deliberate circle
WATER_COOLDOWN_S = 0.60
# The palm trail is shared with the Water Wall's cancel test; it has to outlast
# the longest window measured on it and stays bounded (see ninja/gestures.py).
WATER_TRAIL_MAX_S = 1.00

# --- Water Wall picture ------------------------------------------------------
WATER_WALL_WIDTH_RATIO = 4.20
WATER_WALL_HEIGHT_RATIO = 2.60
WATER_WALL_CURVE_RATIO = 0.45    # how far the arc bows, in palm sizes
WATER_WALL_RADIUS_RATIO = 2.60
WATER_WALL_STREAM_COUNT = 9
WATER_WALL_RAMP_IN_S = 0.18
WATER_WALL_DROP_RATE = 46.0
WATER_WALL_BUBBLE_RATE = 18.0

# ------------------------------------------------------- Fire Wall (P9) ------
# CHIDORI and the old Dragon Flame shared the same two digits (index + middle
# extended, ring + pinky folded), so the *distance between the two fingertips*
# Fire Wall does not use one hand at all - the player holds both hands open
# towards the camera - so only CHIDORI still needs the split rule. The
# values come from the recorded CHIDORI sessions: across 1432 shape frames of
# the 18 stored CSVs the split (tip distance / palm size) had p1 = 0.16, so a
# 0.12 floor keeps those recordings scoring exactly as they did.
CHIDORI_MIN_SPLIT_RATIO = 0.12   # below this the pair counts as pressed

# FIRE WALL: BOTH hands open, palms towards the camera, held side by side.
# The detector is gestures.measure_fire_wall(); every threshold is a ratio of a
# palm size or a signed cosine, so it holds at any distance, hand size or screen
# position and for either hand.
#
# Every forbidden look-alike fails at least one gate on each hand:
#   * EXTENDED    - index..pinky out (PIP straight, tip past the PIP) and the
#                   thumb too, which kills fists, the namaste and the Chidori
#                   two-finger seal;
#   * FACING      - the palm must point at the camera, which kills the back of
#                   the hand held up in the same pose;
#   * SPACING     - neighbouring fingertips must keep a gap, which kills fingers
#                   squeezed into one blade (and the old interlocked clasp);
#   * IN FRAME    - all 21 landmarks inside the picture, which kills a hand half
#                   off the edge of the frame;
#   * STABILITY   - the pair's midpoint must not drift while it confirms.
#
# Calibrated on the 23 stored CSVs that contain detections (6629 hand frames):
# 4945 frames of an open palm towards the camera measured spacing p1 = 0.39,
# facing p1 = 0.58, thumb extended 96 %, fully in frame 85 % - so the floors
# below keep essentially every real open palm. Frames with a folded digit
# measured spacing p50 = 0.70, i.e. spacing does NOT separate a fist: the
# EXTENDED gate is what rejects it. Each hand is judged on its own, so one
# missing hand can never be averaged away.
FIRE_WALL_REQUIRE_THUMB = True     # the sign is all five digits, not four
FIRE_WALL_MIN_PALM_FACING = 0.35   # signed cosine; 0 = palm edge-on, 1 = flat on
FIRE_WALL_MIN_FINGER_SPACING = 0.12  # mean tip gap, in palm sizes (real: 0.39+)
FIRE_WALL_FRAME_MARGIN = 0.02      # landmark slack allowed past the frame edge
FIRE_WALL_STABLE_RATIO = 0.80      # midpoint drift, in palm sizes, before the
                                   # 0.50 s hold starts again
FIRE_WALL_HOLD_S = 0.50           # a passing frame must never arm the wall
FIRE_WALL_RELEASE_S = 0.30        # the wall survives a short tracking dropout
FIRE_WALL_COOLDOWN_S = 0.60       # after a release, before the sign re-arms

# --- Fire Wall picture -------------------------------------------------------
# A wall, not a cone: as wide as the frame and rising from the bottom edge.
# Width and height are clamped to the frame so a distant hand cannot shrink it.
FIRE_WALL_WIDTH_RATIO = 8.00     # total width, in palm sizes
FIRE_WALL_MIN_WIDTH_FRAME = 0.85 # ... but never narrower than this share
FIRE_WALL_MAX_WIDTH_FRAME = 1.40 # (the edges may run off frame, that is fine)
FIRE_WALL_HEIGHT_RATIO = 3.00    # flame height above the base line, palms
FIRE_WALL_MIN_HEIGHT_FRAME = 0.34
FIRE_WALL_BASE_Y = 0.90          # base line, fraction of the frame height
FIRE_WALL_TONGUE_COUNT = 26
FIRE_WALL_TONGUE_REFRESH_S = 0.09
FIRE_WALL_RAMP_IN_S = 0.22
FIRE_WALL_EMBER_RATE = 150.0     # sparks per second at full intensity
FIRE_WALL_SMOKE_RATE = 14.0

# ---------------------------------------------------- mouth tracking (P7) ----
# MediaPipe's FaceMesh ships with the installed package (the .tflite models are
# bundled), so no download and no install is needed. Phase 9 removed the only
# reason the app ever ran it (the Dragon Flame needed a mouth), so App no longer
# asks for a face at all and the mesh is never built during normal play; the
# module and these tunables stay because the tracker is still importable, is
# covered by tests and is useful when diagnosing a camera.
FACE_TRACKING_ENABLED = True
FACE_MAX_FACES = 1
FACE_MIN_DETECTION_CONFIDENCE = 0.50
# Mouth opening = distance between the inner lips / distance between the eye
# corners. A closed mouth measures ~0.05-0.15, a wide open one ~0.35+. The two
# thresholds are a hysteretic pair so a half-open mouth cannot chatter.
FACE_MOUTH_OPEN_RATIO = 0.28
FACE_MOUTH_CLOSE_RATIO = 0.18
FACE_MIN_INTERVAL_S = 0.10       # run the mesh at most 10x per second
FACE_STALE_S = 0.60              # a result older than this counts as "no face"

# ---------------------------------------------------- Lightning Storm (P7) ---
# A single index finger draws one small circle (on screen) with its TIP; the
# circle is measured on the fingertip trail, not on the palm, so it cannot be
# confused with RASENGAN (which is an open palm looping) or with CHIDORI
# (index + middle apart).
STORM_MIN_STEP_RATIO = 0.03      # tip displacement before a trail sample is added
STORM_CIRCLE_WINDOW_S = 2.00     # the loop has to fit in this many seconds
STORM_TRAIL_MAX_S = 2.60         # bounded, longer than every window above
STORM_MIN_SAMPLES = 10
STORM_MIN_REVOLUTIONS = 0.90     # a full loop, minus jitter
STORM_MIN_CONSISTENCY = 0.80     # |net angle| / total angle, 1.0 = one-way
STORM_MIN_ROUNDNESS = 0.55       # min radius / max radius around the centroid
STORM_MIN_RADIUS_RATIO = 0.12    # a flick is not a circle (palm sizes)
STORM_MAX_RADIUS_RATIO = 1.60    # "small circle": stays near the fingertip
STORM_STALE_S = 0.40             # the newest sample has to be this recent
STORM_STATE_S = 6.00             # the storm lives this long, then fades
STORM_BOOST_COOLDOWN_S = 0.80    # a new circle sooner than this is not a boost
STORM_MAX_BOOST = 4              # bounded intensity steps
STORM_CHARGE_REV = 0.25          # "the sky is gathering" cue threshold

# --- Storm picture -----------------------------------------------------------
# The clouds are generated on a small canvas and upscaled; the rain, wind
# streaks, debris and bolts are drawn as vectors on the full frame (see the
# module). Every buffer below is allocated once, in the effect's first frame.
STORM_SKY_W = 160
STORM_SKY_H = 120
STORM_CLOUD_ALPHA = 0.62         # 0 = camera untouched, 1 = clouds fully cover
STORM_SKY_DARK = (26, 20, 15)    # BGR: near-black blue-grey
STORM_SKY_LIGHT = (128, 116, 102)  # BGR: the lit top of a cloud body
STORM_RAMP_IN_S = 1.60           # the sky rolls in slowly, never snaps on
STORM_FADE_OUT_S = 1.60          # ... and clears naturally
# Three banks scroll at different speeds and drift upwards at different rates.
# That parallax is what reads as rolling cloud at 160x120; a single sheet would
# look like a panning texture no matter how good the texture is.
STORM_CLOUD_LAYERS = 3
STORM_CLOUD_DRIFT_MIN = 0.025    # sky widths per second, slowest bank
STORM_CLOUD_DRIFT_MAX = 0.085    # ... fastest bank (about 14 canvas px/s)
STORM_CLOUD_RISE = 0.012         # sky heights per second, upward drift
STORM_CLOUD_SWIRL = 0.35         # 0 = flat pan, 1 = heavy shear between banks
# Sheet lightning: the cloud deck lights up on its own, out of phase with the
# bolts, so the sky is never still between strikes.
STORM_SHEET_GAP_MIN_S = 1.10
STORM_SHEET_GAP_MAX_S = 3.60
# Rain in three tiers with their own speed, length and slant, so the frame reads
# as depth instead of one flat sheet of identical streaks.
STORM_RAIN_LAYERS = 3
STORM_RAIN_COUNT = 260           # vector streaks, one preallocated array
STORM_RAIN_MIN_SPEED = 520.0     # px/s, slowest tier
STORM_RAIN_MAX_SPEED = 1180.0    # px/s, fastest tier
STORM_RAIN_MIN_SLANT = -0.52     # dx/dy of one drop (negative = falls leftwards)
STORM_RAIN_MAX_SLANT = -0.24
STORM_WIND_STREAKS = 16
STORM_GUST_GAP_MIN_S = 1.80      # the wind pulses instead of blowing flat
STORM_GUST_GAP_MAX_S = 4.20
STORM_DUST_RATE = 70.0           # debris particles per second at full intensity
STORM_LEAF_COUNT = 34            # lightweight debris pool, bounded
# Irregular strikes - the interval is drawn from this range every time, so
# there is never a fixed rhythm, and a short gap makes two bolts overlap.
STORM_STRIKE_MIN_GAP_S = 0.30
STORM_STRIKE_MAX_GAP_S = 1.70
STORM_STRIKE_LIFE_S = 0.30
STORM_STRIKE_SEGMENTS = 9        # jittered segments in the main channel
STORM_STRIKE_BRANCHES = 5        # branches per bolt, each recursing once
STORM_DOUBLE_STRIKE_CHANCE = 0.35
STORM_MAX_STRIKES = 5            # bounded: older bolts are dropped
STORM_FLASH_DECAY_S = 0.26       # cloud illumination from a strike
# The bolt itself is drawn additively, so the flash shared by the whole frame is
# deliberately small: at the maximum level the deck already covers 62% of the
# feed, and a big uniform lift on top of that would blow the picture out (the
# tests pin the frame mean below 120). The drama comes from the lit cloud patch
# and the bloom around the bolt, not from a global white-out.
STORM_FLASH_LIFT = 10            # additive peak applied to the whole frame
