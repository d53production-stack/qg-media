# Matt's zoom style, measured from the highlight clips

97 clips, 73.2 minutes, 720 holds. A hold is a stretch where the video window sits still; a move is the cut or the short animated ramp between two holds. Zoom is relative to the widest hold in the same clip (1.0x = the widest view that clip ever shows). Template slide-ins and the end card are excluded.

## Pace

- Moves per minute of video: median 9.38 (middle half 7.09 to 12.24, n=97)
- Hold length: median 3.8s (middle half 2.2 to 6.5s, n=720), one in ten over 11.02s
- Zoomed holds (>= 1.15x): median 3.4s (middle half 2.1 to 5.4s, n=417)
- Wide holds: median 4.7s (middle half 2.3 to 9.5s, n=301)

## How much and how tight

- Share of the clip spent zoomed in: median 0.46 (middle half 0.27 to 0.59, n=97)
- Clips that open already zoomed in: 0.33
- First zoom arrives at median 3.0s (middle half 0.6 to 8.7s, n=89); 8 clips never zoom
- Zoom level when zoomed: median 1.55x (middle half 1.44 to 1.66x, n=417), tightest 2.298x
- Zoom level histogram over all holds: {'1.0-1.15': 301, '1.15-1.4': 61, '1.4-1.6': 201, '1.6-1.9': 145, '1.9-2.5': 10}

## How the moves are made

- Move kinds: {'zoom-in': 233, 'zoom-out': 218, 'pan': 119, 'nudge': 34, 'cut': 15, 'unknown': 2}
- Animated moves last median 0.3s (middle half 0.2 to 0.3s, n=570)
- Zoom-in step: median 1.52x (middle half 1.36 to 1.63x, n=233); zoom-out step: median 0.66x (middle half 0.62 to 0.71x, n=218)
- Most common move sequences: {'zoom-out > zoom-in': 132, 'zoom-in > zoom-out': 125, 'zoom-in > pan': 57, 'pan > zoom-out': 57, 'pan > pan': 34, 'zoom-in > zoom-in': 20, 'zoom-out > zoom-out': 14, 'nudge > zoom-in': 11}

## Where the zoom lands (position of the zoomed view inside the clip's widest frame)

- middle-right: 125
- middle-center: 99
- middle-left: 79
- top-right: 37
- bottom-right: 19
- top-center: 18
- top-left: 17
- bottom-left: 14
- bottom-center: 9

## By webinar date

| date | clips | zoomed holds | zoom level | zoomed share | moves/min | ramp length |
|---|---|---|---|---|---|---|
| 2026-10-07 | 2 | 6 | 1.48x | 0.42 | 7.9 | 0.55s |
| 2026-10-08 | 5 | 5 | 1.39x | 0.18 | 5.6 | 0.2s |
| 2026-10-14 | 12 | 29 | 1.54x | 0.38 | 7.2 | 0.3s |
| 2026-10-15 | 8 | 43 | 1.52x | 0.46 | 12.05 | 0.2s |
| 2026-10-19 | 16 | 61 | 1.59x | 0.42 | 9.2 | 0.3s |
| 2026-10-21 | 12 | 64 | 1.54x | 0.41 | 10.05 | 0.3s |
| 2026-10-22 | 12 | 56 | 1.5x | 0.48 | 8.55 | 0.2s |
| 2026-10-26 | 10 | 40 | 1.55x | 0.46 | 7.6 | 0.3s |
| 2026-10-27 | 12 | 67 | 1.59x | 0.66 | 11.0 | 0.3s |
| 2026-10-28 | 8 | 46 | 1.53x | 0.53 | 9.75 | 0.3s |

## Per clip

