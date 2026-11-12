// Shared-password gate for a Cloudflare Worker. No CBBD credentials in client assets.
const encoder = new TextEncoder();
function hex(bytes) { return [...new Uint8Array(bytes)].map(x => x.toString(16).padStart(2, '0')).join(''); }
async function digest(value) { return hex(await crypto.subtle.digest('SHA-256', encoder.encode(value))); }
async function sign(value, secret) {
  const key = await crypto.subtle.importKey('raw', encoder.encode(secret), {name:'HMAC',hash:'SHA-256'}, false, ['sign']);
  return hex(await crypto.subtle.sign('HMAC', key, encoder.encode(value)));
}
function same(a,b) {
  if (typeof a !== 'string' || typeof b !== 'string' || a.length !== b.length) return false;
  let diff=0; for(let i=0;i<a.length;i++) diff|=a.charCodeAt(i)^b.charCodeAt(i);
  return diff===0;
}
function page(error='') {
  return new Response(`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Basketball Dashboard · Access</title><style>body{font:16px system-ui;background:#142237;color:white;display:grid;place-items:center;min-height:95vh}main{padding:32px;border:1px solid #61758d;border-radius:12px;max-width:360px}input,button{font:inherit;padding:12px;width:100%;box-sizing:border-box;margin-top:12px}button{cursor:pointer}p{color:#ffd1d1}</style></head><body><main><h1>College Basketball Dashboard</h1><form method="post" action="/unlock"><label>Shared password<input name="password" type="password" required autocomplete="current-password" maxlength="200"></label><button>Unlock dashboard</button></form>${error?'<p>Incorrect password. Try again.</p>':''}</main></body></html>`, {status:200,headers:{'content-type':'text/html; charset=utf-8','cache-control':'no-store','x-content-type-options':'nosniff'}});
}
async function authorized(request,secret) {
  const token=(request.headers.get('cookie')||'').split(';').map(x=>x.trim()).find(x=>x.startsWith('basketball_access='))?.slice(18);
  if (!token) return false;
  const [expiry,mac,...extra]=token.split('.');
  if(extra.length||!/^\d{10,13}$/.test(expiry)||!mac||Number(expiry)<Date.now()||Number(expiry)>Date.now()+7*86400000)return false;
  return same(mac,await sign(expiry,secret));
}
export default {
  async fetch(request,env) {
    if(!env.ACCESS_PASSWORD||!env.SESSION_SECRET||!env.ASSETS) return new Response('Hosting not configured', {status:503});
    const url=new URL(request.url);
    if(url.pathname==='/unlock'&&request.method==='POST') {
      const form=await request.formData().catch(()=>null);
      const password=form?.get('password');
      if(typeof password!=='string'||password.length>200)return page(true);
      if(!same(await digest(password),await digest(env.ACCESS_PASSWORD)))return page(true);
      const expiry=String(Date.now()+7*86400000);
      const token=expiry+'.'+await sign(expiry,env.SESSION_SECRET);
      return new Response(null,{status:303,headers:{location:'/', 'set-cookie':'basketball_access='+token+'; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=604800','cache-control':'no-store'}});
    }
    if(url.pathname==='/logout')return new Response(null,{status:303,headers:{location:'/', 'set-cookie':'basketball_access=; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=0','cache-control':'no-store'}});
    if(!await authorized(request,env.SESSION_SECRET))return page();
    if(request.method!=='GET'&&request.method!=='HEAD')return new Response('Method not allowed',{status:405});
    // Team statistics are served from private KV only after authentication.
    // An absent or invalid dataset leaves the existing fictional demo intact.
    if(url.pathname==='/data/teams.json'&&env.PRIVATE_DATA){
      const value=await env.PRIVATE_DATA.get('teams');
      if(value){
        let dataset=null;
        try { dataset=JSON.parse(value); } catch {}
        // Pilot publication is limited to one team and only UI-required fields.
        // Never forward arbitrary provider fields or an unbounded KV payload.
        const allowed=['team','conference','wins','losses','games','ppg','oppPpg','offRating','defRating','netRating','scoringMargin','pace','fgPct','threePct','ftPct','eFg','tsPct','rebounds','offRebounds','defRebounds','oppRebounds','reboundingMargin','assists','turnovers'];
        if(dataset?.schemaVersion===1&&dataset.season===2027&&dataset.demo===false&&Array.isArray(dataset.rows)&&dataset.rows.length===1&&dataset.rows[0]?.team==='Duke'){
          const row=Object.fromEntries(allowed.map(key=>[key,dataset.rows[0][key]??null]));
          const publicView={schemaVersion:1,season:2027,seasonLabel:'2026–27',scope:'Private one-team pilot · Data: CollegeBasketballData.com',generatedAt:dataset.generatedAt,demo:false,rows:[row]};
          return new Response(JSON.stringify(publicView),{headers:{'content-type':'application/json; charset=utf-8','cache-control':'private, no-store','x-content-type-options':'nosniff'}});
        }
      }
    }
    // Other datasets retain their existing private KV lookup behavior.
    const privateFiles={'/data/players.json':'players','/data/demo-schedule.json':'schedule'};
    if(Object.hasOwn(privateFiles,url.pathname)&&env.PRIVATE_DATA){
      const value=await env.PRIVATE_DATA.get(privateFiles[url.pathname]);
      if(value)return new Response(value,{headers:{'content-type':'application/json; charset=utf-8','cache-control':'private, no-store','x-content-type-options':'nosniff'}});
    }
    const response=await env.ASSETS.fetch(request);
    const headers=new Headers(response.headers);headers.set('cache-control','private, no-store');headers.set('x-content-type-options','nosniff');
    return new Response(response.body,{status:response.status,headers});
  }
};
