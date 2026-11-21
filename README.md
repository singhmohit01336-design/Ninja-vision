# NINJA VISION

A real-time jutsu simulator: a webcam, MediaPipe hands tracking **two hands**,
five gesture recognisers, five anime-styled effects and twenty original
synthesised sounds. Everything runs locally on CPU - no network, no assets to
download, no recording of the camera.

**Status: Phase 9 complete.** Five jutsus - Rasengan, Chidori, **Fire Wall**
(both hands open, palms to the camera), Water Wall and a full-frame cinematic
**Lightning Storm**. Phase 9 replaced the old Dragon Flame with the Fire Wall and
rebuilt the storm from the ground up; the FaceMesh that used to gate the fire is
still in the tree but is never built any more. See
[docs/gestures.md](docs/gestures.md), [docs/effects.md](docs/effects.md) and
[docs/sound.md](docs/sound.md).

```
camera -> hand_tracker -> filters/signals -> face (dormant) -> gestures
       -> effects -> sound -> HUD (badge, prompt, jutsu card) -> imshow
```

Effects, sound and HUD are **read-only consumers** of the `GestureReading`: they
can never change a detection, a threshold or a recording. The jutsu card in
particular reads the same reading the effects just used - there is no second
detector anywhere.

## The five jutsus

| Key | Jutsu | How you perform it |
| --- | --- | --- |
| `1` | **RASENGAN** | Open palm facing the camera, then draw **one full circle** with the palm (about 3-4 s). The orb appears in your hand. |
| `2` | **CHIDORI** | Index and middle extended **apart**, ring and pinky folded - hold for 0.50 s. |
| `3` | **FIRE WALL** | Both hands up side by side, **palms open towards the camera**, all five fingers out with a small natural gap - hold it for 0.50 s. The wall stays up for as long as the sign is held. |
| `4` | **WATER WALL** | Open palm held **upright** (fingers up, wrist below) and **still** for 0.80 s. |
| `5` | **LIGHTNING STORM** | Index only, then draw **one small circle** with the fingertip (about a hand span, inside 2 s). Another circle while it is running boosts the storm. |
| `0` | - | Back to LIVE detection (keys `1`...`5` are clearly-labelled simulation) |

Notes that matter in practice:

* Fire Wall is a **two-hand sign**, and it reads each hand on its own: both
  palms facing the camera (`>= 0.35` of the facing cosine), index..pinky plus
  the thumb extended, a fingertip gap of at least `0.12` palm sizes, and all 21
  landmarks inside the frame. The pair then has to stay put (its midpoint must
  drift less than `0.80` palm sizes) for 0.50 s. The back of the hand, a fist,
  fingers squeezed into one blade, a hand half off the frame and a single hand
  all fail one of those gates - none of them has to be recognised as a *wrong*
  gesture, so no other sign is ruled out by mistake.
* A palm held up towards the camera is also the Water Wall pose, so the water
  hold is frozen while the two-hand sign is present; releasing the fire sign
  never raises water instead.
* Nothing else is needed for it: no mouth, no push, no clasp, no key press.
  Once the sign has been stable for 0.50 s the wall rises by itself, stays up
  while both palms stay open, burns down over 0.30 s after the sign breaks and
  re-arms 0.60 s later.
* Chidori and Water Wall are single-hand signs. With two hands on screen the
  recogniser picks the **more expressive** hand, so a second hand cannot break
  a Chidori.
* The storm wants a **small** circle - a big theatrical loop around the whole
  frame is rejected on purpose. It lives for 6 s and every extra circle raises
  the level (rain, wind, debris, strike rate) up to 4; `0` stops the effect
  *and* its ambience.
* Rasengan needs the **palm** to circle; the storm needs the **fingertip** to
  circle. A loop made with an open palm is never a storm.

## The recording view

The window is meant to be filmed, so it shows nothing that a viewer of the clip
does not need:

* **top-right** - `LIVE DETECTION`, `SIMULATION (keyboard)` or `LIVE  * REC`;
* **bottom-left** - two words: `HAND` / `NO HAND` and `SND 70%` / `SND OFF`;
* **bottom-right** - the jutsu card, and only while a jutsu is live or being
  attempted:

```
+----------------------------------+
| [bolt] CHIDORI                   |
| Two fingers out, slightly apart. |
| Hold the sign to fire lightning. |
+----------------------------------+
```

`[bolt]` is a small vector glyph per jutsu (a sphere, a bolt, a flame, a drop, a
cloud). `cv2.putText` with the Hershey fonts cannot draw emoji at all - anything
outside ASCII comes out as `?` - so the brief's emoji became glyphs and `360°`
became `360`.

