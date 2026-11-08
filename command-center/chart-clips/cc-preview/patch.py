"""Add the CHART CLIPS card to a copy of the live Command Center (preview only).
Usage: python3 patch.py <live.html> <clipstatus.js> <out.html>
The card reads the Buffer posts the page already loads (LIVE.buffer.posts) and the
clipper's run doc clips/<YYYY-MM-DD> in the Command Center db (written by the hourly copy, planned)."""
import sys
live, js, out = sys.argv[1:4]
s = open(live).read(); cs = open(js).read()
MON = "https://claude.ai/artifact/W6Tu8vrSJ5JD6SSa8bCfgd"
def sub(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:60], s.count(a))
    s = s.replace(a, b)
sub('<div id="studios"></div>', '<div id="studios"></div>\n      <div id="clipcard"></div>')
css = """
/* CHART CLIPS card: evening SPX/SPY/QQQ clips, creation (clips/<day>) + Buffer per channel (LIVE.buffer.posts) */
.clc{margin:0 0 16px;border:1px solid var(--surface);border-left:3px solid var(--green);background:var(--panel)}
.clc.bad{border-left-color:var(--rose)}
.clc.stale{border-left-color:var(--grey)}
.clc .ah{display:flex;justify-content:space-between;gap:6px 12px;flex-wrap:wrap;align-items:center;padding:10px 14px 8px}
.clc .ah .eyebrow{font-size:10px}
.clc.bad .ah .eyebrow{color:var(--rose)}
.clc.stale .ah .eyebrow{color:var(--grey)}
.clc .tks{display:flex;border:1px solid var(--surface)}
.clc .tks button{background:none;border:0;border-right:1px solid var(--surface);padding:4px 9px;font-size:10px;font-weight:700;letter-spacing:.1em;color:var(--grey);min-height:30px}
.clc .tks button:last-child{border-right:0}
.clc .tks button[aria-pressed="true"]{background:var(--green);color:var(--bg)}
.clc .ag{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1px;background:var(--divider);border-top:1px solid var(--divider)}
.clc .ac{background:var(--panel);padding:8px 12px;min-width:0;display:flex;flex-direction:column;gap:3px}
.clc .ac .tn{font-size:10px;font-weight:700;letter-spacing:.12em;color:var(--grey)}
.clc .ac .n{font-family:var(--display);font-size:26px;line-height:.9;font-variant-numeric:tabular-nums}
.clc .ac .n small{font-size:15px;color:var(--grey)}
.clc .ac b{font-size:11px;font-weight:800;letter-spacing:.08em}
.clc b.confirmed{color:var(--green)}.clc b.pending{color:var(--white)}.clc b.failed{color:var(--rose)}.clc b.unknown{color:var(--grey)}
.clc .ac span.x{font-size:11px;color:var(--grey);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.clc .pips{display:grid;grid-template-columns:repeat(5,1fr);gap:2px}
.clc .pips i{height:4px;background:var(--surface)}
.clc .pips i.confirmed{background:var(--green)}.clc .pips i.pending{outline:1px solid var(--grey);outline-offset:-1px;background:none}.clc .pips i.failed{background:var(--rose)}
.clc .cf{display:flex;justify-content:space-between;gap:8px 12px;flex-wrap:wrap;padding:7px 14px;border-top:1px solid var(--divider);font-size:11px;color:var(--grey)}
.clc .cf a{color:var(--green);font-weight:700;letter-spacing:.08em;text-decoration:none}
.clc .cf .bad{color:var(--rose)}
@media (max-width:520px){.clc .ag{grid-template-columns:repeat(2,minmax(0,1fr))}}
"""
sub('@media (prefers-reduced-motion:reduce){*{transition:none!important}}\n</style>', css + '@media (prefers-reduced-motion:reduce){*{transition:none!important}}\n</style>')
fn = r"""
// ---- CHART CLIPS card (preview) ----
const CLIP_MONITOR=%r;
let CLIP_TK="ALL";try{CLIP_TK=localStorage.getItem("qg.cliptk")||"ALL"}catch(_){}
function clipDay(){const CS=window.ClipStatus,t=CS.etDay(new Date().toISOString());let d=t;while(!CS.isWeekday(d)){const x=new Date(d+"T12:00:00Z");x.setUTCDate(x.getUTCDate()-1);d=x.toISOString().slice(0,10)}return d}
function renderClipCard(){
  const el=$("clipcard"),CS=window.ClipStatus;if(!el||!CS)return;
  const day=clipDay(),nowIso=new Date().toISOString(),B=LIVE.buffer,bst=B.state==="live"?"live":"error";
  const posts=(B.posts||[]).filter(p=>p.source==="buffer"&&CS.etDay(p.dueAt)===day&&CS.inWindow(p.dueAt)).map(p=>({id:p.id,channel:String(p.channel||"").toLowerCase(),status:p.status,text:p.text,dueAt:p.dueAt,media:p.media,error:p.error}));
  const run=(S.clipRuns&&S.clipRuns.get(day))||null;
  const all=CS.groupClips(posts,run),shown=CS.filterTicker(all,CLIP_TK),ctx={now:nowIso,day,buffer:bst};
  const cw=CS.creationWord(run,{now:nowIso}),made=run&&run.clips?CS.filterTicker(CS.groupClips([],run),CLIP_TK).length:null;
  const sums=CS.CHANNELS.map(ch=>[ch,CS.channelSummary(shown,ch,ctx)]);
  const failed=cw==="failed"||sums.some(([,s])=>s.word==="failed"),allUnknown=cw==="unknown"&&sums.every(([,s])=>s.word==="unknown");
  const isToday=day===CS.etDay(nowIso),dl=new Date(day+"T12:00:00Z").toLocaleDateString("en-US",{weekday:"short",month:"short",day:"numeric",timeZone:"UTC"}).toUpperCase();
  const before=Date.parse(nowIso)<CS.windowStart(day);
  const head=`Chart clips · ${isToday?"tonight":dl}${failed?" · needs a look":""}`;
  const pips=(ch)=>{const c=shown.filter(k=>k.posts[ch]).map(k=>CS.postWord(k.posts[ch]));while(c.length<5)c.push("");return `<div class="pips">${c.slice(0,5).map(w=>`<i class="${w}"></i>`).join("")}</div>`};
  const lab={tiktok:"TIKTOK",instagram:"INSTAGRAM",youtube:"YOUTUBE"};
  const cx=!run?"not reporting yet":run.message||"";
  const cells=[`<div class="ac"><span class="tn">CREATED</span><span class="n">${made==null?"&ndash;":made}</span><b class="${cw}">${cw.toUpperCase()}</b><span class="x" title="${esc(cx)}">${esc(cx)}</span></div>`]
    .concat(sums.map(([ch,s])=>`<div class="ac"><span class="tn">${lab[ch]}</span><span class="n">${s.count}<small>/5</small></span>${pips(ch)}<b class="${s.word}">${s.word.toUpperCase()}</b><span class="x">${bst!=="live"?"Buffer not read":s.count?`${s.confirmed} posted · ${s.pending} queued`:before?"opens 6:00 PM ET":"none in Buffer"}</span></div>`)).join("");
  const tks=["ALL","SPX","SPY","QQQ"].map(t=>`<button type="button" data-cliptk="${t}" aria-pressed="${t===CLIP_TK}">${t}</button>`).join("");
  el.innerHTML=`<div class="clc${failed?" bad":allUnknown?" stale":""}" role="region" aria-label="Chart clips"><div class="ah"><span class="eyebrow">${esc(head)}</span><span class="tks" role="group" aria-label="Ticker">${tks}</span></div><div class="ag">${cells}</div><div class="cf"><span>${shown.length?`${shown.length} clip${shown.length>1?"s":""} · 6:00 to 9:30 PM ET`:"Up to 5 per channel, 6:00 to 9:30 PM ET weekdays"}</span><a href="${CLIP_MONITOR}" target="_blank" rel="noopener">WATCH &amp; CHECK &#8599;</a></div></div>`;
}
document.addEventListener("click",e=>{const b=e.target.closest&&e.target.closest("[data-cliptk]");if(!b)return;CLIP_TK=b.dataset.cliptk;try{localStorage.setItem("qg.cliptk",CLIP_TK)}catch(_){}renderClipCard()});
""" % MON
sub('function renderStudios(){', fn + '\nfunction renderStudios(){')
sub('renderAir();renderStudios();', 'renderAir();renderStudios();renderClipCard();')
sub('  db.collection("studio").onSnapshot(s=>{mapSnap(s,S.studios);S.sready=true;render()},onSubErr);', '  db.collection("studio").onSnapshot(s=>{mapSnap(s,S.studios);S.sready=true;render()},onSubErr);\n  S.clipRuns=new Map();db.collection("clips").onSnapshot(s=>{mapSnap(s,S.clipRuns);render()},onSubErr);')
# clipstatus as its own script before the page script; clip run docs from db collection "clips"
sub('<script>', '<script>\n' + cs + '\n</script>\n<script>', 1) if s.count('<script>')==1 else None
open(out, "w").write(s)
print("ok", len(s))
