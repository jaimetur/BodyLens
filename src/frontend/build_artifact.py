# Une app/app_a+b+c.html en la versión artefacto de claude.ai (solo referencia). Se ejecuta desde src/frontend/.
import json,os,gzip,base64,subprocess
tmpl=open('app/app_a.html').read()+open('app/app_b.html').read()+open('app/app_c.html').read()
open('app.html','w').write(tmpl)
tP='"@@PACK@@"'
assert tmpl.count(tP)==1,tmpl.count(tP)
snap=json.load(open('snap.json')) if os.path.exists('snap.json') else None
raw=json.dumps({'self':tmpl,'snap':snap},ensure_ascii=False,separators=(',',':')).encode('utf-8')
pack=base64.b64encode(gzip.compress(raw,9)).decode('ascii')
page=tmpl.replace(tP,'"'+pack+'"')
open('peso.html','w').write(page)
if os.path.exists('preview.html'):
    src=open('preview.html').read();i=src.find('<title>');open('preview.html','w').write(src[:i]+page+'\n</body></html>')
# comprobación de sintaxis de cada script
chk=subprocess.run(['node','-e',"const fs=require('fs');const t=fs.readFileSync('app.html','utf8');for(const m of t.matchAll(/<script(?: id=\\x22core\\x22)?>([\\s\\S]*?)<\\/script>/g)){new Function(m[1])}console.log('sintaxis ok')"],capture_output=True,text=True)
print(chk.stdout.strip() or chk.stderr.strip()[:400])
print('app',len(tmpl),'raw',len(raw),'pack',len(pack),'page',len(page))
