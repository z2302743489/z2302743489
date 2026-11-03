# v13 — locomotion, one robot, two shoes

The v12 regression attached both `v9player` / `v9bot` and `v12native`
animations to the same SVG elements. Both declarations used the CSS
`animation` shorthand, so the later opacity animation replaced the actor's
translation and rotation animation. The v13 builder puts visibility on
separate parent groups. Actors retain their single original transform
animation. A build assertion rejects multiple animation controllers on an
element, and verifies the planted advance/retreat paths.

The ending now uses human-only bitmaps. The original `v9bot` SVG group,
original head/body PNGs and fixed-length articulated arms stay in the arena
through the high kick, waist lock, backward bridge, landing, rear control,
tap and release. There is no paired generated robot to swap into the fight.
Only its screen expression changes during the submission. The builder checks
that the original idle PNG and all its attributes equal the v11 version and
that exactly one robot group exists.

The built-in image generation tool edited the v12 sheet to remove every
robot and repair the stray third shoe. `human-sheet.png` preserves the output,
`PROMPT.txt` records the edit, and `human-00.png` through `human-15.png` are its
web exports. All use one physical scale and genuine alpha transparency.
The contact sheet is `human-review.png`. The landing, seated and victory
poses were visually reviewed for exactly two legs and two connected shoes.
SVG clips put only the gripping forearms in front of the native robot; the
human body remains behind it. No limbs are stretched or independently scaled.

Build:

    python scripts/prepare_finish_v13.py  # Pillow; optional source export
    python3 scripts/build_finish_v13.py  # standard library; final animation

The earlier builders are staged in temporary directories. Previous published
SVGs and source metadata are preserved. `bout.json` records the choreography,
the seven planted steps, original-model finishing transforms and checks.
`verification/v13/` contains static samples from the live animation tracks.
The final self-contained SVG is `assets/fight-hero-v13.svg`.
