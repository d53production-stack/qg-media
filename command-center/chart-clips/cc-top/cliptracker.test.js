// Command Center chart clip tracker: rules on top of clipstatus.js. Run: node --test cc-top/
const test=require("node:test"),assert=require("node:assert/strict");
const CS=require("./clipstatus.js"),T=require("./cliptracker.js");
// Nov 2026: ET = UTC-5. Mon Nov 9, Tue Nov 10, Wed Nov 11. Nov 26 = Thanksgiving (market closed).
const P=(o)=>({id:"p"+Math.random().toString(16).slice(2,8),channel:"tiktok",status:"scheduled",text:"SPX caption.",dueAt:"2026-11-10T23:30:00Z",...o});

test("clip room runs 6:00 PM to 11:59 PM ET on weekdays", ()=>{
  assert.equal(T.inClipRoom("2026-11-09T23:00:00Z"),true);   // Mon 6:00 PM
  assert.equal(T.inClipRoom("2026-11-10T03:50:00Z"),true);   // Mon 10:50 PM (Nov 9 real clip)
  assert.equal(T.inClipRoom("2026-11-10T04:59:00Z"),true);   // Mon 11:59 PM
  assert.equal(T.inClipRoom("2026-11-10T05:00:00Z"),false);  // Tue 12:00 AM
  assert.equal(T.inClipRoom("2026-11-09T22:59:00Z"),false);  // 5:59 PM
  assert.equal(T.inClipRoom("2026-11-08T23:30:00Z"),false);  // Sunday
});

test("late clips (10:50 PM ET) are picked for that day", ()=>{
  const late=P({id:"late",dueAt:"2026-11-10T03:50:00Z"}),other=P({id:"x",dueAt:"2026-11-09T19:00:00Z"});
  assert.deepEqual(T.pickPosts([late,other],"2026-11-09",null).map(p=>p.id),["late"]);
});

test("a post the clipper reported is picked even outside the clip room", ()=>{
  const p=P({id:"b1",dueAt:"2026-11-09T21:00:00Z"});   // 4 PM ET
  const run={status:"done",clips:[{id:"c1",posts:{tiktok:"b1"}}]};
  assert.deepEqual(T.pickPosts([p],"2026-11-09",run).map(x=>x.id),["b1"]);
  assert.deepEqual(T.pickPosts([p],"2026-11-09",null).map(x=>x.id),[]);
});

test("a reported clip still waiting at 10 PM ET is pending, not failed", ()=>{
  const run={status:"done",clips:[{id:"c1",ticker:"SPX",title:"x",posts:{}}]};
  const clips=CS.groupClips([],run),ctx=T.ctx("2026-11-09","2026-11-10T03:00:00Z","live");
  assert.equal(CS.channelSummary(clips,"tiktok",ctx).word,"pending");
  assert.equal(CS.channelSummary(clips,"tiktok",T.ctx("2026-11-09","2026-11-10T05:01:00Z","live")).word,"failed");
});

test("Nov 9 real night: both late clips sent on all channels reads confirmed", ()=>{
  const run={status:"done",updatedAt:"2026-11-10T03:33:09Z",clips:[{id:"01",title:"a",posts:{tiktok:"t1",instagram:"i1",youtube:"y1"}},{id:"03",title:"b",posts:{tiktok:"t3",instagram:"i3",youtube:"y3"}}]};
  const posts=[["t1","tiktok"],["i1","instagram"],["y1","youtube"]].map(([id,ch])=>P({id,channel:ch,status:"sent",dueAt:"2026-11-10T03:50:00Z"}))
    .concat([["t3","tiktok"],["i3","instagram"],["y3","youtube"]].map(([id,ch])=>P({id,channel:ch,status:"sent",dueAt:"2026-11-10T04:20:00Z"})));
  const d=T.dayStatus(posts,run,"2026-11-09","2026-11-10T15:00:00Z","live");
  assert.equal(d.word,"confirmed");
  assert.equal(d.made,2);
  assert.deepEqual(d.channels.map(c=>c.word),["confirmed","confirmed","confirmed"]);
});