| Jutsu | Line 1 | Line 2 | Line 3 |
| --- | --- | --- | --- |
| Rasengan | `RASENGAN` | Open palm, draw a full circle. | One full turn of the palm. |
| Chidori | `CHIDORI` | Two fingers out, slightly apart. | Hold the sign to fire lightning. |
| Fire Wall | `FIRE WALL` | Both palms open, facing the camera. | Hold both hands to raise the wall. |
| Water Wall | `WATER WALL` | Upright open palm, held still. | Keep steady to raise the wall. |
| Lightning Storm | `LIGHTNING STORM` | Extend only your index finger. | Draw a small circle to summon it. |

The wording follows the recognisers, not the other way round: Chidori says
*apart* because the two fingertips must be `>= 0.12` palm sizes apart, Fire Wall
says *both palms open, facing the camera* because that is the whole gate, and
Water Wall says *upright and still* and never mentions the palm facing the
camera, because nothing gates on that.

The card is driven by `reading.state` first (which includes the state a `1`...`5`
key simulated - that *is* the jutsu on screen), then by the same per-frame flags
the gates read (`chidori_shape`, `fire.locked`, an open palm with a started
circle, a started water hold, a storm circle or a running storm). Two open palms
preempt the single-hand attempts - they also read as an upright palm and as the
Rasengan pose, so without that the card could never name them. If two *other*
attempts are live at once the card **shows nothing**, because a wrong jutsu name
is worse than no name. After the pose goes away the card holds for
`HUD_CARD_HOLD_S` (0.9 s) and then fades over `HUD_CARD_FADE_S` (0.3 s), so one
dropped landmark frame cannot make it blink.

`H` hides or shows all of it. `--hud-details` brings back the old full panel
(FPS, palm coordinates, every gate, the key hints) for calibration, including
the Fire Wall rows: `fire hands N left OK right OK`, `ext`/`spc` per hand,
`palm L/R`, `stab` and `hold`, `ready`/`locked` and a `why:` row naming the
first gate that rejected the sign ("left fingers folded", "right palm away",
...). That row is the first thing to read when the wall will not fire.

## Controls

| Key | Action |
| --- | --- |
| `Q` / `Esc` | Quit and release the camera |
| `H` | Show / hide the overlay (badge, recording prompt, jutsu card) |
| `G` | Export the raw-vs-filtered signal graph to `outputs/` |
| `R` | Start a guided recording session (`P` pauses it) |
| `1` ... `5` | Keyboard **simulation** of Rasengan / Chidori / Fire Wall / Water Wall / Lightning Storm |
| `0` | End the simulation, back to LIVE |
| `E` | Visual effects on / off |
| `S` | Sound on / off (independent of `E`) |
| `+` (`=`) / `-` | Volume up / down in 10 % steps |

Simulation keys are ignored while a recording is running, so a recorded take can
never contain a forced state.

## Install and run

The project is **not** an installed package. It expects this layout (Python
3.10, macOS):

```bash
cd /Users/apple/NINJA_VISION
.venv/bin/python run.py
```

Full setup from scratch, if `.venv` does not exist yet:

```bash
python3.10 -m venv .venv
.venv/bin/python -m pip install -U pip setuptools wheel
.venv/bin/python -m pip install --no-deps mediapipe==0.10.14   # skips jax/jaxlib
.venv/bin/python -m pip install -r requirements.txt
```

`mediapipe==0.10.14` is pinned on purpose: 0.10.18+ removed the legacy
`mp.solutions` API the project uses, and NumPy must stay `< 2.0` for the
OpenCV/MediaPipe C extensions. Both models (hands, face landmarks) ship inside
the wheel - nothing is downloaded at run time.

### Command-line options

| Flag | Meaning |
| --- | --- |
| `--no-effects` | Start with the visual effects off (`E` toggles them live) |
| `--no-sound` | Start silently; no audio device is opened at all |
| `--no-face` | Kept for compatibility: the FaceMesh is never built any more, so this flag only stops the stage being reported as enabled |
| `--no-hud` | Start with the overlay hidden |
| `--hud-details` | Draw the full status panel instead of the clean card |
| `--seconds N` | Auto-stop after N seconds (smoke test) |
| `--export-on-exit` | Write `outputs/signals_<stamp>.png` when the session ends |
| `--record` / `--record-*` | Guided recording protocols (NEUTRAL, CHIDORI, RASENGAN) |
| `--evaluate <stamp>` | Re-score a stored session with the current `config.py`, no camera |

