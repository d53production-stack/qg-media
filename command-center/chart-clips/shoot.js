// Screenshot the monitor with a fake viewer: Buffer posts on Mon evening, a clipper report, one review.
const {chromium}=require("playwright");const fs=require("fs");
(async()=>{
 const html=fs.readFileSync(__dirname+"/clip-monitor.html","utf8");
 const b=await chromium.launch();
 for(const [name,vp] of [["desktop",{width:1200,height:1000}],["phone",{width:400,height:1400}]]){
  const p=await b.newPage({viewport:vp,deviceScaleFactor:1});
  await p.addInitScript(()=>{
   const day="2026-11-06";const mk=(i,ch,st,t,text)=>({node:{id:"6aee"+ch.slice(0,2)+i+"0000000000000000",channelService:ch,status:st,dueAt:t,sentAt:st==="sent"?t:null,text,assets:[{source:"https://example.com/"+i+".mp4"}],error:st==="error"?{message:"Video could not be processed"}:null}});
   const caps=["SPX rolls the primary up to 6,800.","SPY and QQQ battle at the primary.","QQQ squeezes off positive gamma.","SPX hits the trap door.","SPY holds 680 support."];
   const times=["2026-11-06T23:05:00Z","2026-11-06T23:50:00Z","2026-11-07T00:35:00Z","2026-11-07T01:20:00Z","2026-11-07T02:05:00Z"];
   const edges=[];caps.forEach((c,i)=>["tiktok","instagram","youtube"].forEach((ch,j)=>{if(i===4&&ch==="youtube")return;edges.push(mk(i,ch,i===3&&ch==="instagram"?"error":"sent",times[i],c))}));
   const fake={payload:{posts:{edges,pageInfo:{hasNextPage:false}}},cache:{storedAt:Date.now()-4*60e3}};
   const snap=docs=>({docs:docs.map(([id,d])=>({id,data:()=>d}))});
   window.claude={use:async n=>n==="mcp"?{watchTool:(s,t,i,h)=>{setTimeout(()=>h({type:"data",result:fake}),50);return()=>{}},callTool:async()=>fake}:
     n==="db"?{collection:c=>({onSnapshot:f=>{setTimeout(()=>f(snap(c==="runs"?[[day,{status:"done",updatedAt:"2026-11-07T02:10:00Z",message:"5 clips made, 5 scheduled",clips:caps.map((t,i)=>({id:"c"+i,ticker:["SPX","SPY","QQQ","SPX","SPY"][i],title:t,assetId:i<3?"vid"+i:undefined}))}]]:c==="reviews"?[[day+"_c2",{verdict:"flag",note:"Caption cut off",at:new Date().toISOString()}],[day+"_c0",{verdict:"ok",at:new Date().toISOString()}]]:[])),60);return()=>{}}}),doc:()=>({set:async()=>{},delete:async()=>{}})}:
     n==="user"?{id:async()=>"u",can:async()=>true}:null};
  });
  await p.goto("http://127.0.0.1:8765/clip-monitor.html");await p.waitForTimeout(400);await p.evaluate(()=>{const v=document.getElementById("vid");if(v){v.currentTime=4}});await p.waitForTimeout(1500);
  await p.screenshot({path:__dirname+`/shots/monitor-${name}.png`,fullPage:true});
 }
 await b.close();
})();