| clip | s | holds | moves/min | zoomed share | max zoom | opens zoomed | first zoom s | moves | unresolved |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-07-webinar-part2 | 45.4 | 6 | 7.3 | 0.53 | 2.298 | no | 4.2 | {'zoom-in': 4, 'zoom-out': 1} | 0 |
| 2026-10-07-webinar-part3 | 25.7 | 4 | 8.5 | 0.31 | 1.351 | no | 2.4 | {'zoom-in': 2, 'zoom-out': 1} | 0 |
| 2026-10-08-webinar-part1-v | 33.7 | 5 | 7.1 | 0.2 | 1.305 | no | 13.0 | {'pan': 1, 'zoom-in': 1, 'zoom-out': 1, 'nudge': 1} | 0 |
| 2026-10-08-webinar-part2-v | 36.2 | 5 | 7.5 | 0.18 | 1.399 | no | 20.7 | {'pan': 1, 'zoom-in': 2, 'zoom-out': 1} | 0 |
| 2026-10-08-webinar-part3-v | 46.1 | 4 | 3.9 | 0.0 | 1.05 | no | None | {'pan': 1, 'nudge': 2} | 0 |
| 2026-10-08-webinar-part4-v | 28.2 | 3 | 5.6 | 0.64 | 1.414 | yes | 0.2 | {'zoom-out': 1, 'zoom-in': 1} | 0 |
| 2026-10-08-webinar-part5-v | 41.0 | 2 | 1.5 | 0.0 | 1.0 | no | None | {'pan': 1} | 0 |
| 2026-10-14-webinar-b-part1 | 37.67 | 6 | 9.0 | 0.39 | 1.44 | no | 5.5 | {'zoom-in': 2, 'pan': 1, 'zoom-out': 2} | 0 |
| 2026-10-14-webinar-b-part2 | 53.47 | 11 | 12.2 | 0.37 | 1.773 | no | 10.5 | {'zoom-in': 4, 'zoom-out': 3, 'nudge': 1, 'pan': 1, 'cut': 1} | 0 |
| 2026-10-14-webinar-b-part3 | 37.03 | 5 | 7.4 | 0.44 | 1.586 | yes | 0.6 | {'pan': 2, 'zoom-out': 1, 'cut': 1} | 0 |
| 2026-10-14-webinar-b-part4 | 28.27 | 4 | 7.6 | 0.3 | 1.671 | no | 3.5 | {'zoom-in': 1, 'zoom-out': 1, 'cut': 1} | 0 |
| 2026-10-14-webinar-b-part5 | 49.37 | 9 | 10.7 | 0.63 | 1.683 | yes | 0.6 | {'nudge': 1, 'zoom-out': 3, 'zoom-in': 3, 'pan': 1} | 0 |
| 2026-10-14-webinar-b-part6 | 31.43 | 4 | 6.7 | 0.12 | 1.474 | no | 11.6 | {'zoom-in': 2, 'zoom-out': 1} | 0 |
| 2026-10-14-webinar-b-part7 | 33.63 | 5 | 8.2 | 0.57 | 1.489 | no | 5.9 | {'zoom-in': 1, 'pan': 2, 'zoom-out': 1} | 0 |
| 2026-10-14-webinar-b-part8 | 38.77 | 5 | 7.0 | 0.4 | 1.672 | no | 4.9 | {'zoom-in': 2, 'zoom-out': 2} | 0 |
| 2026-10-14-webinar-b-part9 | 39.57 | 5 | 6.8 | 0.59 | 1.605 | yes | 0.6 | {'pan': 1, 'zoom-out': 2, 'zoom-in': 1} | 0 |
| 2026-10-14-webinar-part5 | 28.27 | 2 | 2.5 | 0.0 | 1.066 | no | None | {'cut': 1} | 0 |
| 2026-10-14-webinar-part6 | 49.37 | 3 | 2.7 | 0.0 | 1.035 | no | None | {'nudge': 1, 'pan': 1} | 0 |
| 2026-10-14-webinar-part9 | 38.77 | 2 | 1.7 | 0.0 | 1.0 | no | None | {'nudge': 1} | 0 |
| 2026-10-15-webinar-part1 | 49.97 | 13 | 15.8 | 0.47 | 1.767 | no | 3.9 | {'zoom-in': 5, 'zoom-out': 4, 'pan': 3} | 0 |
| 2026-10-15-webinar-part2 | 38.9 | 9 | 14.0 | 0.55 | 1.651 | yes | 0.6 | {'pan': 2, 'cut': 1, 'zoom-in': 3, 'zoom-out': 2} | 0 |
| 2026-10-15-webinar-part3 | 40.3 | 8 | 11.7 | 0.55 | 1.746 | yes | 0.6 | {'zoom-out': 4, 'zoom-in': 3} | 0 |
| 2026-10-15-webinar-part4 | 57.0 | 11 | 11.5 | 0.46 | 1.837 | no | 8.8 | {'zoom-in': 5, 'zoom-out': 5} | 0 |
| 2026-10-15-webinar-part5 | 41.7 | 6 | 8.1 | 0.77 | 2.067 | no | 2.6 | {'zoom-in': 3, 'zoom-out': 2} | 0 |
| 2026-10-15-webinar-part6 | 40.13 | 10 | 15.2 | 0.13 | 1.914 | yes | 0.6 | {'zoom-out': 4, 'nudge': 1, 'zoom-in': 4} | 0 |
| 2026-10-15-webinar-part7 | 42.17 | 7 | 9.5 | 0.37 | 1.701 | yes | 0.6 | {'zoom-out': 3, 'zoom-in': 2, 'nudge': 1} | 0 |
| 2026-10-15-webinar-part8 | 48.6 | 10 | 12.4 | 0.38 | 1.794 | no | 5.8 | {'zoom-in': 4, 'zoom-out': 4, 'pan': 1} | 0 |
| 2026-10-19-webinar-part1 | 27.2 | 6 | 13.2 | 0.61 | 1.652 | yes | 0.6 | {'nudge': 1, 'zoom-out': 2, 'zoom-in': 2} | 0 |
| 2026-10-19-webinar-part10 | 48.1 | 6 | 6.9 | 0.29 | 1.675 | yes | 0.6 | {'zoom-out': 3, 'zoom-in': 2} | 0 |
| 2026-10-19-webinar-part11 | 40.13 | 6 | 8.4 | 0.38 | 1.622 | no | 3.8 | {'zoom-in': 3, 'zoom-out': 2} | 0 |
| 2026-10-19-webinar-part12 | 34.1 | 9 | 16.2 | 0.69 | 1.749 | yes | 0.6 | {'zoom-out': 3, 'zoom-in': 1, 'nudge': 1, 'pan': 3} | 0 |
| 2026-10-19-webinar-part13 | 42.1 | 7 | 9.6 | 0.82 | 1.794 | no | 2.3 | {'zoom-in': 4, 'zoom-out': 2} | 0 |
| 2026-10-19-webinar-part14 | 39.4 | 14 | 22.3 | 0.47 | 1.598 | yes | 0.6 | {'zoom-out': 3, 'nudge': 4, 'zoom-in': 2, 'pan': 2, 'cut': 2} | 0 |
| 2026-10-19-webinar-part15 | 38.03 | 5 | 7.2 | 0.14 | 1.804 | no | 23.0 | {'unknown': 2, 'zoom-in': 1, 'zoom-out': 1} | 2 |
| 2026-10-19-webinar-part16 | 31.07 | 5 | 9.1 | 0.32 | 1.7 | no | 4.8 | {'zoom-in': 1, 'pan': 2, 'zoom-out': 1} | 0 |
| 2026-10-19-webinar-part2 | 41.2 | 4 | 4.9 | 0.28 | 1.893 | yes | 0.6 | {'zoom-out': 1, 'zoom-in': 1, 'cut': 1} | 0 |
| 2026-10-19-webinar-part3 | 47.8 | 7 | 8.3 | 0.67 | 1.685 | no | 10.3 | {'zoom-in': 3, 'zoom-out': 1, 'nudge': 2} | 0 |
| 2026-10-19-webinar-part4 | 37.23 | 6 | 9.3 | 0.87 | 1.702 | yes | 0.6 | {'nudge': 1, 'pan': 1, 'zoom-out': 2, 'zoom-in': 1} | 0 |
| 2026-10-19-webinar-part5 | 38.03 | 5 | 7.2 | 0.81 | 1.784 | yes | 0.6 | {'zoom-in': 2, 'zoom-out': 1, 'cut': 1} | 0 |
| 2026-10-19-webinar-part6 | 28.7 | 6 | 12.4 | 0.36 | 1.629 | yes | 0.6 | {'nudge': 1, 'zoom-out': 2, 'zoom-in': 2} | 0 |
| 2026-10-19-webinar-part7 | 42.63 | 10 | 14.2 | 0.49 | 1.789 | yes | 0.6 | {'zoom-out': 4, 'zoom-in': 4, 'pan': 1} | 0 |
| 2026-10-19-webinar-part8 | 49.03 | 7 | 8.1 | 0.33 | 1.748 | no | 4.0 | {'zoom-in': 2, 'pan': 1, 'zoom-out': 2, 'nudge': 1} | 0 |
| 2026-10-19-webinar-part9 | 34.3 | 7 | 12.1 | 0.25 | 1.604 | no | 9.8 | {'zoom-in': 3, 'zoom-out': 2, 'cut': 1} | 0 |
| 2026-10-21-halloween-qqq-launches-off-the-news-catalyst | 68.6 | 11 | 9.4 | 0.31 | 1.623 | no | 10.3 | {'zoom-in': 4, 'zoom-out': 4, 'nudge': 1, 'pan': 1} | 0 |
| 2026-10-21-halloween-spx-and-qqq-watch-for-a-primary-roll-up | 61.5 | 6 | 5.3 | 0.24 | 1.636 | yes | 0.6 | {'zoom-out': 2, 'zoom-in': 2, 'nudge': 1} | 0 |
| 2026-10-21-halloween-spx-flips-the-trap-door-into-a-launch-pad | 39.7 | 10 | 15.5 | 0.71 | 1.742 | no | 8.7 | {'zoom-in': 2, 'pan': 7} | 0 |
| 2026-10-21-halloween-spx-gets-competitive-at-7-775 | 21.37 | 5 | 14.2 | 0.57 | 1.528 | yes | 0.6 | {'pan': 1, 'zoom-out': 1, 'zoom-in': 1, 'nudge': 1} | 0 |
| 2026-10-21-halloween-spx-shifts-the-primary-up-to-7-770 | 48.03 | 8 | 9.7 | 0.22 | 1.605 | no | 11.1 | {'zoom-in': 3, 'pan': 2, 'zoom-out': 2} | 0 |
| 2026-10-21-halloween-spy-and-qqq-hold-primary-support | 50.47 | 9 | 10.4 | 0.51 | 1.769 | yes | 0.6 | {'pan': 1, 'zoom-out': 4, 'zoom-in': 3} | 0 |
| 2026-10-21-webinar-part1 | 39.7 | 10 | 15.5 | 0.71 | 1.742 | no | 8.7 | {'zoom-in': 2, 'pan': 7} | 0 |
| 2026-10-21-webinar-part2 | 50.47 | 9 | 10.4 | 0.51 | 1.769 | yes | 0.6 | {'pan': 1, 'zoom-out': 4, 'zoom-in': 3} | 0 |
| 2026-10-21-webinar-part3 | 48.03 | 8 | 9.7 | 0.22 | 1.605 | no | 11.1 | {'zoom-in': 3, 'pan': 2, 'zoom-out': 2} | 0 |
| 2026-10-21-webinar-part4 | 61.5 | 6 | 5.3 | 0.24 | 1.636 | yes | 0.6 | {'zoom-out': 2, 'zoom-in': 2, 'nudge': 1} | 0 |
| 2026-10-21-webinar-part5 | 21.37 | 5 | 14.2 | 0.57 | 1.528 | yes | 0.6 | {'pan': 1, 'zoom-out': 1, 'zoom-in': 1, 'nudge': 1} | 0 |
| 2026-10-21-webinar-part6 | 68.6 | 11 | 9.4 | 0.31 | 1.623 | no | 10.3 | {'zoom-in': 4, 'zoom-out': 4, 'nudge': 1, 'pan': 1} | 0 |
| 2026-10-22-halloween-aapl-rejects-at-the-primary | 27.83 | 3 | 2.6 | 0.0 | 1.027 | no | None | {'cut': 1} | 0 |
| 2026-10-22-halloween-spx-and-qqq-roll-the-primary-up-twice | 78.33 | 8 | 5.7 | 0.27 | 1.752 | no | 20.2 | {'zoom-in': 3, 'pan': 1, 'zoom-out': 3} | 0 |
| 2026-10-22-halloween-spx-drops-through-the-trap-door | 76.97 | 17 | 13.2 | 0.59 | 1.68 | no | 4.5 | {'zoom-in': 6, 'zoom-out': 6, 'pan': 3, 'nudge': 1} | 0 |
| 2026-10-22-halloween-spx-sets-up-a-trap-door | 36.63 | 5 | 7.5 | 0.59 | 1.761 | no | 2.6 | {'zoom-in': 2, 'zoom-out': 2} | 0 |
| 2026-10-22-halloween-spy-and-qqq-battle-between-two-primaries | 41.9 | 7 | 9.6 | 0.39 | 1.68 | no | 2.0 | {'zoom-in': 3, 'zoom-out': 2, 'cut': 1} | 0 |
| 2026-10-22-halloween-spy-and-qqq-roll-the-primary-down | 43.3 | 12 | 17.1 | 0.58 | 1.652 | no | 4.5 | {'zoom-in': 5, 'zoom-out': 4, 'pan': 2} | 0 |
| 2026-10-22-webinar-part1 | 76.97 | 17 | 13.2 | 0.59 | 1.68 | no | 4.5 | {'zoom-in': 6, 'zoom-out': 6, 'pan': 3, 'nudge': 1} | 0 |
| 2026-10-22-webinar-part2 | 43.3 | 12 | 17.1 | 0.58 | 1.652 | no | 4.5 | {'zoom-in': 5, 'zoom-out': 4, 'pan': 2} | 0 |
| 2026-10-22-webinar-part3 | 27.83 | 3 | 2.6 | 0.0 | 1.027 | no | None | {'cut': 1} | 0 |
| 2026-10-22-webinar-part4 | 36.63 | 5 | 7.5 | 0.59 | 1.761 | no | 2.6 | {'zoom-in': 2, 'zoom-out': 2} | 0 |
| 2026-10-22-webinar-part5 | 78.33 | 8 | 5.7 | 0.27 | 1.752 | no | 20.2 | {'zoom-in': 3, 'pan': 1, 'zoom-out': 3} | 0 |
| 2026-10-22-webinar-part6 | 41.9 | 7 | 9.6 | 0.39 | 1.68 | no | 2.0 | {'zoom-in': 3, 'zoom-out': 2, 'cut': 1} | 0 |
| 2026-10-26-webinar-part1 | 49.83 | 9 | 10.6 | 0.62 | 1.623 | no | 6.1 | {'zoom-in': 3, 'pan': 2, 'zoom-out': 3} | 0 |
| 2026-10-26-webinar-part10 | 36.3 | 6 | 9.5 | 0.62 | 1.357 | no | 3.1 | {'zoom-in': 2, 'pan': 1, 'zoom-out': 2} | 0 |
| 2026-10-26-webinar-part2 | 50.77 | 11 | 13.1 | 0.45 | 1.855 | no | 2.7 | {'zoom-in': 4, 'pan': 3, 'zoom-out': 3} | 0 |
| 2026-10-26-webinar-part3 | 48.67 | 3 | 2.7 | 0.59 | 1.561 | no | 18.1 | {'zoom-in': 2} | 0 |
| 2026-10-26-webinar-part4 | 78.63 | 9 | 6.5 | 0.12 | 1.547 | no | 5.0 | {'zoom-in': 3, 'zoom-out': 3, 'pan': 2} | 0 |
| 2026-10-26-webinar-part5 | 59.67 | 9 | 8.7 | 0.2 | 1.701 | no | 37.4 | {'zoom-in': 3, 'nudge': 1, 'pan': 2, 'zoom-out': 2} | 0 |
| 2026-10-26-webinar-part6 | 45.9 | 5 | 5.8 | 0.23 | 1.936 | no | 1.3 | {'zoom-in': 2, 'zoom-out': 2} | 0 |
| 2026-10-26-webinar-part7 | 44.83 | 4 | 4.5 | 0.58 | 1.424 | no | 5.7 | {'zoom-in': 2, 'zoom-out': 1} | 0 |
| 2026-10-26-webinar-part8 | 72.93 | 8 | 6.1 | 0.33 | 1.764 | no | 4.2 | {'zoom-in': 3, 'zoom-out': 3, 'pan': 1} | 0 |
| 2026-10-26-webinar-part9 | 64.63 | 10 | 9.0 | 0.48 | 1.817 | no | 17.1 | {'zoom-in': 3, 'pan': 3, 'zoom-out': 3} | 0 |
| 2026-10-27-webinar-part1 | 44.73 | 8 | 10.5 | 0.71 | 1.699 | no | 3.0 | {'zoom-in': 3, 'zoom-out': 2, 'pan': 2} | 0 |
| 2026-10-27-webinar-part10 | 38.43 | 7 | 10.6 | 0.71 | 2.245 | yes | 0.6 | {'zoom-out': 3, 'nudge': 1, 'zoom-in': 2} | 0 |
| 2026-10-27-webinar-part11 | 72.67 | 14 | 11.4 | 0.67 | 2.052 | yes | 0.6 | {'pan': 3, 'zoom-out': 6, 'zoom-in': 4} | 0 |
| 2026-10-27-webinar-part12 | 50.97 | 9 | 10.4 | 0.36 | 1.704 | no | 8.8 | {'zoom-in': 3, 'zoom-out': 4, 'pan': 1} | 0 |
| 2026-10-27-webinar-part2 | 59.07 | 16 | 16.5 | 0.67 | 1.936 | yes | 0.6 | {'pan': 3, 'zoom-out': 8, 'cut': 1, 'zoom-in': 3} | 0 |
| 2026-10-27-webinar-part3 | 52.33 | 11 | 12.6 | 0.6 | 1.594 | yes | 0.6 | {'pan': 4, 'zoom-out': 3, 'zoom-in': 3} | 0 |
| 2026-10-27-webinar-part4 | 48.3 | 10 | 12.4 | 0.71 | 2.124 | yes | 0.6 | {'zoom-out': 3, 'zoom-in': 4, 'pan': 2} | 0 |
| 2026-10-27-webinar-part5 | 49.67 | 5 | 5.3 | 0.73 | 1.562 | no | 11.8 | {'zoom-in': 2, 'zoom-out': 1, 'pan': 1} | 0 |
| 2026-10-27-webinar-part6 | 24.43 | 5 | 12.2 | 0.64 | 1.363 | no | 2.3 | {'zoom-in': 2, 'pan': 1, 'zoom-out': 1} | 0 |
| 2026-10-27-webinar-part7 | 41.97 | 7 | 9.6 | 0.42 | 1.853 | yes | 0.6 | {'zoom-out': 2, 'zoom-in': 2, 'pan': 1, 'nudge': 1} | 0 |
| 2026-10-27-webinar-part8 | 29.77 | 6 | 11.9 | 0.18 | 1.787 | no | 6.7 | {'zoom-in': 2, 'zoom-out': 2, 'nudge': 1} | 0 |
| 2026-10-27-webinar-part9 | 38.37 | 3 | 3.5 | 0.19 | 1.423 | no | 21.0 | {'zoom-in': 1, 'zoom-out': 1} | 0 |
| 2026-10-28-webinar-part1 | 79.07 | 18 | 13.7 | 0.83 | 1.77 | no | 2.4 | {'zoom-in': 4, 'pan': 8, 'zoom-out': 3, 'nudge': 2} | 0 |
| 2026-10-28-webinar-part2 | 54.53 | 8 | 8.4 | 0.6 | 1.786 | yes | 0.6 | {'zoom-out': 3, 'zoom-in': 2, 'pan': 2} | 0 |
| 2026-10-28-webinar-part3 | 89.9 | 12 | 7.7 | 0.57 | 1.707 | yes | 0.6 | {'pan': 2, 'zoom-out': 5, 'zoom-in': 4} | 0 |
| 2026-10-28-webinar-part4 | 19.93 | 3 | 7.9 | 0.0 | 1.004 | no | None | {'pan': 2} | 0 |
| 2026-10-28-webinar-part5 | 55.33 | 7 | 7.1 | 0.49 | 1.635 | no | 18.7 | {'zoom-in': 2, 'zoom-out': 2, 'pan': 2} | 0 |
| 2026-10-28-webinar-part6 | 32.77 | 8 | 14.9 | 0.64 | 1.727 | no | 2.9 | {'zoom-in': 2, 'zoom-out': 2, 'pan': 3} | 0 |
| 2026-10-28-webinar-part8 | 42.37 | 8 | 11.1 | 0.5 | 1.736 | yes | 0.6 | {'pan': 3, 'zoom-out': 2, 'zoom-in': 2} | 0 |
| 2026-10-28-webinar-part9 | 25.27 | 5 | 11.6 | 0.37 | 1.564 | no | 9.9 | {'zoom-in': 2, 'zoom-out': 2} | 0 |

