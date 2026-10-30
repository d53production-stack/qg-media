// Screenshots of the refresh preview: idle, checking, checked, no new report, couldn't start. A fake window.claude feeds the page:
// db docs can be pushed later (window.__push), and mcp.callTool records the fire_trigger call (or rejects, for the error case).
// Usage: node shoot.js <page.html> <outDir>
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [,, page_, outDir] = process.argv;
const ago = m => new Date(Date.now() - m * 60e3).toISOString();
const url = { highlight: 'https://claude.ai/artifact/9pKYhvbeaxpwwDyhQswHvi', factory: 'https://claude.ai/artifact/Q9r9A3GK8dhbKB5jKb2p2g', style: 'https://claude.ai/artifact/AmAqmKFatXwLoTUiE29iTU', desk: 'https://claude.ai/artifact/Y876Yu3rcP3g4hX6oSfcKz' };
const label = { highlight: 'Highlight Studio', factory: 'Video Factory', style: 'Style Studio', desk: 'Publishing Desk' };
const job = (title, min, extra = {}) => ({ title, status: 'confirmed', raw: 'done', step: 'Ready', startedAt: ago(min + 30), endedAt: ago(min), updatedAt: ago(min), videos: 11, message: '', by: 'hourly', ...extra });
const studios = checkedAt => [
  { studio: 'highlight', label: label.highlight, url: url.highlight, checkedAt, checkedBy: 'hourly', jobs: { '2026-10-29-0ww4': job('Oct 29 webinar', 20 * 60) } },
  { studio: 'factory', label: label.factory, url: url.factory, checkedAt, checkedBy: 'hourly', jobs: { '2026-10-29-whats-new': job("What's New: roundup + 7 release-note videos", 19 * 60) } },
  { studio: 'style', label: label.style, url: url.style, checkedAt, checkedBy: 'hourly', jobs: { rmvoi1xo6: job('Halloween 2', 5 * 1440, { videos: 0 }) } },
  { studio: 'desk', label: label.desk, url: url.desk, checkedAt, checkedBy: 'hourly', jobs: { '2026-W44': job('Week 2026-W44', 4 * 1440, { raw: 'APPROVED', videos: 0 }) } },
];
const air = lastSeen => ({ apps: { GEEKDISPLAY: { up: true, screen: { activeNow: true, connected: true } }, GEEKRECORDER: { up: true, recording: true, state: 'recording', day: null, frames: 3311, lastExport: { at: ago(400), name: 'Recap.mp4' }, post: null } }, diskFreeGB: 12.8, lastSeen, problems: ['QuantGeeks login expires Sat Oct 31 6:29 AM PT'], staleAfterMinutes: 10 });

function shim(failCode) {
  const D = { 'settings/home': { tz: 'America/Los_Angeles', zip: '95014' }, 'status/air': air(ago(12)) };
  const C = { studio: studios(ago(17 * 60)), tasks: [], content: [], projects: [], playbooks: [], suggestions: [], days: [] };
  return `(()=>{const D=${JSON.stringify(D)},C=${JSON.stringify(C)},L={doc:{},coll:{}};
    const snap=arr=>({docs:arr.map(d=>({id:d.id||d.studio,data:()=>d}))});
    const coll=name=>({onSnapshot:cb=>{(L.coll[name]=L.coll[name]||[]).push(cb);cb(snap(C[name]||[]));return()=>{}},where:()=>coll(name),orderBy:()=>coll(name),limit:()=>coll(name)});
    const db={collection:coll,doc:p=>({onSnapshot:cb=>{(L.doc[p]=L.doc[p]||[]).push(cb);const d=D[p];cb({exists:!!d,data:()=>d});return()=>{}}})};
    window.__push=(p,d)=>{if(p.includes("/")){D[p]=d;(L.doc[p]||[]).forEach(cb=>cb({exists:true,data:()=>d}))}else{C[p]=d;(L.coll[p]||[]).forEach(cb=>cb(snap(d)))}};
    window.__bump=()=>{const n=new Date().toISOString();window.__push("status/air",{...D["status/air"],lastSeen:n});window.__push("studio",C.studio.map(d=>({...d,checkedAt:n})))};
    window.__rerender=()=>window.__push("status/air",{...D["status/air"]});
    window.__fired=[];
    const mcp={watchTool:()=>()=>{},callTool:async(s,t,i)=>{window.__fired.push([s,t,i]);${failCode ? `const e=new Error("x");e.code=${JSON.stringify(failCode)};throw e` : 'return {payload:{}}'}}};
    window.claude={use:async n=>n==="db"?db:n==="mcp"?mcp:null};})();`;
}

(async () => {
  const browser = await chromium.launch();
  fs.mkdirSync(outDir, { recursive: true });
  const file = 'file://' + path.resolve(page_);
  for (const [w, h, tag] of [[1280, 900, 'desktop'], [390, 844, 'phone']]) {
    for (const failCode of [null, 'consent_required']) {
      const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 2, colorScheme: 'dark' });
      const page = await ctx.newPage();
      const errors = [];
      page.on('pageerror', e => errors.push(String(e)));
      await page.addInitScript(shim(failCode) + 'try{localStorage.setItem("qg.tab","today")}catch(_){}');
      await page.goto(file + '#today', { waitUntil: 'load' });
      await page.addStyleTag({ content: '.tabbar,.toast,.topbar{display:none!important}' }); // fixed layers would land on the clipped full-page shot
      await page.waitForTimeout(1200);
      const cards = page.locator('#air, #studios');
      const shot = async name => {
        // page coordinates, so the sticky top bar and the bottom tabs never cover the cards
        const r = await page.evaluate(() => { const a = document.getElementById('air').getBoundingClientRect(), b = document.getElementById('studios').getBoundingClientRect(); return { x: a.left, y: a.top + scrollY, w: a.width, h: b.bottom - a.top }; });
        await page.screenshot({ path: `${outDir}/${name}-${tag}.png`, fullPage: true, clip: { x: r.x - 8, y: r.y - 8, width: r.w + 16, height: r.h + 16 } });
      };
      const btn = () => page.locator('[data-act=refresh]').first();
      if (!failCode) {
        await shot('1-idle');
        await btn().click(); await page.waitForTimeout(400);
        await shot('2-checking');
        const twice = await page.locator('[data-act=refresh]').count();
        await page.waitForTimeout(4200); // let the start toast clear
        await page.evaluate(() => window.__bump());
        await page.waitForTimeout(400);
        await shot('3-checked');
        await page.waitForTimeout(4200);
        await btn().click(); await page.waitForTimeout(300);
        await page.evaluate(() => { const o = Date.now; Date.now = () => o() + 6 * 60e3; window.__rerender(); });
        await page.waitForTimeout(4200);
        await shot('4-no-new-report');
        const fired = await page.evaluate(() => window.__fired);
        console.log(tag, 'fired', JSON.stringify(fired), 'refresh buttons while checking:', twice);
      } else {
        await btn().click(); await page.waitForTimeout(500);
        await shot('5-couldnt-start');
      }
      console.log(tag, failCode || 'ok', errors.length ? 'ERRORS ' + errors.join(' | ') : 'no page errors');
      await ctx.close();
    }
  }
  await browser.close();
})();
