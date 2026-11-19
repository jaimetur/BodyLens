import sys,json,datetime
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo
TZ=ZoneInfo('Europe/Madrid')
loc=lambda s:datetime.datetime.strptime(s,'%Y-%m-%d %H:%M:%S %z').astimezone(TZ).strftime('%Y-%m-%d %H:%M')
C='HKCategoryTypeIdentifier';Q='HKQuantityTypeIdentifier'
T={C+'SexualActivity':'sexual',C+'MenstrualFlow':'menstrual',C+'IntermenstrualBleeding':'intermenstrual',C+'Headache':'headache',C+'LowerBackPain':'backpain',
   C+'Fatigue':'fatigue',C+'PelvicPain':'pelvicpain',C+'AppetiteChanges':'appetite',C+'NightSweats':'nightsweats',C+'Bloating':'bloating',
   C+'AbdominalCramps':'cramps',C+'MindfulSession':'mindful',Q+'NumberOfAlcoholicBeverages':'alcohol'}
out=[]
for ev,el in ET.iterparse(sys.argv[1],events=('end',)):
    if el.tag=='Record':
        k=T.get(el.get('type'))
        if k:
            v=el.get('value') or ''
            v=v.replace('HKCategoryValue','')
            for e in el.findall('MetadataEntry'):
                if e.get('key')=='HKSexualActivityProtectionUsed':v='protección' if e.get('value')=='1' else 'sin protección'
            out.append([k,loc(el.get('startDate')),loc(el.get('endDate')),v])
        el.clear()
    elif el.tag in('Workout','ActivitySummary'):el.clear()
out.sort(key=lambda x:x[1])
json.dump({'v':1,'e':out},open(sys.argv[2],'w'),ensure_ascii=False,separators=(',',':'))
import collections;print(collections.Counter(x[0] for x in out));print(collections.Counter((x[0],x[3]) for x in out).most_common(20))
