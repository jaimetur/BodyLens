import sys,json,collections,datetime
import xml.etree.ElementTree as ET
src=sys.argv[1];out=sys.argv[2]
P='HKQuantityTypeIdentifier';C='HKCategoryTypeIdentifier'
want={P+'RestingHeartRate':'rhr',P+'HeartRateVariabilitySDNN':'hrv',P+'OxygenSaturation':'spo2',P+'RespiratoryRate':'rr',P+'VO2Max':'vo2',
 P+'AppleSleepingWristTemperature':'temp',P+'AppleSleepingBreathingDisturbances':'bdist',P+'TimeInDaylight':'day',P+'HeartRateRecoveryOneMinute':'hrr',
 P+'WalkingHeartRateAverage':'whr',P+'FlightsClimbed':'flights',P+'WalkingSpeed':'wspeed',P+'AppleWalkingSteadiness':'steady',
 C+'AppleStandHour':'stand',C+'LowHeartRateEvent':'lowhr',C+'HighHeartRateEvent':'highhr',C+'SleepApneaEvent':'apnea',C+'HypertensionEvent':'hyper',C+'LowCardioFitnessEvent':'lowfit'}
D=collections.defaultdict(lambda:collections.defaultdict(list));events=[]
from zoneinfo import ZoneInfo
TZ=ZoneInfo('Europe/Madrid')
def loc(s):return datetime.datetime.strptime(s,'%Y-%m-%d %H:%M:%S %z').astimezone(TZ).strftime('%Y-%m-%d %H:%M')
def day(s):return s[:10]
def hour(s):return int(s[11:13])
n=0
for ev,el in ET.iterparse(src,events=('end',)):
    if el.tag=='Record':
        t=el.get('type');k=want.get(t)
        if k:
            sd=loc(el.get('startDate'));ed=loc(el.get('endDate'));v=el.get('value')
            if k in('lowhr','highhr','apnea','hyper','lowfit'):
                events.append([k,sd[:16],ed[:16]])
            elif k=='stand':
                if v and v.endswith('Stood'):D[day(sd)]['stand'].append(1)
            else:
                try:x=float(v)
                except:x=None
                if x is not None:
                    # medidas nocturnas: cuentan para el día en que te levantas (de las 18:00 a las 18:00)
                    dk=day(sd)
                    if k in('spo2','rr','temp','bdist','hrv') and hour(sd)>=18:
                        dk=(datetime.date.fromisoformat(dk)+datetime.timedelta(days=1)).isoformat()
                    if k=='spo2':x*=100
                    if k=='hrv':D[dk]['hrvN' if (hour(sd)<9 or hour(sd)>=22) else 'hrvD'].append(x)
                    D[dk][k].append(x)
                    if k=='spo2' and (hour(sd)<9 or hour(sd)>=22):D[dk]['spo2N'].append(x)
                n+=1
        el.clear()
    elif el.tag in('Workout','ActivitySummary','ClinicalRecord','Correlation'):el.clear()
COLS=['rhr','hrv','hrvN','spo2','spo2min','spo2N','rr','rrmin','rrmax','vo2','temp','bdist','day','stand','flights','whr','wspeed','steady','hrr']
mean=lambda a:sum(a)/len(a) if a else None
r1=lambda x,d=1:None if x is None else round(x,d)
hk={}
for dk,m in D.items():
    row=[r1(m['rhr'][-1],0) if m['rhr'] else None,r1(mean(m['hrv'])),r1(mean(m['hrvN'])),r1(mean(m['spo2'])),r1(min(m['spo2'])) if m['spo2'] else None,r1(mean(m['spo2N'])),
      r1(mean(m['rr'])),r1(min(m['rr'])) if m['rr'] else None,r1(max(m['rr'])) if m['rr'] else None,r1(m['vo2'][-1]) if m['vo2'] else None,
      r1(m['temp'][-1],2) if m['temp'] else None,r1(m['bdist'][-1]) if m['bdist'] else None,r1(sum(m['day']),0) if m['day'] else None,
      len(m['stand']) or None,r1(sum(m['flights']),0) if m['flights'] else None,r1(mean(m['whr']),0),r1(mean(m['wspeed'])*1,2) if m['wspeed'] else None,
      r1(m['steady'][-1]*100 if m['steady'] and m['steady'][-1]<=1 else (m['steady'][-1] if m['steady'] else None)),r1(max(m['hrr'])) if m['hrr'] else None]
    if any(v is not None for v in row):hk.setdefault(dk[:4],{'y':int(dk[:4]),'d':{}})['d'][dk]=row
json.dump({'cols':COLS,'hk':hk,'events':sorted(events)},open(out,'w'),separators=(',',':'))
print('records',n,'days',sum(len(v['d']) for v in hk.values()),'events',len(events))
