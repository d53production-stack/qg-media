// Screenshots of the CHART CLIPS card in the Command Center preview. Fake window.claude: db docs + Buffer list_posts.
// Usage: node shoot.js <page.html> <outDir>
const {chromium}=require("playwright"),fs=require("fs"),path=require("path");
const [,,page_,outDir]=process.argv;
// Scenario: Mon Nov 9 2026 at 8:10 PM ET, clipper mid-run.
const NOW=Date.parse("2026-11-10T01:10:00Z");
const day="2026-11-09";
function shim(sc){
  const caps=["SPX rolls the primary up to 6,800.","SPY and QQQ battle at the primary.","QQQ squeezes off positive gamma.","SPX hits the trap door."];
  const t=["2026-11-09T23:05:00Z","2026-11-09T23:50:00Z","2026-11-10T00:35:00Z","2026-11-10T01:20:00Z"];
  const edges=[];
  caps.forEach((c,i)=>["tiktok","instagram","youtube"].forEach(ch=>{
    const st=i<3?"sent":"scheduled";const err=sc==="bad"&&i===2&&ch==="instagram";
    edges.push({node:{id:`6af0${i}${ch.slice(0,2)}00000000000000000`,channelService:ch,status:err?"error":st,dueAt:t[i],text:c,assets:[{type:"video",source:"https://x/"+i+".mp4"}],error:err?{message:"Video could not be processed"}:null}})}));
  const C={clips:sc==="none"?[]:[{id:day,status:"working",updatedAt:new Date(NOW-6*60e3).toISOString(),message:"Made from 4 of Joule's reads",clips:caps.map((c,i)=>({id:"c"+i,ticker:["SPX","SPY","QQQ","SPX"][i],title:c}))}],studio:[],tasks:[],content:[],projects:[],playbooks:[],suggestions:[],days:[]};
  const D={"settings/home":{tz:"America/Los_Angeles",zip:"95014"}};
  return `(()=>{const RN=${NOW};const _D=Date;class FD extends _D{constructor(...a){super(...(a.length?a:[RN]))}static now(){return RN}}window.Date=FD;
    const D=${JSON.stringify(D)},C=${JSON.stringify(C)};
    const snap=arr=>({docs:arr.map(d=>({id:d.id,data:()=>d}))});
    const coll=name=>({onSnapshot:cb=>{cb(snap(C[name]||[]));return()=>{}},where:()=>coll(name),orderBy:()=>coll(name),limit:()=>coll(name)});
    const db={collection:coll,doc:p=>({onSnapshot:cb=>{const d=D[p];cb({exists:!!d,data:()=>d});return()=>{}}})};
    const buf={payload:{posts:{edges:${JSON.stringify(sc==="nobuffer"?[]:edges)},pageInfo:{hasNextPage:false}}},cache:{storedAt:RN-3*60e3}};
    const mcp={watchTool:(s,t,i,h)=>{setTimeout(()=>${sc==="nobuffer"?'h({type:"error",error:{code:"needs_reauth"}})':'h({type:"data",result:s==="Buffer"?buf:{payload:{data:[]}}})'},30);return()=>{}},callTool:async()=>buf,invalidate:async()=>{}};
    window.claude={use:async n=>n==="db"?db:n==="mcp"?mcp:null};})();`;
}
(async()=>{
  const b=await chromium.launch();fs.mkdirSync(outDir,{recursive:true});const errs=[];
  for(const [w,h,tag] of [[1280,900,"desktop"],[390,844,"phone"]])for(const sc of ["ok","bad","nobuffer"]){
    const ctx=await b.newContext({viewport:{width:w,height:h},deviceScaleFactor:2,colorScheme:"dark"});const p=await ctx.newPage();
    p.on("pageerror",e=>errs.push(sc+" "+e));
    await p.addInitScript(shim(sc)+'try{localStorage.setItem("qg.tab","today")}catch(_){}');
    await p.goto("file://"+path.resolve(page_)+"#today",{waitUntil:"load"});
    await p.addStyleTag({content:".tabbar,.toast,.topbar{display:none!important}"});
    await p.waitForTimeout(900);
    const r=await p.evaluate(()=>{const a=document.getElementById("clipcard").getBoundingClientRect();return {x:a.left,y:a.top+scrollY,w:a.width,h:a.height}});
    if(r.h<10){errs.push(sc+" card empty");continue}
    await p.screenshot({path:`${outDir}/clips-${sc}-${tag}.png`,fullPage:true,clip:{x:r.x-8,y:r.y-8,width:r.w+16,height:r.h+16}});
    if(sc==="ok"&&tag==="desktop"){await p.screenshot({path:`${outDir}/today-${tag}.png`});}
    await ctx.close();
  }
  await b.close();console.log(errs.length?errs.join("\n"):"no page errors");
})();
