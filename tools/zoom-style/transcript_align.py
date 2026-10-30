#!/usr/bin/env python3
"""Tie every zoom to the sentence being said, using the Zoom .vtt transcripts.

The highlight clips are cut from the full webinar recording, so clip time
maps to recording time with one unknown offset per clip.  The burned-in
captions (read by caption_ocr.py) are matched to transcript cues by their
words; each match votes for an offset and the densest cluster wins.  With that offset each move is given the cue that is active when it
starts, plus the neighbouring cues, and the result is written back into the
analysis JSON (`align` on the clip, `transcript` on each move).

    python3 transcript_align.py analysis/ vtt/ [--md zoom-sentences.md]

Clip names start with the webinar date (2026-10-28-...); the .vtt files carry
it in the Zoom name (GMT20261028-...).  Clips without a transcript are skipped.
"""
import argparse
import glob
import json
import os
import difflib
import re
import sys
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from profile import classify_move  # noqa: E402

TOK = re.compile(r"[a-z0-9']+")
MIN_SUPPORT = 4    # captions that agree on the offset
MIN_SHARE = 0.4    # ... as a share of the captions that matched anything
CLUSTER_S = 4.0    # captions agreeing within this are one offset


def toks(text):
    return TOK.findall(text.lower().replace("’", "'"))


def tok_eq(a, b):
    if a == b:
        return True
    if len(a) < 4 or len(b) < 4:
        return False
    return difflib.SequenceMatcher(None, a, b).ratio() >= 0.8


def find_runs(cap, cue_toks):
    """Longest run of caption tokens found in order in the cue (fuzzy).  Returns (run, first_index)."""
    best, best_i = 0, None
    for i in range(len(cue_toks)):
        if not tok_eq(cap[0], cue_toks[i]) and not any(tok_eq(cap[k], cue_toks[i]) for k in range(min(2, len(cap)))):
            continue
        # align greedily from here
        j, k, run = i, 0, 0
        while j < len(cue_toks) and k < len(cap):
            if tok_eq(cap[k], cue_toks[j]):
                run += 1
                j += 1
                k += 1
            elif k + 1 < len(cap) and tok_eq(cap[k + 1], cue_toks[j]):
                k += 1
            else:
                j += 1
                if j - i > len(cap) + 3:
                    break
        if run > best:
            best, best_i = run, i
    return best, best_i


def match_caption(cap_text, cues, index):
    """Candidate (recording_time, cue_i) for one OCR'd caption, or None."""
    cap = [t for t in toks(cap_text) if len(t) >= 2]
    if len(cap) < 3:
        return None
    cands = Counter()
    for t in cap:
        for ci in index.get(t, ()):
            cands[ci] += 1
    best = None
    for ci, n in cands.most_common(12):
        if n < 2:
            break
        ct = cues[ci]["toks"]
        run, i = find_runs(cap, ct)
        need = 3 if len(cap) >= 4 else len(cap)
        if run >= need and (best is None or run > best[0]):
            c = cues[ci]
            frac = i / max(1, len(ct))
            best = (run, c["start"] + frac * (c["end"] - c["start"]), ci)
    if best is None:
        return None
    return best[1], best[2], best[0]