The shutdown printout shows per-stage timings (`track`, `face`, `gesture`,
`effects`, `sound`, `hud`), the effects state, the adaptive quality level and
the frame count.

## Tests

```bash
.venv/bin/python -m unittest discover -s tests -v
```

**344 tests, all passing** (`Ran 344 tests ... OK`, 20-35 s depending on how
busy the laptop is), with no camera,
no window and no audio device:

| Module | Tests | Covers |
| --- | --- | --- |
| `test_effects.py` | 42 | Phase 4 effects, anchors, pools, adaptive quality, `E`/`1`/`2`/`0` |
| `test_gestures.py` | 73 | Phase 3 recognisers (Chidori, Rasengan, Water Wall) |
| `test_info_overlay.py` | 54 | Phase 8 card content, selection, hold/fade, ambiguity, bottom-right geometry, pixels at 320/640/1280, `H`, `--hud-details`, card budget |
| `test_phase6.py` | 40 | Water Wall picture, cue edges/loops, the twenty WAVs, keys, HUD |
| `test_phase7.py` | 84 | Fire Wall open-palm sign recognition and sound, Lightning Storm circle and sound, two-hand tracking and `primary_hand`, app wiring, config guards |
| `test_phase7_effects.py` | 32 | Fire Wall and storm pixels, cloud/wind/rain motion, full-frame compositing, particle caps, budgets, buffer reuse |
| `test_sound.py` | 36 | Mixer, cue state machine, toggles, missing device and corrupt assets |

The suite that inspects pixels hands the layer a **fresh copy of the source
frame** each time, exactly like the camera does - a repeated blend on one array
would compound the sky and test a bug the app cannot have.

Four of the budget assertions are wall-clock measurements. Each of them measures
**three independent passes** and asserts on the best median / p95 pair: a real
regression is slow in all three, while an IDE, a browser or the window server
taking one slice of CPU can no longer turn a green suite red. The thresholds
were not touched, and a thermal throttle (the 2018 MBP drops to
`CPU_Speed_Limit 46` after a long benchmark) still fails the suite - correctly,
because the picture really would not fit then.

## Performance

Measured headless on the target machine (Intel i7-8750H, 8 GB, macOS, 640x480):

| Stage | Median | p95 |
| --- | --- | --- |
| Hand tracking (`process_both`, two-hand graph, blank frame) | 13.1-13.4 ms | 15.1-15.3 ms |
| FaceMesh (dormant: exists, never built) | 0.000 ms | 0.000 ms |
| Gesture recogniser, one hand (Chidori / Water Wall / storm) | 0.054 ms | 0.063 ms |
| Gesture recogniser, two hands (Fire Wall sign) | 0.124 ms | 0.135 ms |
| Effects: Rasengan / Chidori | 1.47 / 1.08 ms | 1.95 / 1.43 ms |
| Effect: Fire Wall | 2.0-2.4 ms | 2.5-3.1 ms |
| Effect: Water Wall | 1.8-2.1 ms | 2.7-3.5 ms |
| Effect: Lightning Storm, level 1 / maximum stage | 1.7-2.3 / 3.2 ms | 4.0-5.6 / 6.3 ms |
| Sound director (storm running) | 0.009 ms | 0.013 ms |
| Jutsu card (bottom-right, 640x480) | 0.6 ms | 0.7 ms |
| Clean HUD (strip + card) | 0.97 ms | 1.16 ms |
| Detailed panel (`--hud-details`) | 1.78 ms | 2.52 ms |

Practical notes for this hardware:

* **Two hands cost one graph pass, not two.** `HandTracker.process_both()` calls
  MediaPipe once with `max_num_hands=2` and returns 0, 1 or 2 hands, so a second
  hand adds no tracker call at all; the recognisers then see the same
  `HandResult` objects they always did.
* The effects stay under ~15 % of the MediaPipe frame budget. The storm is the
  most expensive picture because it is a full-frame pass (2.3 ms at level 1,
  3.2 ms at the maximum stage) and the Fire Wall is a bounded region pass
  (2.4 ms). Ranges are repeated runs - an 8 GB laptop is not a quiet benchmark
  box. Those numbers come from an idle desktop; with an IDE and a browser open
  the same benchmark roughly doubles (tracker 24-25 ms, Fire Wall 4.1-4.5 ms,
  storm 3.9-5.7 ms), which is why the layer lowers its particle quality when
  the FPS drops.
* The FaceMesh is never built, so the old mouth stage costs exactly nothing and
  no reading can switch it on. `--no-face` is still accepted.
