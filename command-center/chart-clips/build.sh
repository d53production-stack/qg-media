#!/bin/sh
# Inline clipstatus.js into the page. Output: clip-monitor.html (the published file).
cd "$(dirname "$0")" && python3 - <<'P'
s=open("page.src.html").read();j=open("clipstatus.js").read()
open("clip-monitor.html","w").write(s.replace("/*CLIPSTATUS*/",j))
P