def align(captions, cues, index):
    """captions: [{t, text}] from caption_ocr.py.

    Matt's reels are chronological with cuts, so the clip maps to the
    recording through a few segments, each with its own offset and the
    offsets increasing.  Each caption that matches a cue votes (clip t,
    recording t); consecutive votes that agree within CLUSTER_S form a
    segment.  Returns {"ok", "segments": [{t0, t1, offset, n}], ...}.
    """
    votes = []
    for cp in captions:
        if not cp["text"]:
            continue
        m = match_caption(cp["text"], cues, index)
        if m:
            votes.append({"t": cp["t"], "offset": m[0] - cp["t"], "cue": m[1], "run": m[2]})
    n_text = sum(1 for cp in captions if cp["text"])
    if len(votes) < 2:
        return {"ok": False, "reason": "too few matches", "matched": len(votes), "captions": n_text}
    segs = []
    for v in votes:
        if segs and abs(v["offset"] - np.median([x["offset"] for x in segs[-1]])) <= CLUSTER_S / 2:
            segs[-1].append(v)
        else:
            segs.append([v])
    # a lone vote is kept only if it sits between its neighbours in time (chronological cuts)
    kept = []
    for i, sg in enumerate(segs):
        off = float(np.median([x["offset"] for x in sg]))
        if len(sg) >= 2:
            kept.append({"t0": sg[0]["t"], "t1": sg[-1]["t"], "offset": round(off, 2), "n": len(sg)})
            continue
        prev_off = max((float(np.median([x["offset"] for x in p])) for p in segs[:i] if len(p) >= 2), default=None)
        next_off = min((float(np.median([x["offset"] for x in p])) for p in segs[i + 1:] if len(p) >= 2), default=None)
        if (prev_off is None or off > prev_off) and (next_off is None or off < next_off):
            kept.append({"t0": sg[0]["t"], "t1": sg[-1]["t"], "offset": round(off, 2), "n": 1})
    # drop segments that run backwards in the recording
    mono = []
    for sg in kept:
        if mono and sg["offset"] < mono[-1]["offset"] - 1.0:
            if sg["n"] > mono[-1]["n"]:
                mono[-1] = sg
            continue
        mono.append(sg)
    used = sum(sg["n"] for sg in mono)
    ok = used >= MIN_SUPPORT and used / len(votes) >= MIN_SHARE
    return {"ok": bool(ok), "segments": mono, "matched": len(votes), "used": used,
            "captions": n_text, "share": round(used / len(votes), 2)}


def offset_at(segments, t):
    """Recording offset for clip time t: the segment covering t, else the nearest one."""
    for sg in segments:
        if sg["t0"] - 1.5 <= t <= sg["t1"] + 1.5:
            return sg["offset"], True
    best = min(segments, key=lambda sg: min(abs(t - sg["t0"]), abs(t - sg["t1"])))
    return best["offset"], False


def parse_vtt(path):
    cues = []
    with open(path, encoding="utf-8", errors="replace") as f:
        block = []
        for line in f.read().splitlines() + [""]:
            if line.strip():
                block.append(line)
                continue
            if any("-->" in b for b in block):
                tl = next(b for b in block if "-->" in b)
                a, b = [x.strip() for x in tl.split("-->")]
                text = " ".join(block[block.index(tl) + 1:]).strip()
                m = re.match(r"([^:]{1,40}):\s*(.*)", text)
                speaker, words = (m.group(1), m.group(2)) if m else ("", text)
                cues.append({"start": ts(a), "end": ts(b), "speaker": speaker, "text": words})
            block = []
    return cues


def ts(s):
    h, m, rest = s.split(":")
    return int(h) * 3600 + int(m) * 60 + float(rest)


def vtt_date(path):
    m = re.search(r"GMT(\d{4})(\d{2})(\d{2})", os.path.basename(path))
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None


def cue_at(cues, t):
    """Index of the cue active at recording time t, else the latest one started before t."""
    best = None
    for i, c in enumerate(cues):
        if c["start"] <= t:
            best = i
        else:
            break
    return best


