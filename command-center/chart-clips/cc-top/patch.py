#!/usr/bin/env python3
"""Make the Command Center draft with the improved chart clip tracker.
Usage: python3 patch.py <live.html> <out.html>
Reads the live page, never writes it. Each step must match exactly once or the script stops."""
import sys, re, pathlib
here = pathlib.Path(__file__).parent
src, out = sys.argv[1], sys.argv[2]
s = open(src).read()

def once(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit(f"{label}: expected 1 match, found {n}")
    s = s.replace(old, new)

# 1. Move the card to the top of the status stack: under the brief, above Recap Mac.
once('<div id="brief"></div>\n      <div id="air"></div>\n      <div id="studios"></div>\n      <div id="clipcard"></div>',
     '<div id="brief"></div>\n      <div id="clipcard"></div>\n      <div id="air"></div>\n      <div id="studios"></div>', "order")

# 2. Status rules: the clipstatus.js copy with closeOf(ctx), plus cliptracker.js.
a = s.index("// Chart Clips status logic. Pure functions"); b = s.index("})(this);", a) + len("})(this);")
s = s[:a] + (here/"clipstatus.js").read_text().rstrip() + "\n" + (here/"cliptracker.js").read_text().rstrip() + s[b:]

# 3. Card CSS: append after the existing CHART CLIPS rules.
once("@media (max-width:520px){.clc .ag{grid-template-columns:repeat(2,minmax(0,1fr))}}",
     "@media (max-width:520px){.clc .ag{grid-template-columns:repeat(2,minmax(0,1fr))}}\n" + (here/"card.css").read_text().rstrip(), "css")

# 4. Card renderer.
a = s.index("// ---- CHART CLIPS card (preview) ----"); b = s.index("function renderStudios(){", a)
s = s[:a] + (here/"card.js").read_text().rstrip() + "\n\n" + s[b:]

open(out, "w").write(s)
print("ok", len(s), "bytes")
