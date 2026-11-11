// ---- CHART CLIPS tracker (top of Today) ----
// Rules: ClipTracker (cliptracker.js, tests in qg-media command-center/chart-clips/cc-top). Data: clips/<day> (the clipper's report,
// mirrored from the Clip Monitor) + the Buffer posts this page already reads. The card only reads; it never touches Buffer or the clipper.
const CLIP_MONITOR='https://claude.ai/artifact/W6Tu8vrSJ5JD6SSa8bCfgd';
const CLIP_HEAD={confirmed:"all posted",pending:"in progress",failed:"needs a look",unknown:"no word yet"};
function renderClipCard(){
  const el=$("clipcard"),CS=window.ClipStatus,T=window.ClipTracker;if(!el||!CS||!T)return;
  const nowIso=new Date().toISOString(),day=T.clipDay(nowIso),B=LIVE.buffer,bst=B.state==="live"?"live":"error";
  const tz=(S.home&&S.home.tz)||"America/Los_Angeles";
  const tm=iso=>{const t=Date.parse(iso||"");return t?new Date(t).toLocaleTimeString("en-US",{timeZone:tz,hour:"numeric",minute:"2-digit"}):""};
  const posts=(B.posts||[]).filter(p=>p.source==="buffer").map(p=>({id:p.id,channel:String(p.channel||"").toLowerCase(),status:p.status,text:p.text,dueAt:p.dueAt,media:p.media,error:p.error}));
  const runOf=d=>(S.clipRuns&&S.clipRuns.get(d))||null;
  const run=runOf(day),st=T.dayStatus(posts,run,day,nowIso,bst);
  const isToday=day===CS.etDay(nowIso),dl=new Date(day+"T12:00:00Z").toLocaleDateString("en-US",{weekday:"short",month:"short",day:"numeric",timeZone:"UTC"}).toUpperCase();
  const waiting=!run&&st.word==="pending";
  const head=`Chart clips · ${isToday?"tonight":dl} · ${waiting?"waiting for the clipper":CLIP_HEAD[st.word]}`;
  const when=run&&run.updatedAt?`<span class="when">REPORTED ${esc(tm(run.updatedAt).toUpperCase())}</span>`:`<span class="when">NO REPORT YET</span>`;
  const lab={tiktok:"TIKTOK",instagram:"INSTAGRAM",youtube:"YOUTUBE"},ab={tiktok:"TT",instagram:"IG",youtube:"YT"};
  const pips=s=>{const n=Math.max(s.total,s.count);if(!n)return"";const w=st.rows.map(r=>r.words[s.ch]);return `<div class="pips" style="grid-template-columns:repeat(${w.length},1fr)">${w.map(x=>`<i class="${x}"></i>`).join("")}</div>`};
  const opens=Date.parse(nowIso)<CS.windowStart(day);
  const cells=[`<div class="ac"><span class="tn">CREATED</span><span class="n">${st.made==null||(!st.made&&st.creation!=="failed")?"&ndash;":st.made}</span><b class="${st.creation}">${st.creation.toUpperCase()}</b><span class="x" title="${esc(st.job.text)}">${esc(st.job.text)}</span></div>`]
    .concat(st.channels.map(s=>`<div class="ac"><span class="tn">${lab[s.ch]}</span><span class="n">${s.count}<small>/${s.total}</small></span>${pips(s)}<b class="${s.word}">${s.word.toUpperCase()}</b><span class="x">${bst!=="live"?"Buffer not read":s.count?`${s.confirmed} posted · ${s.pending} queued${s.failed?" · "+s.failed+" failed":""}`:opens?"room opens "+esc(tm(new Date(CS.windowStart(day)).toISOString())):"none in Buffer"}</span></div>`)).join("");
  const rows=st.rows.length?`<div class="cl">${st.rows.map(r=>{const bad=Object.values(r.words).includes("failed");return `<div class="cr${bad?" failed":""}"><span class="tm">${esc(tm(r.dueAt))||"&ndash;"}</span><span class="tt" title="${esc(r.title)}">${esc(r.title)}${r.grade?`<small>${esc(r.grade)}</small>`:""}</span><span class="chs">${CS.CHANNELS.map(ch=>`<i class="${r.words[ch]}" title="${lab[ch]}: ${r.words[ch]}">${ab[ch]}</i>`).join("")}</span></div>`}).join("")}</div>`:"";
  const hist=T.recentDays(day,5).map(d=>{const w=d===day?st.word:T.dayStatus(posts,runOf(d),d,nowIso,bst).word;const c={confirmed:"ok",failed:"miss",pending:"pend",unknown:"unk"}[w];const lbl=new Date(d+"T12:00:00Z").toLocaleDateString("en-US",{weekday:"short",month:"short",day:"numeric",timeZone:"UTC"});return `<i class="${c}${d===day?" now":""}" title="${esc(lbl)}: ${w}"></i>`}).join("");
  el.innerHTML=`<div class="clc${st.word==="failed"?" bad":st.word==="unknown"?" stale":""}" role="region" aria-label="Chart clips"><div class="ah"><span class="eyebrow">${esc(head)}</span>${when}</div><div class="ag">${cells}</div>${rows}<div class="cf"><span class="hist">LAST 5 DAYS <span class="dots">${hist}</span></span><a href="${CLIP_MONITOR}" target="_blank" rel="noopener">WATCH &amp; CHECK &#8599;</a></div></div>`;
}