def attach(d, cues, index):
    segs = d["align"]["segments"]
    for mv in d["moves"]:
        offset, sure = offset_at(segs, mv["start"])
        # the words on screen at the move decide between neighbouring segments
        m = match_caption(mv.get("caption_text", ""), cues, index)
        direct = None
        if m:
            own = m[0] - mv["start"]
            near = [sg for sg in segs if abs(sg["offset"] - own) <= CLUSTER_S]
            if near:
                offset, sure = near[0]["offset"], True
                direct = m[1]           # the words on screen are in this very cue
        t = mv["start"] + offset
        i = direct if direct is not None else cue_at(cues, t)
        if i is None:
            mv["transcript"] = None
            continue
        c = cues[i]
        mv["transcript"] = {
            "recording_t": round(t, 2),
            "cue_i": i,
            "sure": sure,
            "direct": direct is not None,
            "speaker": c["speaker"],
            "text": c["text"],
            "into_cue_s": round(t - c["start"], 2),
            "cue_dur": round(c["end"] - c["start"], 2),
            "in_gap": t > c["end"] + 0.2,
            "prev": cues[i - 1]["text"] if i > 0 else "",
            "next": cues[i + 1]["text"] if i + 1 < len(cues) else "",
        }
    # the cues spoken over the clip (for word baselines)
    idx = set()
    for sg in segs:
        a, b = sg["t0"] + sg["offset"] - 2, sg["t1"] + sg["offset"] + 2
        idx.update(i for i, c in enumerate(cues) if c["end"] >= a and c["start"] <= b)
    d["align"]["cues"] = sorted(idx)
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("analysis_dir")
    ap.add_argument("vtt_dir")
    ap.add_argument("--md", help="write a per-clip listing of moves and sentences")
    ap.add_argument("--json", help="write the alignment summary here")
    args = ap.parse_args()

    vtts = {}
    for p in sorted(glob.glob(os.path.join(args.vtt_dir, "*.vtt"))):
        day = vtt_date(p)
        if day:
            cues = parse_vtt(p)
            index = defaultdict(set)
            for i, c in enumerate(cues):
                c["toks"] = toks(c["text"])
                for t in c["toks"]:
                    index[t].add(i)
            vtts[day] = (cues, index)
            print(f"{day}: {len(cues)} cues from {os.path.basename(p)}", file=sys.stderr)

    summary = {"clips": {}, "aligned": 0, "skipped_no_vtt": 0, "failed": 0}
    md = []
    for f in sorted(glob.glob(os.path.join(args.analysis_dir, "*.json"))):
        d = json.load(open(f))
        clip = d["clip"]
        day = clip[:10]
        if day not in vtts:
            summary["skipped_no_vtt"] += 1
            continue
        captions = d.get("captions")
        if not captions:
            summary["failed"] += 1
            d["align"] = {"ok": False, "reason": "no OCR captions (run caption_ocr.py)"}
            json.dump(d, open(f, "w"), indent=1)
            continue
        cues, index = vtts[day]
        res = align(captions, cues, index)
        d["align"] = res
        if res.get("ok"):
            summary["aligned"] += 1
            attach(d, cues, index)
            segtxt = ", ".join(f"{sg['t0']:.0f}-{sg['t1']:.0f}s -> +{sg['offset']:.0f}s" for sg in res["segments"])
            md.append(f"\n## {clip}  ({len(res['segments'])} segment(s): {segtxt})\n")
            for mv in d["moves"]:
                k = classify_move(mv, d["holds"], d["duration"])
                if k == "template" or not mv.get("transcript"):
                    continue
                tr = mv["transcript"]
                z = f"{mv['zoom_from']:.2f}->{mv['zoom_to']:.2f}" if mv.get("zoom_from") and mv.get("zoom_to") else ""
                on_screen = mv.get("caption_text", "")
                md.append(f"- **{mv['start']:5.1f}s {k:8s}** {z:11s} on screen: \"{on_screen}\" | {tr['speaker']}: {tr['text']}  _(+{tr['into_cue_s']:.1f}s into cue)_")
        else:
            summary["failed"] += 1
            for mv in d["moves"]:
                mv.pop("transcript", None)
        summary["clips"][clip] = res
        json.dump(d, open(f, "w"), indent=1)
        print(f"{clip}: {res}", file=sys.stderr)

    print(json.dumps({k: v for k, v in summary.items() if k != "clips"}, indent=1))
    if args.json:
        json.dump(summary, open(args.json, "w"), indent=1)
    if args.md:
        with open(args.md, "w") as out:
            out.write("# Every move, with the sentence being said\n\nClip time, move kind, zoom level before -> after (widest hold of the clip = 1.0), then the transcript cue active at that moment.\n")
            out.write("\n".join(md) + "\n")


if __name__ == "__main__":
    main()
