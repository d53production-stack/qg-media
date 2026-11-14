// Chart Clips status logic. Pure functions, shared by the monitor page and its tests.
// Status words are only: confirmed, pending, failed, unknown.
(function(root){
const TZ="America/New_York",TICKERS=["SPX","SPY","QQQ"],CHANNELS=["tiktok","instagram","youtube"];
const WIN_START=18*60,WIN_END=21*60+30,STALE_MS=3*3600e3;
function etParts(iso){
  const p=new Intl.DateTimeFormat("en-US",{timeZone:TZ,year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit",weekday:"short",hourCycle:"h23"}).formatToParts(new Date(iso));
  const g=t=>(p.find(q=>q.type===t)||{}).value;
  return {day:`${g("year")}-${g("month")}-${g("day")}`,min:(+g("hour"))*60+(+g("minute")),wd:g("weekday")};
}
function etDay(iso){return etParts(iso).day}
function isWeekday(day){const d=new Date(day+"T12:00:00Z").getUTCDay();return d>0&&d<6}
function inWindow(iso){const p=etParts(iso);return isWeekday(p.day)&&p.min>=WIN_START&&p.min<=WIN_END}
// UTC instant of an ET wall-clock time on a given day
function etInstant(day,min){
  const guess=Date.parse(day+"T00:00:00Z")+min*60e3;
  const off=(()=>{const p=etParts(new Date(guess).toISOString());const back=Date.parse(p.day+"T00:00:00Z")+p.min*60e3;return back-guess})();
  return guess-off;
}
function windowEnd(day){return etInstant(day,WIN_END)}
function windowStart(day){return etInstant(day,WIN_START)}
function tickers(text){const t=String(text||"").toUpperCase();return TICKERS.filter(k=>new RegExp("(^|[^A-Z])\\$?"+k+"(?![A-Z])").test(t))}
function postWord(p){
  if(!p||!p.id)return "unknown";
  const s=String(p.status||"").toLowerCase();
  if(s==="sent")return "confirmed";
  if(s==="scheduled"||s==="sending"||s==="draft"||s==="needs_approval")return "pending";
  if(s==="error")return "failed";
  return "unknown";
}
function captionKey(text){return String(text||"").split(/\n/)[0].replace(/#\S+/g,"").split(/[.!?]/)[0].toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}
// clips: [{id,title,tickers,posts:{channel:post},report?,dueAt}]
function groupClips(posts,report){
  const out=[],byPost=new Map();
  for(const c of (report&&report.clips)||[]){
    const clip={id:c.id,title:c.title||c.id,tickers:TICKERS.filter(k=>[].concat(c.ticker||[]).map(x=>String(x).toUpperCase()).includes(k)||tickers(c.title).includes(k)),posts:{},report:c,key:captionKey(c.caption||c.title),dueAt:c.dueAt||null};
    for(const [ch,pid] of Object.entries(c.posts||{}))byPost.set(pid,{clip,ch});
    out.push(clip);
  }
  const byKey=new Map(out.filter(c=>c.key).map(c=>[c.key,c]));
  for(const p of posts||[]){
    let hit=byPost.get(p.id),clip=hit&&hit.clip;
    if(!clip){const k=captionKey(p.text);clip=k&&byKey.get(k);if(!clip){clip={id:"buffer:"+p.id,title:String(p.text||"").split(/\n/)[0],tickers:tickers(p.text),posts:{},report:null,key:k,dueAt:null};out.push(clip);if(k)byKey.set(k,clip)}}
    if(!clip.posts[p.channel])clip.posts[p.channel]=p;
    if(!clip.tickers.length)clip.tickers=tickers(p.text);
    if(!clip.dueAt||p.dueAt<clip.dueAt)clip.dueAt=p.dueAt;
  }
  return out;
}
// A reported clip with no `posts` field was never handed to Buffer (e.g. a test render): no evidence either way.
function sentToBuffer(clip){return !clip.report||clip.report.posts!=null||Object.keys(clip.posts).length>0}
function channelWord(clip,ch,ctx){
  if(ctx.buffer!=="live")return "unknown";
  const p=clip.posts[ch];
  if(p)return postWord(p);
  if(!sentToBuffer(clip))return "unknown";
  return Date.parse(ctx.now)<=windowEnd(ctx.day)?"pending":"failed";
}
function channelSummary(clips,ch,ctx){
  const s={total:(clips||[]).length,count:0,confirmed:0,pending:0,failed:0,unknown:0,word:"unknown"};
  let missing=0;
  for(const c of clips){if(!c.posts[ch]){if(c.report&&sentToBuffer(c))missing++;continue}s.count++;s[postWord(c.posts[ch])]++}
  if(ctx.buffer!=="live"){s.word="unknown";return s}
  const open=Date.parse(ctx.now)<=windowEnd(ctx.day);
  s.missing=missing;
  if(!s.count&&!missing){s.word=open?"pending":"unknown";return s}
  s.word=(s.failed||(missing&&!open))?"failed":(s.pending||s.unknown||missing)?"pending":"confirmed";
  return s;
}
function creationWord(rep,ctx){
  if(!rep)return "unknown";
  const st=String(rep.status||"").toLowerCase();
  if(st==="failed")return "failed";
  if(st==="done")return ((rep.clips||[]).length?"confirmed":"failed");
  if(st==="queued"||st==="working"){const u=Date.parse(rep.updatedAt||"");return (u&&Date.parse(ctx.now)-u<=STALE_MS)?"pending":"unknown"}
  return "unknown";
}
function filterTicker(clips,t){return !t||t==="ALL"?clips:clips.filter(c=>c.tickers.includes(t))}
const api={TZ,TICKERS,CHANNELS,etParts,etDay,isWeekday,inWindow,windowStart,windowEnd,tickers,postWord,captionKey,groupClips,sentToBuffer,channelWord,channelSummary,creationWord,filterTicker};
if(typeof module!=="undefined"&&module.exports)module.exports=api;else root.ClipStatus=api;
})(this);
