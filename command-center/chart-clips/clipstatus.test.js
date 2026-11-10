// Status logic for the Chart Clips monitor. Run: node --test
const test=require("node:test"),assert=require("node:assert/strict");
const S=require("./clipstatus.js");

// Nov 9 2026 is a Monday; ET = UTC-5 after Nov 1.
const post=(o)=>({id:"p"+Math.random().toString(16).slice(2,8),channel:"tiktok",status:"scheduled",text:"SPX rolls the primary up.",dueAt:"2026-11-09T23:30:00Z",media:"https://x/a.mp4",error:null,...o});

test("evening window is 6:00-9:30 PM ET on weekdays only", ()=>{
  assert.equal(S.inWindow("2026-11-09T23:00:00Z"),true);   // Mon 6:00 PM ET
  assert.equal(S.inWindow("2026-11-10T02:30:00Z"),true);   // Mon 9:30 PM ET
  assert.equal(S.inWindow("2026-11-10T02:31:00Z"),false);  // 9:31 PM
  assert.equal(S.inWindow("2026-11-09T22:59:00Z"),false);  // 5:59 PM
  assert.equal(S.inWindow("2026-11-08T23:30:00Z"),false);  // Sunday
});

test("ET day key follows New York, not UTC", ()=>{
  assert.equal(S.etDay("2026-11-10T02:00:00Z"),"2026-11-09");
});

test("tickers are read from the caption, SPX/SPY/QQQ only", ()=>{
  assert.deepEqual(S.tickers("SPY and QQQ battle at the primary; SPX lags"),["SPX","SPY","QQQ"]);
  assert.deepEqual(S.tickers("AAPL rejects"),[]);
  assert.deepEqual(S.tickers("$spx bounces"),["SPX"]);
});

test("Buffer status maps to the four words", ()=>{
  assert.equal(S.postWord({id:"a",status:"sent"}),"confirmed");
  assert.equal(S.postWord({id:"a",status:"scheduled"}),"pending");
  assert.equal(S.postWord({id:"a",status:"sending"}),"pending");
  assert.equal(S.postWord({id:"a",status:"error"}),"failed");
  assert.equal(S.postWord({id:"a",status:"weird"}),"unknown");
  assert.equal(S.postWord(null),"unknown");
});

test("a post without a Buffer id is never confirmed", ()=>{
  assert.equal(S.postWord({status:"sent"}),"unknown");
});

test("posts of one clip across channels group by caption", ()=>{
  const ps=[post({channel:"tiktok",text:"SPX rolls the primary up. #gex"}),post({channel:"instagram",text:"SPX rolls the primary up!"}),post({channel:"youtube",text:"QQQ holds 710."})];
  const g=S.groupClips(ps,null);
  assert.equal(g.length,2);
  const spx=g.find(c=>c.tickers.includes("SPX"));
  assert.deepEqual(Object.keys(spx.posts).sort(),["instagram","tiktok"]);
});

test("clipper report links posts by post id first", ()=>{
  const a=post({id:"b1",channel:"tiktok",text:"Totally different caption"});
  const rep={status:"done",clips:[{id:"c1",ticker:"SPY",title:"SPY tests 769",posts:{tiktok:"b1"}}]};
  const g=S.groupClips([a],rep);
  assert.equal(g.length,1);assert.equal(g[0].id,"c1");assert.equal(g[0].posts.tiktok.id,"b1");
  assert.deepEqual(g[0].tickers,["SPY"]);
});

test("a reported clip with no Buffer post shows that channel unknown before the window, failed after", ()=>{
  const rep={status:"done",clips:[{id:"c1",ticker:"SPX",title:"x",posts:{}}]};
  const [c]=S.groupClips([],rep);
  assert.equal(S.channelWord(c,"tiktok",{now:"2026-11-09T20:00:00Z",day:"2026-11-09",buffer:"live"}),"pending");
  assert.equal(S.channelWord(c,"tiktok",{now:"2026-11-10T03:00:00Z",day:"2026-11-09",buffer:"live"}),"failed");
  assert.equal(S.channelWord(c,"tiktok",{now:"2026-11-10T03:00:00Z",day:"2026-11-09",buffer:"error"}),"unknown");
});

