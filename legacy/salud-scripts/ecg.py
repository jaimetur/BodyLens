import sys,os,json,glob,re
d=sys.argv[1];out={}
for f in sorted(glob.glob(os.path.join(d,'*.csv'))):
    L=open(f,encoding='utf-8').read().splitlines();meta={};i=0
    while i<len(L) and not re.match(r'^-?\d+,\d+$|^-?\d+$',L[i].strip()):
        p=L[i].split(',',1)
        if len(p)==2:meta[p[0].strip()]=p[1].strip().strip('"')
        i+=1
    sig=[float(x.replace(',','.')) for x in L[i:] if x.strip()]
    fs=int(re.findall(r'\d+',meta.get('Frecuencia de muestreo','512'))[0])
    # a 128 Hz (media de cada 4 muestras)
    st=max(1,fs//128);ds=[round(sum(sig[j:j+st])/st) for j in range(0,len(sig)-st+1,st)];fs2=fs//st
    # pulso: picos R (derivada) sobre la señal
    w=int(fs2*0.2);hp=[ds[j]-sum(ds[max(0,j-w):j+w+1])/len(ds[max(0,j-w):j+w+1]) for j in range(len(ds))]
    a=[abs(x) for x in hp];srt=sorted(a);thr=0.45*srt[int(len(srt)*0.99)]
    pk=[];last=-999
    for j in range(1,len(a)-1):
        if a[j]>thr and a[j]>=a[j-1] and a[j]>=a[j+1]:
            if j-last>fs2*0.28:pk.append(j);last=j
            elif a[j]>a[pk[-1]]:pk[-1]=j;last=j
    rr=sorted(pk[i+1]-pk[i] for i in range(len(pk)-1))
    hr=round(60*fs2/rr[len(rr)//2]) if len(rr)>3 else None
    import datetime
    from zoneinfo import ZoneInfo
    t=datetime.datetime.strptime(meta.get('Fecha de registro',''),'%Y-%m-%d %H:%M:%S %z').astimezone(ZoneInfo('Europe/Madrid')).strftime('%Y-%m-%d %H:%M')
    out[t]={'t':t,'cls':meta.get('Clasificación',''),'sym':meta.get('Síntomas',''),'dev':meta.get('Dispositivo',''),'fs':fs2,'hr':hr,'sig':ds}
    print(t,out[t]['cls'],hr,len(ds),fs2)
json.dump(out,open(sys.argv[2],'w'),separators=(',',':'),ensure_ascii=False)
