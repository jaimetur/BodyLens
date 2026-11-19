const fs=require('fs');const {JSDOM,VirtualConsole}=require('jsdom');const {Blob}=require('buffer');
const page=fs.readFileSync('peso.html','utf8');
const html=page.replace(/<script src="[^"]+"><\/script>/g,'');
const errors=[];const vc=new VirtualConsole();vc.on('jsdomError',e=>{if(!/scrollTo/.test(e.message))errors.push('jsdomError: '+e.message)});vc.on('error',(...a)=>errors.push('console.error: '+a.map(x=>x&&x.stack||x).join(' ')));
const dom=new JSDOM(`<!doctype html><html><head></head><body>${html}</body></html>`,{runScripts:'outside-only',url:'https://example.test/#resumen',pretendToBeVisual:true,virtualConsole:vc});
const w=dom.window;w.ResizeObserver=class{observe(){}};w.XLSX={};w.matchMedia=()=>({matches:false});
Object.assign(w,{Blob,Response,CompressionStream,DecompressionStream});
const mode=process.argv[2]||'anon';
w.claude={use:async n=>mode==='owner'&&n==='user'?{isOwner:async()=>true,id:async()=>'me'}:null};
const scripts=[...html.matchAll(/<script(?: id="core")?>([\s\S]*?)<\/script>/g)].map(m=>m[1]);
try{w.eval(scripts.join("\n;\n")+"\n;window.__t={regen:()=>buildPage(SNAP),snap:()=>SNAP,self:()=>SELF_T,life:()=>LIFE,go:v=>{location.hash='#'+v;route()}};")}catch(e){errors.push("eval: "+e.stack)}
setTimeout(async()=>{
  const $=id=>w.document.getElementById(id);
  console.log(mode,'| viewer',w.document.body.classList.contains('viewer'),'| pill',$('syncPill').textContent,'| notice',$('notice').hidden?'(oculto)':$('notice').textContent.slice(0,90));
  const L=w.__t.life();console.log('life act',L&&L.act.length,'slp',L&&L.slp.length,'wo',L&&L.wo.length,'stepWeeks',L&&L.stepWeeks&&L.stepWeeks.length,'slpRes',L&&L.slpRes&&L.slpRes.length);
  console.log('tiles2',[...w.document.querySelectorAll('#tiles2 .tile')].map(t=>t.querySelector('.k').textContent+'='+t.querySelector('.v').textContent+' ['+t.querySelector('.d').textContent+']').join(' | '));
  console.log('insights',[...w.document.querySelectorAll('#insights li')].map(l=>l.textContent.trim()).filter(t=>/pasos|dormir/.test(t)).join(' || '));
  for(const v of ['actividad','sueno']){w.__t.go(v);const sec=$('v-'+v);console.log(v,'svgs',sec.querySelectorAll('svg').length,'empties',JSON.stringify([...sec.querySelectorAll('.empty')].map(e=>e.textContent.trim().slice(0,50))),'kv',sec.querySelector('.kv').textContent.replace(/\s+/g,' ').slice(0,300))}
  console.log('actWTxt',$('actWTxt').textContent);console.log('slpWTxt',$('slpWTxt').textContent);
  if(mode==='owner'){const html2=await w.__t.regen();const m=/const PACK="([^"]+)"/.exec(html2);const gz=require('zlib').gunzipSync(Buffer.from(m[1],'base64')).toString();const p=JSON.parse(gz);
    console.log('regen ok',html2.startsWith('<!doctype html>'),'self igual',p.self===w.__t.self(),'snap años act',Object.keys(p.snap.act||{}).join(','),'len',html2.length)}
  console.log('ERRORS',errors.length?errors.join('\n'):'none');
},600);
