# v12 — high kick, German suplex, rear naked choke

The built-in image generation tool authored a sixteen-frame paired finisher
sheet using the existing v7 human and the existing CRT robot as references.
The selected sheet is `finish-sheet.png`; the generation prompt is preserved
in `PROMPT.txt`. A targeted background-extraction edit supplied true alpha.
The PNG files `finish-00.png` through `finish-15.png` are the editable exports;
`finish-review.png` is a contact sheet, and `poses.json` records placement.

The two characters share a complete authored frame throughout the finish, so
the rear waist lock, bridge, landing and rear control keep their grips joined.
Extraction applies one uniform physical scale to every cell, including floor
poses. Limbs are never independently stretched or resized. Alpha cleanup and
palette export only remove near-zero alpha and reduce web payload size.

The existing dense MMA bout and planted boxing footwork lead into a high
roundhouse, rear waist lock, German suplex, roll into back control and rear
naked choke. The robot taps the mat, the player releases, and TAP OUT /
SUBMISSION / YOU WIN replace the old knockout ending. There are no further
attacks after the tap. The player wins at 12% health, keeping the earlier
two-way exchanges and difficult comeback.

Rebuild source exports with Pillow:

    python scripts/prepare_finish_v12.py

Build the self-contained SVG with Python's standard library:

    python3 scripts/build_finish_v12.py

The builder stages the v9–v11 renderers in temporary folders and preserves all
previously published assets. It embeds all PNGs into `assets/fight-hero-v12.svg`
and needs no JavaScript or external image fetches. `bout.json` records events,
health, finish order, tap, release and review times. Static review SVGs in
`verification/v12/` sample the same animation tracks used by the live SVG.
