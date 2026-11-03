# v14 — neck lock, flowing fall and dazed victory

The built-in image generation tool edited the seated human's arms into a rear
naked choke and authored four bridge inbetweens. `PROMPT.txt` preserves both
prompts. `choke-source.png` and `fall-sheet.png` are the original outputs;
`choke.png` and `fall-0.png` through `fall-3.png` are transparent web exports.
The last two bridge inbetweens are used in the final animation. `review.png`
shows the exports, including the two shoes in each pose.

The robot remains the original v9bot group with the same head/body bitmaps and
fixed-length articulated arms. In the neck lock, its short connector directly
under the monitor meets the newly bent choking forearm. The assisting arm is
behind the monitor. It releases after the tap.

The suplex now samples a rigid falling/rotating path every 16 ms, then makes a
small damped rebound without scaling or squashing the robot. Human bridge
inbetweens accompany the descent. A continuous roll carries the bot into
seated back control instead of jumping from the landing position. `bout.json`
records those samples and the timeline.

Pain begins at mat contact: tightly squeezed eyes, a trembling mouth and a
small cyan sweat pixel. The victorious ending changes to a dazed expression,
with four gold pixel stars emerging around the screen face, flashing and
drifting upward. These are code-native SVG details attached to the same robot,
so their positions follow its head through the ending.

Build:

    python scripts/prepare_finish_v14.py  # optional source export; Pillow
    python3 scripts/build_finish_v14.py  # standard-library SVG builder

The earlier builders and replacement source poses are staged in temporary
folders. Previously published versions are preserved. `fight-hero-v14.svg`
embeds all assets, with no JavaScript or external image requests. Static
snapshots under `verification/v14/` sample the actual animation tracks.