test("creation word comes only from the clipper report", ()=>{
  const now="2026-11-09T23:00:00Z";
  assert.equal(S.creationWord(null,{now}),"unknown");
  assert.equal(S.creationWord({status:"working",updatedAt:"2026-11-09T22:30:00Z"},{now}),"pending");
  assert.equal(S.creationWord({status:"working",updatedAt:"2026-11-09T18:00:00Z"},{now}),"unknown"); // stale > 3h
  assert.equal(S.creationWord({status:"done",clips:[{id:"a"}]},{now}),"confirmed");
  assert.equal(S.creationWord({status:"done",clips:[]},{now}),"failed");
  assert.equal(S.creationWord({status:"failed"},{now}),"failed");
});

test("channel summary counts against however many clips the day has", ()=>{
  const ps=[1,2,3].map(i=>post({channel:"tiktok",text:"SPX clip "+i,status:i===3?"error":"sent"}));
  const g=S.groupClips(ps,null);
  const s=S.channelSummary(g,"tiktok",{now:"2026-11-10T03:00:00Z",day:"2026-11-09",buffer:"live"});
  assert.deepEqual(s,{total:3,count:3,confirmed:2,pending:0,failed:1,unknown:0,missing:0,word:"failed"});
});

test("summary word: all sent = confirmed, any queued = pending, Buffer down = unknown", ()=>{
  const g=S.groupClips([post({status:"sent"})],null);
  assert.equal(S.channelSummary(g,"tiktok",{now:"2026-11-10T03:00:00Z",day:"2026-11-09",buffer:"live"}).word,"confirmed");
  const q=S.groupClips([post({status:"scheduled"})],null);
  assert.equal(S.channelSummary(q,"tiktok",{now:"2026-11-09T20:00:00Z",day:"2026-11-09",buffer:"live"}).word,"pending");
  assert.equal(S.channelSummary(q,"tiktok",{now:"2026-11-09T20:00:00Z",day:"2026-11-09",buffer:"error"}).word,"unknown");
  assert.equal(S.channelSummary([],"tiktok",{now:"2026-11-09T20:00:00Z",day:"2026-11-09",buffer:"live"}).word,"pending");
  assert.equal(S.channelSummary([],"tiktok",{now:"2026-11-10T03:00:00Z",day:"2026-11-09",buffer:"live"}).word,"unknown");
});

test("ticker filter keeps clips that mention the ticker", ()=>{
  const g=S.groupClips([post({text:"SPY and QQQ hold"}),post({text:"SPX flips"})],null);
  assert.equal(S.filterTicker(g,"QQQ").length,1);
  assert.equal(S.filterTicker(g,"ALL").length,2);
});

test("a made clip missing from a channel after the window makes that channel failed", ()=>{
  const rep={status:"done",clips:[{id:"c1",ticker:"SPX",title:"SPX flips",posts:{}},{id:"c2",ticker:"SPY",title:"SPY holds",posts:{}}]};
  const g=S.groupClips([post({channel:"youtube",text:"SPX flips",status:"sent"})],rep);
  const late={now:"2026-11-10T03:00:00Z",day:"2026-11-09",buffer:"live"};
  assert.equal(S.channelSummary(g,"youtube",late).word,"failed");
  assert.equal(S.channelSummary(g,"youtube",{...late,now:"2026-11-09T23:30:00Z"}).word,"pending");
});

test("report ticker and caption tickers are combined", ()=>{
  const rep={status:"done",clips:[{id:"c1",ticker:"SPY",title:"SPY and QQQ battle"}]};
  assert.deepEqual(S.groupClips([],rep)[0].tickers,["SPY","QQQ"]);
});

test("total follows the day's clips, not a fixed 5", ()=>{
  const rep={status:"done",clips:[{id:"a",title:"SPX one"},{id:"b",title:"QQQ two"}]};
  const g=S.groupClips([post({channel:"tiktok",text:"SPX one",status:"sent"})],rep);
  const s=S.channelSummary(g,"tiktok",{now:"2026-11-09T20:00:00Z",day:"2026-11-09",buffer:"live"});
  assert.equal(s.total,2);assert.equal(s.count,1);
});

test("a reported clip with no posts field was never sent: unknown, not failed", ()=>{
  const rep={status:"done",clips:[{id:"c1",ticker:"SPX",title:"SPX test"}]};
  const g=S.groupClips([],rep),late={now:"2026-11-10T03:00:00Z",day:"2026-11-09",buffer:"live"};
  assert.equal(S.channelWord(g[0],"tiktok",late),"unknown");
  assert.equal(S.channelSummary(g,"tiktok",late).word,"unknown");
  assert.equal(S.sentToBuffer(g[0]),false);
});
