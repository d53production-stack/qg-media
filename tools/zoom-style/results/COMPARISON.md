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

