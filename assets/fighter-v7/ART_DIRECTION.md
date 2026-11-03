# Fighter v7

Generated with the built-in image generation tool, using three stills from the
owner's shadowboxing video as appearance and movement references. The source
video and reference stills are not included in the public repository.

## Prompt / art direction

A transparent 6-column by 4-row sprite sheet containing 24 complete poses of the
same young East Asian man from the supplied references. High-detail arcade
fighting game pixel art, natural 6.5–7 head adult proportions and clean pixel
clusters. Match the lean, long-legged build, youthful angular oval face, black
fringe, black backwards baseball cap and tan adjustment strap. Match the outfit:
loose black long-sleeve crewneck sweatshirt with small off-white chest wordmarks,
black mid-thigh athletic shorts, white ankle socks and pale wheat yellow trainers.
Bare fists. Consistent head size, body scale, clothing and palette in all frames.
Wide orthodox stance facing right, with lead knee bent and rear heel pivoting.
Preserve anatomical limb lengths; use whole-body rotation and weight transfer.
No background, opponents, grid lines, labels, shadows or effects in the sheet.

Pose sequence: guard, compressed guard, jab load, half jab, full jab, jab retract;
cross windup, half cross, full cross, retract, rear-step guard, duck begin;
low slip/roll, rise from slip, hook load, mid hook, hook follow-through, recover;
uppercut load, half uppercut, full rising uppercut, recoil, neutral guard,
understated one-fist salute still facing right.

The straight punches, planted wide stance, hip rotation and defensive rhythm
reference the video. The hook/uppercut and AI impact effects are stylized
extensions, not an exact frame-by-frame tracing of the source clip.

## Build

`python scripts/build_fighter_v7.py` (Pillow required) creates the individual PNG
poses, review sheet, standalone GIF loop, timing manifest and self-contained
`assets/fight-hero-v7.svg`. Every pose uses a single uniform image scale. Only
whole-body translation is animated; no image or limb stretching is used.

The full source sheet retains its original alpha. Export processing removes
near-invisible alpha residue and uses an indexed palette without dithering.
The final SVG embeds every bitmap, so it needs no external image loads or scripts
when GitHub displays it as an image. The existing v6 SVG supplies the unchanged
terminal layout, arena, robot and effect timing.
