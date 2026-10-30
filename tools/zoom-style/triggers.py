#!/usr/bin/env python3
"""What is being said when Matt zooms in, zooms out, or pans.

Needs the `transcript` fields written by transcript_align.py.

    python3 triggers.py analysis/ > triggers.json
    python3 triggers.py analysis/ --md > TRIGGERS.md
"""
import argparse
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from profile import classify_move, pct  # noqa: E402
from transcript_align import parse_vtt, vtt_date, toks  # noqa: E402

# word families a human editor (or Claude) might treat as a cue to move the frame
FAMILIES = {
    "ticker": r"\b(spx|spy|qqq|iwm|dia|es|nq|vix|nvda|tsla|aapl|msft|amzn|meta|googl?|amd|btc|eth|gold|oil|tlt|dxy)\b",
    "price level": r"\b\d{2,5}(\.\d+)?\b",
    "pointing (here / this / look)": r"\b(right here|over here|here|this one|this|that one|look at|look|see|notice|watch)\b",
    "chart structure (primary / major / value / magnet)": r"\b(primary|major|minor|value|magnet|box|boxed|range|level|zone|trim|wick|gap|trend ?line|support|resistance|trap ?door|launch ?pad|roll ?up|pin|pinning|pinned)\b",
    "drawing (draw / pencil / line)": r"\b(draw|drawing|drew|pencil|line|lines|mark|circle|arrow|highlight)\b",
    "direction (up / down / break)": r"\b(up|down|higher|lower|break|breaks|breaking|breakout|flip|flips|fail|fails|hold|holds|holding|bounce|push|pull ?back)\b",
    "time (today / tomorrow / open)": r"\b(today|tomorrow|yesterday|monday|tuesday|wednesday|thursday|friday|open|close|overnight|premarket|eod|week|weekly|month|monthly)\b",
    "question / aside (okay, questions, so)": r"\b(okay|ok|alright|all right|questions?|anyone|anybody|guys|so|right\?)\b",
    "big picture (overall / big picture / zoom out)": r"\b(overall|big picture|bigger picture|zoom out|wide|whole|entire|context|macro)\b",
}
STOP = set("the a an and or but so to of in on at for with is are was were be been it its it's this that these those we i you he she they them our your my me us do does did doing done gonna going go get got just like kind of right here there now then if what when where which who how not no yes yeah um uh oh okay ok really very can could would should will all some any one two about up down out over into from as by".split())


