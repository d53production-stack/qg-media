// Tests for the card REFRESH logic. Runs the exact block shipped in the page (between refresh-logic markers).
const fs=require("fs"),assert=require("assert");
const html=fs.readFileSync(process.argv[2],"utf8");
const m=/\/\* refresh-logic:start \*\/([\s\S]*?)\/\* refresh-logic:end \*\//.exec(html);
assert(m,"refresh-logic block not found in page");
const G=new Function(m[1]+";return {refreshState,airMark,studioMark,REFRESH_WAIT_MS,REFRESH_SHOW_FAILED_MS};")();
let n=0;const t=(name,fn)=>{fn();n++;console.log("ok -",name)};
const T=iso=>Date.parse(iso);
const press=(mark,at="2026-10-30T20:05:00Z",err=null)=>({at:T(at),mark,err});

t("no request is idle",()=>assert.equal(G.refreshState(null,"2026-10-30T19:55:00Z",T("2026-10-30T20:05:00Z")),"idle"));
t("right after the press it is pending",()=>assert.equal(G.refreshState(press("2026-10-30T19:55:00Z"),"2026-10-30T19:55:00Z",T("2026-10-30T20:05:30Z")),"pending"));
t("still pending just before the wait runs out",()=>assert.equal(G.refreshState(press("2026-10-30T19:55:00Z"),"2026-10-30T19:55:00Z",T("2026-10-30T20:09:59Z")),"pending"));
t("confirmed once the evidence moves past the pre-press mark",()=>assert.equal(G.refreshState(press("2026-10-30T19:55:00Z"),"2026-10-30T20:05:00Z",T("2026-10-30T20:06:30Z")),"confirmed"));
t("the same mark after the wait is failed, never confirmed",()=>assert.equal(G.refreshState(press("2026-10-30T19:55:00Z"),"2026-10-30T19:55:00Z",T("2026-10-30T20:10:01Z")),"failed"));
t("an older mark (doc rolled back) is not confirmed",()=>assert.equal(G.refreshState(press("2026-10-30T19:55:00Z"),"2026-10-30T19:50:00Z",T("2026-10-30T20:06:00Z")),"pending"));
t("a failed start is failed even inside the wait",()=>assert.equal(G.refreshState(press("2026-10-30T19:55:00Z","2026-10-30T20:05:00Z","not approved"),"2026-10-30T19:55:00Z",T("2026-10-30T20:05:10Z")),"failed"));
t("no doc before the press, a doc after it is confirmed",()=>assert.equal(G.refreshState(press(null),"2026-10-30T20:06:00Z",T("2026-10-30T20:07:00Z")),"confirmed"));
t("no doc before or after is pending, then failed",()=>{
  assert.equal(G.refreshState(press(null),null,T("2026-10-30T20:06:00Z")),"pending");
  assert.equal(G.refreshState(press(null),null,T("2026-10-30T20:11:00Z")),"failed");
});
t("a failed refresh clears to idle after 30 minutes",()=>{
  assert.equal(G.refreshState(press("2026-10-30T19:55:00Z"),"2026-10-30T19:55:00Z",T("2026-10-30T20:34:00Z")),"failed");
  assert.equal(G.refreshState(press("2026-10-30T19:55:00Z"),"2026-10-30T19:55:00Z",T("2026-10-30T20:36:00Z")),"idle");
});
t("wait is 5 minutes",()=>assert.equal(G.REFRESH_WAIT_MS,5*60e3));
t("airMark is the Air's lastSeen",()=>{
  assert.equal(G.airMark({lastSeen:"2026-10-30T19:55:00Z"}),"2026-10-30T19:55:00Z");
  assert.equal(G.airMark(null),null);
});
t("studioMark is the newest checkedAt and skips missing ones",()=>{
  const docs=new Map([["highlight",{checkedAt:"2026-10-30T03:44:00Z"}],["factory",{checkedAt:"2026-10-30T03:07:48Z"}],["style",{}],["desk",null]]);
  assert.equal(G.studioMark(docs),"2026-10-30T03:44:00Z");
  assert.equal(G.studioMark(new Map()),null);
});
console.log(`${n} tests passed`);
