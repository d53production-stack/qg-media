# Matt's zoom style vs Claude's default

Matt's numbers are medians over 97 highlight clips (73.2 min). Claude's are the defaults in CLAUDE-DEFAULT-STYLE.md.

| what | Matt (measured) | Claude (default) | read |
|---|---|---|---|
| moves per minute | 9.38 | 8 to 12 | same |
| hold length (s) | 3.8 (p90 11.02) | 4 to 6s | Matt shorter |
| share of time zoomed in | 0.46 | 0.5 to 0.6 | Matt less |
| zoom level when zoomed | 1.55x (middle half 1.44 to 1.66x) | 1.5x | Matt less |
| tightest zoom used | 2.298x | 2.0 to 2.5x |  |
| zoom histogram | {'1.0-1.15': 301, '1.15-1.4': 61, '1.4-1.6': 201, '1.6-1.9': 145, '1.9-2.5': 10} | mostly 1.5x, some 2 to 2.5x |  |
| animated move length (s) | 0.3 | 0.4 to 0.6s | Matt faster |
| clips that open already zoomed | 0.33 | 0 (always open wide) | Matt more |
| first zoom at (s) | 3.0 | 1.5 to 3.0s | same |
| move kinds | {'zoom-in': 233, 'zoom-out': 218, 'pan': 119, 'nudge': 34, 'cut': 15, 'unknown': 2} | zoom-in / zoom-out / pan, no cuts |  |
| zoom-in step | 1.52x | 1.5x from wide, 1.3 to 1.7x again for tight |  |
| zoom-out step | 0.66x | back to wide (0.67x from 1.5x) |  |
| common sequences | {'zoom-out > zoom-in': 132, 'zoom-in > zoom-out': 125, 'zoom-in > pan': 57, 'pan > zoom-out': 57, 'pan > pan': 34, 'zoom-in > zoom-in': 20, 'zoom-out > zoom-out': 14, 'nudge > zoom-in': 11} | in > out > in |  |
| where the zoom lands | {'middle-right': 125, 'middle-center': 99, 'middle-left': 79, 'top-right': 37, 'bottom-right': 19, 'top-center': 18, 'top-left': 17, 'bottom-left': 14, 'bottom-center': 9} | wherever the named thing is |  |

## Does the zoom follow the red ink?

- Zoomed holds with Matt's red ink inside the window: 343 of 392 (0.88)
- Wide holds with red ink on screen (Claude's rules would zoom on these): 122 of 276 (0.44)
- When ink is inside a zoomed hold, its centre sits a median 0.138 of the window away from centre (0 = dead centre, 0.5 = at the edge)


## What is being said when the frame moves (68 clips aligned to the Zoom transcripts)

| what | Matt (measured) | Claude (default) | read |
|---|---|---|---|
| when the zoom-in starts | mid-sentence: 30% within 1 s of the sentence start, median 2.17 s in | at the start of the sentence that names the thing | Matt waits for the noun |
| when the zoom-out starts | at the next sentence: 46% within 1 s of its start | when the topic changes | same idea, Matt is quicker |
| sentences that draw a zoom-in | ticker 1.6x, price level 1.6x, "primary / value / magnet" 1.3x, "here / this / look" 1.3x the base rate | zoom on every "look here" and every new annotation | pointing words are too common to be the trigger; the level or ticker is |
| share of sentences with a zoom-in | 22% | would be higher (every pointing word) | Claude would over-zoom |
| whose words | Chuy, 161 of 162 zoom-ins | the speaker | same |
| spoken drawing cues | 5 sentences in 681 say draw / line / pencil | would wait for them | the pencil is seen, not said: use the ink detector |

The per-move listing is in `zoom-sentences.md`; the aggregates in `TRIGGERS.md` and `triggers.json`.