test("day word: any failure fails the day", ()=>{
  assert.equal(T.dayWord("confirmed",["confirmed","failed","confirmed"]),"failed");
  assert.equal(T.dayWord("failed",["unknown","unknown","unknown"]),"failed");
});
test("day word: confirmed only when the clips were made and every channel posted", ()=>{
  assert.equal(T.dayWord("confirmed",["confirmed","confirmed","confirmed"]),"confirmed");
  assert.equal(T.dayWord("unknown",["confirmed","confirmed","confirmed"]),"pending");
  assert.equal(T.dayWord("confirmed",["confirmed","pending","confirmed"]),"pending");
  assert.equal(T.dayWord("confirmed",["confirmed","unknown","confirmed"]),"unknown");
});
test("day word: nothing known is unknown", ()=>{
  assert.equal(T.dayWord("unknown",["unknown","unknown","unknown"]),"unknown");
  assert.equal(T.dayWord("pending",["pending","pending","pending"]),"pending");
});

test("tracked day is today on a trading day, else the last trading day", ()=>{
  assert.equal(T.clipDay("2026-11-11T19:00:00Z"),"2026-11-11");   // Wed
  assert.equal(T.clipDay("2026-11-14T19:00:00Z"),"2026-11-13");   // Sat -> Fri
  assert.equal(T.clipDay("2026-11-26T19:00:00Z"),"2026-11-25");   // Thanksgiving -> Wed
  assert.equal(T.clipDay("2026-11-10T03:00:00Z"),"2026-11-09");   // Mon 10 PM ET is still Monday
});

test("recent trading days skip weekends and holidays, newest last", ()=>{
  assert.deepEqual(T.recentDays("2026-11-30",5),["2026-11-23","2026-11-24","2026-11-25","2026-11-27","2026-11-30"]);
});

test("job line says what the clipper is doing, in words", ()=>{
  const day="2026-11-11";
  assert.equal(T.jobLine(null,day,"2026-11-11T19:00:00Z").text,"Starts after the close");
  assert.equal(T.jobLine(null,day,"2026-11-11T19:00:00Z").word,"unknown");
  assert.equal(T.jobLine(null,day,"2026-11-11T23:30:00Z").text,"No report from the clipper yet");
  assert.equal(T.jobLine({status:"working",updatedAt:"2026-11-11T21:40:00Z",message:"Rendering 2 of 3"},day,"2026-11-11T21:45:00Z").text,"Working · Rendering 2 of 3");
  assert.equal(T.jobLine({status:"working",updatedAt:"2026-11-11T21:40:00Z"},day,"2026-11-11T21:45:00Z").word,"pending");
  assert.equal(T.jobLine({status:"done",updatedAt:"2026-11-11T22:35:00Z",clips:[{},{},{}]},day,"2026-11-11T23:00:00Z").text,"Done · 3 clips made");
  assert.equal(T.jobLine({status:"done",updatedAt:"2026-11-11T22:35:00Z",clips:[{}]},day,"2026-11-11T23:00:00Z").text,"Done · 1 clip made");
  assert.equal(T.jobLine({status:"failed",message:"Render crashed"},day,"2026-11-11T23:00:00Z").text,"Failed · Render crashed");
  assert.equal(T.jobLine({status:"working",updatedAt:"2026-11-11T17:00:00Z"},day,"2026-11-11T23:00:00Z").text,"Last report over 3 hours ago");
});

test("clip rows list each clip by post time with a word per channel", ()=>{
  const run={status:"done",clips:[{id:"b",title:"Second",dueAt:"2026-11-11T21:28:00-05:00",grade:"READ GRADED: HIT",posts:{tiktok:"t2"}},{id:"a",title:"First",dueAt:"2026-11-11T18:00:00-05:00",posts:{tiktok:"t1"}}]};
  const posts=[P({id:"t1",status:"sent",dueAt:"2026-11-11T23:00:00Z"}),P({id:"t2",status:"error",dueAt:"2026-11-12T02:28:00Z"})];
  const d=T.dayStatus(posts,run,"2026-11-11","2026-11-12T03:00:00Z","live");
  assert.deepEqual(d.rows.map(r=>r.title),["First","Second"]);
  assert.deepEqual(d.rows[0].words,{tiktok:"confirmed",instagram:"pending",youtube:"pending"});  // 10 PM ET: room still open
  assert.equal(d.rows[1].words.tiktok,"failed");
  assert.equal(d.rows[1].grade,"READ GRADED: HIT");
  assert.equal(d.word,"failed");
});
