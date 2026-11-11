// Command Center chart clip tracker. Pure rules on top of ClipStatus (clipstatus.js); the page and the tests share them.
// Status words are only: confirmed, pending, failed, unknown. Confirmed needs evidence: a clipper report that says done
// with clips, and Buffer saying sent for every channel.
(function(root){
const CS=(typeof module!=="undefined"&&module.exports)?require("./clipstatus.js"):root.ClipStatus;
const ROOM_START=18*60,ROOM_END=23*60+59,CLOSE=16*60,STALE_MS=3*3600e3;
// NYSE full-day closures (same list as the Command Center)
const HOLIDAYS=new Set(["2026-01-01","2026-01-19","2026-02-16","2026-04-03","2026-05-25","2026-06-19","2026-07-03","2026-09-07","2026-11-26","2026-12-25",
  "2027-01-01","2027-01-18","2027-02-15","2027-03-26","2027-05-31","2027-06-18","2027-07-05","2027-09-06","2027-11-25","2027-12-24"]);
const isTradingDay=day=>CS.isWeekday(day)&&!HOLIDAYS.has(day);
const prevDay=day=>{const x=new Date(day+"T12:00:00Z");x.setUTCDate(x.getUTCDate()-1);return x.toISOString().slice(0,10)};
// The clip room: the top-up keeps 6:00 PM to 11:59 PM ET free for the clipper (Buffer pacing quiet hours).
function inClipRoom(iso){const p=CS.etParts(iso);return isTradingDay(p.day)&&p.min>=ROOM_START&&p.min<=ROOM_END}
function ctx(day,now,buffer){return {day,now,buffer,endMin:ROOM_END}}
function clipDay(nowIso){let d=CS.etDay(nowIso);while(!isTradingDay(d))d=prevDay(d);return d}
function recentDays(day,n){const out=[];let d=day;while(out.length<n){if(isTradingDay(d))out.unshift(d);d=prevDay(d)}return out}
function reportedIds(run){const s=new Set();for(const c of (run&&run.clips)||[])for(const id of Object.values(c.posts||{}))if(id)s.add(id);return s}
function pickPosts(posts,day,run){const ids=reportedIds(run);return (posts||[]).filter(p=>ids.has(p.id)||(CS.etDay(p.dueAt)===day&&inClipRoom(p.dueAt)))}
function dayWord(creation,channelWords){
  const all=[creation].concat(channelWords);
  if(all.includes("failed"))return "failed";
  if(creation==="confirmed"&&channelWords.every(w=>w==="confirmed"))return "confirmed";
  if(all.includes("pending"))return "pending";
  if(creation==="unknown"&&channelWords.every(w=>w==="confirmed"))return "pending";
  return "unknown";
}
function jobLine(run,day,nowIso){
  const word=CS.creationWord(run,{now:nowIso});
  if(!run){const before=Date.parse(nowIso)<CS.etInstant(day,CLOSE);return {word,text:before?"Starts after the close":"No report from the clipper yet"}}
  const st=String(run.status||"").toLowerCase(),msg=run.message?String(run.message):"";
  if(st==="done"){const n=(run.clips||[]).length;return {word,text:n?`Done · ${n} clip${n>1?"s":""} made`:"Done · but no clips made"}}
  if(st==="failed")return {word,text:"Failed"+(msg?" · "+msg:"")};
  if(word==="unknown")return {word,text:"Last report over 3 hours ago"};
  return {word,text:(st==="queued"?"Queued":"Working")+(msg?" · "+msg:"")};
}
function dayStatus(posts,run,day,nowIso,buffer){
  const c=ctx(day,nowIso,buffer),clips=CS.groupClips(pickPosts(posts,day,run),run);
  const creation=CS.creationWord(run,{now:nowIso});
  const channels=CS.CHANNELS.map(ch=>({ch,...CS.channelSummary(clips,ch,c)}));
  const rows=clips.map(k=>({id:k.id,title:k.title,dueAt:k.dueAt,grade:(k.report&&k.report.grade)||"",tickers:k.tickers,words:Object.fromEntries(CS.CHANNELS.map(ch=>[ch,CS.channelWord(k,ch,c)]))}))
    .sort((a,b)=>(Date.parse(a.dueAt||"")||Infinity)-(Date.parse(b.dueAt||"")||Infinity));
  return {day,creation,made:run&&run.clips?run.clips.length:null,channels,rows,word:dayWord(creation,channels.map(x=>x.word)),job:jobLine(run,day,nowIso)};
}
const api={inClipRoom,ctx,clipDay,recentDays,pickPosts,dayWord,jobLine,dayStatus,isTradingDay};
if(typeof module!=="undefined"&&module.exports)module.exports=api;else root.ClipTracker=api;
})(this);
