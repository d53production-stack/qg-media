# Proof promo template

Turns one proof screenshot (a leaderboard, a payout, a tweet) into the full QuantGeeks promo set, the way the bricks × Lucid Trading post was built:

- Twitter/X 1600×900 in three layouts: **mirror** (card left, copy right), **split** (copy left, card right) and **band** (headline across the top)
- Instagram Story 1080×1920, with everything inside y 250–1580
- Instagram landscape 1080×566 in the same three layouts
- an overview sheet of all of them

It follows the promo playbook and the Lucid promo design rules in qg-command (`reference/promo-playbook`, `reference/lucid-promo-design-rules`): the proof is shown whole and never cropped, retouched or upscaled; only glow outlines, tags and dimming (no darker than 60%) go on top; QuantGeeks appears only outside the proof, as the tool the trader uses; the logo is the official `Quant Geeks-Logo-v2.svg` in `assets/`.

## Make a new post

1. Copy `posts/2026-10-bricks-lucid/` to a new folder, for example `posts/2026-11-<who>-<platform>/`.
2. Put the full, uncropped screenshot in it as `proof.png`.
3. Edit `post.json` (fields below). Measure the two focus boxes in the screenshot's own pixels.
4. Run `python3 build_promo.py posts/<folder>`, or add `x`, `story` or `ig` to make just those sizes.
5. The images land in `posts/<folder>/out/`. Without a `proof.png` it renders a labelled placeholder so you can check the layout; those files end in `-PLACEHOLDER`.

## post.json

| Field | What it is |
|---|---|
| `name` | Prefix for the output file names |
| `proof`, `proof_size` | Screenshot file name and its exact size in pixels (the build stops if they don't match) |
| `source_label` | Neutral credit on the card's top edge, naming the platform |
| `kicker` | Green mono line, `> PLATFORM'S RESULT` |
| `headline` | Two lines, white; auto-shrinks to fit |
| `stats` | 2–4 figures copied exactly from the proof; `"green": true` for the money figure |
| `signoff` | Muted line above the logo, such as `BRICKS TRADES WITH` |
| `hero` | Main highlight: `box` [left, top, right, bottom], `tag` text, `tag_align` left or right, `ring` false to drop the second ring |
| `secondary` | Optional gold highlight: `box`, `tag`, and `tag_x` (where the tag's centre sits, in screenshot pixels; put it in an empty gap) |
| `dim` | Brightness outside the focus areas, 0.6 to 1 |

## What's kept out of git

Screenshots and renders are binaries, so `.gitignore` keeps every PNG and JPG out of this repo (it is public hosting for Buffer). Keep the proof and finished images in Drive or the project folder.

## Needs

Python 3 with Pillow and cairosvg (`pip install pillow cairosvg`), and the fonts Inter Display ExtraBold and DejaVu Sans Mono Bold (installed, or dropped in a `fonts/` folder here).
