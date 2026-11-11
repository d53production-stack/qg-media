// Screenshots of the chart clip tracker in the Command Center draft. Fake window.claude: db docs + Buffer list_posts.
// Usage: node shoot.js <draft.html> <outDir>. Data: the real Nov 9 and Nov 10 clipper reports (fixtures/), Buffer statuses made up per scenario.
const {chromium}=require("playwright"),fs=require("fs"),path=require("path");
const [,,page_,outDir]=process.argv;
const R9=require("./fixtures/2026-11-09.json"),R10=require("./fixtures/2026-11-10.json");
const SC={
  // Wed Nov 11, 11:05 AM PT: before the close, history from Nov 9/10
  before:{now:"2026-11-11T19:05:00Z",runs:[R9,R10],status:()=>"sent"},
  // Tue Nov 10, 7:00 PM PT (10 PM ET): clips made, 2 posted, last one still queued
  tonight:{now:"2026-11-11T02:00:00Z",runs:[R9,R10],status:(day,id,ch,due)=>Date.parse(due)<Date.parse("2026-11-11T02:00:00Z")?"sent":"scheduled"},
  // same night, Instagram rejected the 7:44 PM ET clip
  bad:{now:"2026-11-11T02:00:00Z",runs:[R9,R10],status:(day,id,ch,due)=>day==="2026-11-10"&&id==="01_call"&&ch==="instagram"?"error":Date.parse(due)<Date.parse("2026-11-11T02:00:00Z")?"sent":"scheduled"},
  // clipper mid-run on Wed Nov 11
  working:{now:"2026-11-11T21:50:00Z",runs:[R9,R10,{day:"2026-11-11",status:"working",updatedAt:"2026-11-11T21:42:00Z",message:"Rendering clip 2 of 3",clips:[]}],status:()=>"sent"},
};
function shim(name){
  const sc=SC[name],NOW=Date.parse(sc.now),edges=[];
  for(const r of sc.runs)for(const c of r.clips||[])for(const [ch,id] of Object.entries(c.posts||{})){
    const due=new Date(c.dueAt).toISOString(),stt=sc.status(r.day,c.id,ch,due);
    edges.push({node:{id,channelService:ch,status:stt,dueAt:due,text:c.caption,assets:[{type:"video",source:"https://x/"+id+".mp4"}],error:stt==="error"?{message:"Video could not be processed"}:null}});
  }
  const C={clips:sc.runs.map(r=>({id:r.day,...r})),studio:[],tasks:[],content:[],projects:[],playbooks:[],suggestions:[],days:[]};
  const D={"settings/home":{tz:"America/Los_Angeles",zip:"95014"}};
  return `(()=>{const RN=${NOW};const _D=Date;class FD extends _D{constructor(...a){super(...(a.length?a:[RN]))}static now(){return RN}}window.Date=FD;
    const D=${JSON.stringify(D)},C=${JSON.stringify(C)};
    const snap=arr=>({docs:arr.map(d=>({id:d.id,data:()=>d}))});
    const coll=name=>({onSnapshot:cb=>{cb(snap(C[name]||[]));return()=>{}},where:()=>coll(name),orderBy:()=>coll(name),limit:()=>coll(name)});
    const db={collection:coll,doc:p=>({onSnapshot:cb=>{const d=D[p];cb({exists:!!d,data:()=>d});return()=>{}}})};
    const buf={payload:{posts:{edges:${JSON.stringify(edges)},pageInfo:{hasNextPage:false}}},cache:{storedAt:RN-3*60e3}};
    const mcp={watchTool:(s,t,i,h)=>{setTimeout(()=>h({type:"data",result:s==="Buffer"?buf:{payload:{data:[]}}}),30);return()=>{}},callTool:async()=>buf,invalidate:async()=>{}};
    window.claude={use:async n=>n==="db"?db:n==="mcp"?mcp:null};})();`;
}
(async()=>{
  const b=await chromium.launch();fs.mkdirSync(outDir,{recursive:true});const errs=[];
  for(const [w,h,tag] of [[1280,900,"desktop"],[390,844,"phone"]])for(const sc of Object.keys(SC)){
    const ctx=await b.newContext({viewport:{width:w,height:h},deviceScaleFactor:2,colorScheme:"dark"});const p=await ctx.newPage();
    p.on("pageerror",e=>errs.push(sc+" "+e));
    await p.addInitScript(shim(sc)+'try{localStorage.setItem("qg.tab","today")}catch(_){}');
    await p.goto("file://"+path.resolve(page_)+"#today",{waitUntil:"load"});
    await p.addStyleTag({content:".tabbar,.toast{display:none!important}"});
    await p.waitForTimeout(1000);
    const r=await p.evaluate(()=>{const a=document.getElementById("clipcard").getBoundingClientRect();return {x:a.left,y:a.top+scrollY,w:a.width,h:a.height,txt:document.getElementById("clipcard").innerText}});
    if(r.h<10){errs.push(sc+" "+tag+" card empty");await ctx.close();continue}
    if(tag==="desktop")console.log("---",sc,"\n"+r.txt.replace(/\n+/g," | "));
    await p.locator("#clipcard").screenshot({path:`${outDir}/${sc}-${tag}.png`});
    if(sc==="tonight"){await p.evaluate(()=>{scrollTo(0,0);document.querySelectorAll("*").forEach(e=>{if(e.scrollTop)e.scrollTop=0})});await p.waitForTimeout(200);}
    if(sc==="tonight")await p.screenshot({path:`${outDir}/today-top-${tag}.png`});
    await ctx.close();
  }
  await b.close();console.log(errs.length?errs.join("\n"):"no page errors");
})();
