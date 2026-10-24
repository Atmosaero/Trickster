#!/usr/bin/env python3
"""Acceptance gate, independent of regression-test success. Returns nonzero for partial work."""
import argparse, json
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--input',type=Path,default=Path('artifacts/reliability'))
a=p.parse_args();failures=[]
def load(relative):
 path=a.input/relative
 if not path.exists():failures.append(f'Missing evidence: {relative}');return {}
 return json.loads(path.read_text(encoding='utf-8-sig'))
data=load('fullbody/results.json');cases=data.get('cases',[])
expected={f'rig{r}-{k}-v{v}' for r in (0,1) for k in ('squat','landing') for v in (0,1,2)}
found={r['id'] for r in cases}
for missing in sorted(expected-found):failures.append(f'Missing variation: {missing}')
for case in cases+[dict(load('fullbody/jump/report.json'),id='fullbody-jump')]:
 report=case.get('report',{});name=case.get('id','unknown')
 if not case.get('calculated'):failures.append(f'{name}: calculation failed: {case.get("error")}')
 if report.get('status')!='solved':failures.append(f'{name}: {report.get("status","missing status")}')
 for domain in ('nativeControl','bakedKinematics','bakedDynamics','intervalBoundaries'):
  status=report.get('validationDomains',{}).get(domain,{}).get('status')
  if status!='passed':failures.append(f'{name}: {domain} = {status}')
external=load('external-refined-dynamics.json')
if not external.get('cases'):failures.append('No external dynamics measurements')
for case,formats in external.get('cases',{}).items():
 for fmt,m in formats.items():
  # Original seven-body fixtures: M=70kg, g=9.81, H=2.035m.
  if (m.get('rootForceRmsN',float('inf'))>.03*70*9.81 or
      m.get('rootForcePeakN',float('inf'))>.10*70*9.81 or
      m.get('rootTorqueRmsNm',float('inf'))>.03*70*9.81*2.035 or
      m.get('rootTorquePeakNm',float('inf'))>.10*70*9.81*2.035 or
      m.get('requiredWindowTorqueLimitRatio',float('inf'))>1.01):
   failures.append(f'{case}/{fmt}: external window balance/drive threshold failed')
for kind in ('squat','landing'):
 summary=load(f'independent-refined/{kind}/summary.json')
 if not summary:failures.append(f'{kind}: no external geometry summary')
 for fmt,m in summary.items():
  if not m.get('passed',False):failures.append(f'{kind}/{fmt}: external geometry/matrix check failed')
for rig in (0,1):
 for kind in ('squat','landing'):
  name=f'rig{rig}-{kind}-v1';summary=load(f'independent-fullbody/{name}/summary.json')
  for fmt,m in summary.items():
   if not m.get('passed',False):failures.append(f'{name}/{fmt}: full-body external geometry/matrix check failed')
  # The seven-body convergence experiment cannot certify an imported full-body rig.
  failures.append(f'{name}: full-body external dynamics not yet certified')
result={'acceptanceComplete':not failures,'failures':failures,
 'scope':'Mandatory full-body, boundary and external gates; regression success alone does not imply acceptance.'}
(a.input/'acceptance-gate.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
for failure in failures:print('OPEN:',failure)
print('PASS' if not failures else f'INCOMPLETE: {len(failures)} open gates')
raise SystemExit(bool(failures))
