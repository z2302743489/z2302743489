# v10 — boxing footwork and a close win

The built-in image generation tool authored the additional footwork sheet using
the accepted v7 fighter as its identity and art-style reference. See `PROMPT.txt`
for the full prompt. `footwork-sheet.png` preserves the original generated image.
The existing punch and defence poses remain v7's authored sprites.

`prepare_footwork_v10.py` extracts cells at one uniform scale, indexes the PNG
palette and measures each trainer's ball-of-foot contact point. It does not
reshape or stretch limbs. `footwork-review.png` marks rear/lead contacts.

The bout uses the clearest stepping poses from the sheet. On advance the rear
foot stays planted during the push, the lead foot lands and the rear follows.
On retreat the lead foot pushes, the rear foot lands and the lead follows.
The support point is held in world space between frame changes. Recovery uses
the original v7 guard to preserve the established stance and appearance.

Robot arms are SVG articulated plates with fixed 40/42-unit bones. The six
attacks are a jab, rear cross, body straight, hook, uppercut and overhand.
The robot lands six punches, leaving the player at 12% HP before the knockout.
The player has 12 explicit advance/retreat steps; the bout lasts 28.81 seconds.
`bout.json` records every step, outcome, health change and preview time.

Build:

1. Optional source re-extraction: `python scripts/prepare_footwork_v10.py`
   (requires Pillow; the extracted PNGs are already included).
2. `python3 scripts/build_fight_v10.py` (standard library only).

The v10 builder imports the v9 renderer and uses the v8 layout as a template in
a temporary staging directory. It never overwrites the published v8 or v9 SVG.
The resulting `assets/fight-hero-v10.svg` embeds all bitmaps and requires no
JavaScript or external images when displayed on GitHub.
