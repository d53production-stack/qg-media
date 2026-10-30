"""Builds the preview copy of the Command Center with REFRESH buttons on the Recap Mac and Studios cards.
REFRESH starts the hourly copy task now; a card only reads the refresh as done when its own evidence moves.
Each edit must match exactly once in the live source, so a changed live page fails loudly instead of silently.
Usage: python3 patch.py <live.html> <out.html>"""
import sys
src, out = sys.argv[1], sys.argv[2]
html = open(src, encoding="utf-8").read()


def rep(old, new, count=1):
    global html
    n = html.count(old)
    assert n == count, f"expected {count} match(es), found {n} for: {old[:70]!r}"
    html = html.replace(old, new)


# --- CSS: the button sits at the right of each card's header ----------------------
rep('.chip.studio{color:var(--green);border-color:var(--green)}\n',
'''.chip.studio{color:var(--green);border-color:var(--green)}
/* REFRESH on the Recap Mac and Studios headers: starts the hourly copy now */
.air .ah,.sto .ah{align-items:center}
.ahr{display:flex;align-items:center;gap:6px 12px;flex-wrap:wrap;justify-content:flex-end;min-width:0}
.btn.rf{padding:5px 10px;font-size:11px;letter-spacing:.12em;min-height:30px;color:var(--white);border-color:var(--surface)}
.btn.rf:hover{border-color:var(--green);color:var(--green)}
.btn.rf[disabled]{cursor:default;color:var(--grey);border-color:var(--surface)}
.btn.rf[disabled] i{display:inline-block;width:6px;height:6px;margin-right:7px;background:var(--green);vertical-align:1px;animation:rfblink 1.2s steps(2,start) infinite}
@keyframes rfblink{to{visibility:hidden}}
@media (prefers-reduced-motion:reduce){.btn.rf[disabled] i{animation:none}}
.ahw{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:2px 12px;min-width:0}
/* phone: title over the time, the button to the right of both */
@media (max-width:520px){
  .air .ah,.sto .ah{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:4px 12px}
  .ahr{display:contents}
  .ah .eyebrow{grid-column:1;grid-row:1}
  .ahw{grid-column:1;grid-row:2;justify-content:flex-start}
  .btn.rf{grid-column:2;grid-row:1/3;align-self:center}
}
''')

# --- logic: pure, tested by refresh.test.js -----------------------------------------
rep('/* studio-logic:start */\n',
'''/* refresh-logic:start */
/* REFRESH starts the hourly copy now. A card counts the refresh as done only when its evidence moves past what it showed at the
   press: Recap Mac = status/air lastSeen, Studios = newest studio/* checkedAt. No move within REFRESH_WAIT_MS is a failed
   refresh, never confirmed; a failed one stays on the card for REFRESH_SHOW_FAILED_MS after the press. */
const REFRESH_WAIT_MS=5*60e3,REFRESH_SHOW_FAILED_MS=30*60e3;
function airMark(doc){return (doc&&doc.lastSeen)||null}
function studioMark(docs){
  let best=null;
  for(const d of (docs?docs.values():[]))if(d&&d.checkedAt&&(!best||Date.parse(d.checkedAt)>Date.parse(best)))best=d.checkedAt;
  return best;
}
function refreshState(req,mark,nowMs){
  if(!req)return "idle";
  if(nowMs-req.at>REFRESH_SHOW_FAILED_MS)return "idle";
  if(req.err)return "failed";
  const got=Date.parse(mark||""),was=Date.parse(req.mark||"");
  if(got&&(!was||got>was))return "confirmed";
  return nowMs-req.at<REFRESH_WAIT_MS?"pending":"failed";
}
/* refresh-logic:end */
/* studio-logic:start */
''')

rep('function renderAir(){\n',
'''const COPY_TRIGGER="trig_01NU7aWKpkA7LmF3mh6tbz9N",REFRESH_LABEL={air:"Recap Mac",studios:"Studios"};
S.refresh={air:null,studios:null};
const refreshMark=card=>card==="air"?airMark(S.air):studioMark(S.studios);
/* the card's refresh state; a confirmed refresh is cleared on the spot and said once, an expired one just clears */
function refreshNow(card){
  const req=S.refresh[card],st=refreshState(req,refreshMark(card),Date.now());
  if(req&&st==="confirmed"){S.refresh[card]=null;toast(REFRESH_LABEL[card]+" updated")}
  else if(req&&st==="idle")S.refresh[card]=null;
  return {st,why:req&&req.err};
}
function refreshBtn(card,st){
  if(!LIVE.mcp)return "";
  return st==="pending"?`<button class="btn rf" disabled aria-live="polite"><i aria-hidden="true"></i>CHECKING</button>`
    :`<button class="btn rf" data-act="refresh" data-card="${card}" aria-label="Check ${esc(REFRESH_LABEL[card])} now">REFRESH</button>`;
}
function refreshWhen(r,when){
  return `<span class="ahw">${when}${r.st==="failed"?`<span class="when warn">${r.why?"COULDN'T START THE CHECK":"NO NEW REPORT"}</span>`:""}</span>`;
}
/* one run of the hourly copy refreshes both cards, so a press puts both into CHECKING. The copy starts a fresh thread per
   run, and those refuse added text, so it starts bare */
async function refreshRun(){
  if(!LIVE.mcp)return;
  const t=Date.now();
  if(["air","studios"].some(k=>refreshState(S.refresh[k],refreshMark(k),t)==="pending"))return;
  S.refresh={air:{at:t,mark:refreshMark("air"),err:null},studios:{at:t,mark:refreshMark("studios"),err:null}};render();
  try{await LIVE.mcp.callTool("Claude Code Remote","fire_trigger",{trigger_id:COPY_TRIGGER});toast("Checking now. The cards update in a minute or two.")}
  catch(e){
    const why=WEEK_WHY[e&&e.code]||"the check couldn't be started"+(e&&e.code?" ("+e.code+")":"");
    for(const k of ["air","studios"])if(S.refresh[k])S.refresh[k].err=why;
    toast("Couldn't check: "+why);render();
  }
}
document.addEventListener("click",e=>{if(e.target.closest("[data-act=refresh]"))refreshRun()});
function renderAir(){
''')

# --- Recap Mac header ---------------------------------------------------------------
rep('''  el.innerHTML=`<div class="air${cls}" role="region" aria-label="Recap Mac status"><div class="ah"><span class="eyebrow">Recap Mac${probs.length?` · ${probs.length} problem${probs.length>1?"s":""}`:silent?"":" · all good"}</span>${when}</div>''',
'''  const rf=refreshNow("air");
  el.innerHTML=`<div class="air${cls}" role="region" aria-label="Recap Mac status"><div class="ah"><span class="eyebrow">Recap Mac${probs.length?` · ${probs.length} problem${probs.length>1?"s":""}`:silent?"":" · all good"}</span><span class="ahr">${refreshWhen(rf,when)}${refreshBtn("air",rf.st)}</span></div>''')

# --- Studios header -----------------------------------------------------------------
rep('''  el.innerHTML=`<div class="sto${cls}" role="region" aria-label="Studio status"><div class="ah"><span class="eyebrow">${esc(head)}</span>${when}</div>''',
'''  const rf=refreshNow("studios");
  el.innerHTML=`<div class="sto${cls}" role="region" aria-label="Studio status"><div class="ah"><span class="eyebrow">${esc(head)}</span><span class="ahr">${refreshWhen(rf,when)}${refreshBtn("studios",rf.st)}</span></div>''')

open(out, "w", encoding="utf-8").write(html)
print("wrote", out)
