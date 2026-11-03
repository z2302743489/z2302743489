# v11 — denser MMA exchanges

The built-in image generation tool authored 24 additional complete poses using
the approved v7 fighter as the identity, costume and pixel-art reference. The
full prompt is in `PROMPT.txt`; `mma-sheet.png` preserves the original output.
No bitmap limbs are stretched to create kicks, knees or wrestling actions.

The new poses cover shin checks, low kicks, teeps, clinch entries, knees, level
changes, double-leg entries, lifts, drives, top control, ground punches, sprawls,
defensive ground guard and a technical stand-up. All 24 cells share one physical
scale, including the crouching and grounded figures.

The bout has 51 scored exchanges in about 30 seconds (v10 had 31 exchanges in
about 29 seconds). It includes a robot clinch trip, defensive sprawl, a player
double-leg takedown, top-control short punches, a robot roll escape and technical
stand-ups. The robot can also deploy an articulated low kick. The player still
wins at 12% health after a final defensive counter sequence.

Support trainers are measured in `supports.json`. Low kicks and knees pivot on
the lead-foot contact; teeps load the rear-foot contact. Whole authored frames
are translated onto that fixed contact between pose changes. The v10 planted
advance/retreat steps and fixed-length robot arms are retained. The new robot
leg is another fixed-length two-joint SVG chain.

Build:

- Optional source extraction: `python scripts/prepare_mma_v11.py` (Pillow).
- Build the self-contained animation: `python3 scripts/build_fight_v11.py`
  (standard library only; imports the v9 and v10 render helpers).

The builder stages earlier templates in temporary directories; it does not
overwrite the previously published SVGs. `bout.json` records the full timeline,
damage outcomes, wrestling passages, footwork and preview moments. The final
`assets/fight-hero-v11.svg` embeds every used sprite and needs no JavaScript or
external image fetches. Unused source poses remain available in this folder but
are omitted from the embedded SVG to reduce its size.