def fam_hits(text):
    t = text.lower()
    return {k for k, rx in FAMILIES.items() if re.search(rx, t)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("analysis_dir")
    ap.add_argument("vtt_dir")
    ap.add_argument("--md", action="store_true")
    args = ap.parse_args()

    vtts = {}
    for p in sorted(glob.glob(os.path.join(args.vtt_dir, "*.vtt"))):
        day = vtt_date(p)
        if day:
            vtts[day] = parse_vtt(p)

    kinds = ("zoom-in", "zoom-out", "pan")
    by_kind = {k: [] for k in kinds}
    cue_words = Counter()        # words over all cues spoken in aligned clips
    all_cue_ids = set()
    kind_cue_ids = {k: set() for k in kinds}
    screen_words = {k: Counter() for k in kinds}
    cue_fams = Counter()         # families over all those cues
    cue_fams_zoom_in = Counter() # families over cues during which a zoom-in starts
    n_cues = 0
    n_cues_with_zoom_in = 0
    speakers_all = Counter()
    speakers = {k: Counter() for k in kinds}
    clips = 0
    for f in sorted(glob.glob(os.path.join(args.analysis_dir, "*.json"))):
        d = json.load(open(f))
        al = d.get("align") or {}
        if not al.get("ok"):
            continue
        clips += 1
        cues = vtts[d["clip"][:10]]
        for mv in d["moves"]:
            mv["kind"] = classify_move(mv, d["holds"], d["duration"])
        zoom_in_rec_t = [mv["transcript"]["recording_t"] for mv in d["moves"]
                         if mv["kind"] == "zoom-in" and mv.get("transcript")]
        day = d["clip"][:10]
        cue_ids = set(al.get("cues", [])) | {mv["transcript"]["cue_i"] for mv in d["moves"] if mv.get("transcript")}
        for ci in sorted(cue_ids):
            c = cues[ci]
            n_cues += 1
            all_cue_ids.add((day, ci))
            speakers_all[c["speaker"]] += c["end"] - c["start"]
            fams = fam_hits(c["text"])
            cue_fams.update(fams)
            cue_words.update(w for w in set(toks(c["text"])) if w not in STOP and len(w) > 2)
            if any(c["start"] - 0.5 <= t <= c["end"] + 0.5 for t in zoom_in_rec_t):
                n_cues_with_zoom_in += 1
                cue_fams_zoom_in.update(fams)
        for mv in d["moves"]:
            tr = mv.get("transcript")
            if mv["kind"] not in kinds or not tr:
                continue
            on_screen = mv.get("caption_text") or ""
            rec = {
                "clip": d["clip"], "t": mv["start"], "kind": mv["kind"], "ratio": mv.get("zoom_ratio"),
                "speaker": tr["speaker"], "into_cue_s": tr["into_cue_s"], "cue_dur": tr["cue_dur"],
                "on_screen": on_screen, "cue": tr["text"], "sure": tr.get("sure", True),
                "fams_screen": sorted(fam_hits(on_screen)), "fams_cue": sorted(fam_hits(tr["text"])),
            }
            by_kind[mv["kind"]].append(rec)
            kind_cue_ids[mv["kind"]].add((day, tr["cue_i"], tr["text"]))
            speakers[mv["kind"]][tr["speaker"]] += 1
            screen_words[mv["kind"]].update(w for w in set(toks(on_screen)) if w not in STOP and len(w) > 2)

    out = {"clips_aligned": clips, "cues_spoken": n_cues, "cues_with_zoom_in": n_cues_with_zoom_in}
    base_rate = n_cues_with_zoom_in / n_cues if n_cues else 0
    out["zoom_in_rate_per_cue"] = round(base_rate, 3)
    fam_table = []
    for fam in FAMILIES:
        n = cue_fams[fam]
        z = cue_fams_zoom_in[fam]
        fam_table.append({"family": fam, "cues": n, "cues_with_zoom_in": z,
                          "p_zoom_in": round(z / n, 2) if n else None,
                          "lift": round((z / n) / base_rate, 2) if n and base_rate else None,
                          "share_of_zoom_ins": round(z / n_cues_with_zoom_in, 2) if n_cues_with_zoom_in else None})
    out["families"] = fam_table
    for k in kinds:
        recs = by_kind[k]
        out[k] = {
            "n": len(recs),
            "within_1s_of_sentence_start": round(sum(1 for r in recs if r["into_cue_s"] <= 1.0) / len(recs), 2) if recs else None,
            "median_into_cue_s": pct([r["into_cue_s"] for r in recs], 0.5),
            "median_cue_dur": pct([r["cue_dur"] for r in recs], 0.5),
            "speakers": dict(speakers[k].most_common(4)),
            "families_on_screen": dict(Counter(f for r in recs for f in r["fams_screen"]).most_common()),
            "families_in_sentence": dict(Counter(f for r in recs for f in r["fams_cue"]).most_common()),
        }
    # words with the strongest lift in zoom-in / zoom-out sentences vs all sentences (unique sentences)
    def lift_table(kind, min_n):
        ids = kind_cue_ids[kind]
        words = Counter()
        for _, _, text in ids:
            words.update(w for w in set(toks(text)) if w not in STOP and len(w) > 2)
        rows = []
        for w, c in words.items():
            if c >= min_n and cue_words[w] >= min_n:
                rows.append({"word": w, "lift": round((c / len(ids)) / (cue_words[w] / n_cues), 2),
                             "sentences_with_move": c, "all_sentences": cue_words[w]})
        rows.sort(key=lambda r: -r["lift"])
        return rows
    out["zoom_in_words_by_lift"] = lift_table("zoom-in", 6)[:25]
    out["zoom_out_words_by_lift"] = lift_table("zoom-out", 5)[:20]
    out["on_screen_words"] = {k: dict(screen_words[k].most_common(25)) for k in kinds}
    n_zi, n_zo = len(by_kind["zoom-in"]), len(by_kind["zoom-out"])
    speak_total = sum(speakers_all.values())
    out["speaking_time_share"] = {s: round(v / speak_total, 2) for s, v in speakers_all.most_common(5)} if speak_total else {}
    out["examples"] = {k: [{"clip": r["clip"], "t": r["t"], "ratio": r["ratio"], "on_screen": r["on_screen"], "cue": r["cue"]}
                           for r in by_kind[k][:: max(1, len(by_kind[k]) // 12)][:12]] for k in kinds}

    if not args.md:
        print(json.dumps(out, indent=1))
        return
    L = []
    L.append("# What Matt is saying when he moves the frame\n")
    L.append(f"{clips} clips aligned to the Zoom transcripts, {n_cues} transcript sentences spoken over them, "
             f"{n_zi} zoom-ins, {n_zo} zoom-outs, {len(by_kind['pan'])} pans tied to a sentence.\n")
    L.append("## Sentence families and how often a zoom-in lands on them\n")
    L.append(f"Base rate: a zoom-in starts during {out['zoom_in_rate_per_cue']:.0%} of all sentences.\n")
    L.append("| family | sentences | with a zoom-in | P(zoom-in) | lift | share of zoom-ins |\n|---|---|---|---|---|---|")
    for r in sorted(fam_table, key=lambda r: -(r["lift"] or 0)):
        L.append(f"| {r['family']} | {r['cues']} | {r['cues_with_zoom_in']} | {r['p_zoom_in']} | {r['lift']} | {r['share_of_zoom_ins']} |")
    for k in kinds:
        o = out[k]
        L.append(f"\n## {k} ({o['n']})\n")
        L.append(f"- Starts within 1 s of the start of a sentence: {o['within_1s_of_sentence_start']:.0%}; median {o['median_into_cue_s']} s into a sentence that runs {o['median_cue_dur']} s.")
        L.append(f"- Speaker: {o['speakers']}")
        L.append(f"- Families in the words on screen at the move: {o['families_on_screen']}")
        L.append(f"- Families in the sentence: {o['families_in_sentence']}")
    L.append("\n## Words that over-index in zoom-in sentences (lift vs all sentences)\n")
    L.append("| word | lift | zoom-in sentences | all sentences |\n|---|---|---|---|")
    for r in out["zoom_in_words_by_lift"]:
        L.append(f"| {r['word']} | {r['lift']} | {r['sentences_with_move']} | {r['all_sentences']} |")
    L.append("\n## Words that over-index in zoom-out sentences\n")
    L.append("| word | lift | zoom-out sentences | all sentences |\n|---|---|---|---|")
    for r in out["zoom_out_words_by_lift"]:
        L.append(f"| {r['word']} | {r['lift']} | {r['sentences_with_move']} | {r['all_sentences']} |")
    L.append("\n## Words on screen at the moment of the move (most common)\n")
    for k in kinds:
        L.append(f"- {k}: " + ", ".join(f"{w} ({c})" for w, c in out["on_screen_words"][k].items()))
    L.append(f"\nSpeaking time over the aligned clips: {out['speaking_time_share']}\n")
    for k in kinds:
        L.append(f"\n## {k}: a dozen examples\n")
        for e in out["examples"][k]:
            z = f"{e['ratio']:.2f}x" if e["ratio"] else ""
            L.append(f"- {e['clip']} @ {e['t']:.1f}s {z}: on screen \"{e['on_screen']}\"; sentence: {e['cue']}")
    print("\n".join(L))


if __name__ == "__main__":
    main()