* `EffectLayer` steps its own quality down (`1.0 -> 0.6 -> 0.35`) when the
  measured FPS stays under 26 and back up above 29, which scales particle
  spawn rates without touching any recogniser.
* All particles live in fixed-capacity pools - the wall's embers, smoke and
  tongues are three separate capped pools, the storm's rain is one preallocated
  `260 x 5` array, its dust and leaves are pools, its bolts are capped at 5 with
  3 painted - and the storm's sky buffers are allocated once per resolution, so
  nothing large is allocated per frame.
* The clean HUD costs *less* than the panel it replaced (0.97 vs 1.78 ms): the
  card darkens its own ~210x75 box through a cached rounded mask and a
  pre-allocated scratch buffer, so a steady frame allocates nothing. Its text
  size, box, mask and subtitle positions are computed once per (jutsu, frame
  size) and cached on the overlay instance.

## Known limitations

* Geometry is 2D: a hand strongly edge-on can read as folded fingers.
* Fire Wall measures each hand on its own (all five digits extended, palm
  facing the camera, a fingertip gap, all 21 landmarks inside the frame) and
  then asks the pair not to move for 0.50 s. The back of the hand, a fist,
  fingers pressed into one blade, a hand half off the frame and a single hand
  all fail on purpose. It does *not* ask the hands to touch, to be a particular
  distance apart, or to be the same size on screen - everything is measured in
  each hand's own palm size.
* The wall survives a 0.30 s tracking dropout (`FIRE_WALL_RELEASE_S`) and then
  re-arms 0.60 s later, so two signs in quick succession count as one.
* Lightning Storm rejects circles larger than 1.60 palm sizes and loops slower
  than 2 s, and a pause while drawing restarts the measurement from the pause.
* The storm darkens the whole frame by design, but its sky blend is capped at
  `STORM_CLOUD_ALPHA` (0.62) and re-applied to a fresh capture every frame, so
  the feed - and the face, the hand and the jutsu card - always stay visible
  underneath.
* Storm intensity is raised by drawing **another circle while it is running**,
  bounded at level 4; there is no separate gesture and no manual slider.
* No heat-haze refraction on the Fire Wall: a per-frame remap of the whole frame
  does not fit the 25-30 FPS budget on this machine. The embers and the swaying
  tongues carry the motion instead.
* Sound is coarse on purpose: one master volume, no positional audio, and no
  thunder for dim flickers (`SOUND_THUNDER_MIN_GAIN`).
* Guided recording still covers `NEUTRAL`, `CHIDORI` and `RASENGAN` only, and
  the CSV columns are unchanged; Fire Wall, Water Wall and Lightning Storm are
  live-only (plus simulated). The 86 existing recordings were not touched.
* No screen shake.
* The card can briefly name a jutsu the user is only *starting*: during the
  first ~0.3 s of a Rasengan circle the palm is still an upright steady open
  palm, which is exactly what Water Wall's hold accumulates, so `WATER WALL`
  can show until the circle puts the card on `RASENGAN`. Both are true of the
  recogniser at that instant; the fired state always wins once it fires.
* When two recognisers are visibly trying at once the card goes blank rather
  than guessing. That is deliberate, but it does mean an ambiguous frame shows
  no help at all.

## Layout

```
run.py                 entry point (adds src/ and the root to sys.path)
config.py              every tunable: thresholds, timings, sizes, colours
src/ninja/
  app.py               the loop, keys, simulation, shutdown timings
  camera.py            capture thread
  hand_tracker.py      MediaPipe hands, up to two -> 21 landmarks each
  face_tracker.py      the old gated FaceMesh - kept in the tree, never built
  filters.py           smoothing (palm centre, landmarks)
  signals.py           signal buffer for the graph export
  gestures.py          the five recognisers, the open-palm Fire Wall measure, live/sim state
  gesture_recorder.py  guided recording sessions and offline re-scoring
  hud.py               clean strip, mode badge, recording prompt, detailed panel
  info_overlay.py      the bottom-right jutsu card (Phase 8)
  effects/             base.py, layer.py, rasengan, chidori, fire_wall,
                       water_wall, lightning_storm, particles, sprites, sound
tests/                 the unittest suite, no camera needed
tools/                 make_sounds.py (regenerate assets), diagnose_env.py
assets/sounds/         20 original WAVs (16-bit PCM, 44.1 kHz, mono)
outputs/               exported graphs; gesture_recordings/ is real session data
docs/                  gestures.md, effects.md, sound.md
```

`outputs/gesture_recordings/` holds the recorded sessions and their metadata.
They are measurement data, not build artefacts - do not delete or rewrite them.
