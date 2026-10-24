#!/usr/bin/env python3
"""Publish scalar reliability evidence and scientific plots; never copies private fixtures."""
from pathlib import Path
import json, argparse, csv, zipfile, re
parser=argparse.ArgumentParser()
parser.add_argument('--input',type=Path,default=Path('artifacts/reliability'))
parser.add_argument('--output',type=Path,default=Path('artifacts/reliability-publication'))
parser.add_argument('--publish-examples',action='store_true')
args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
excluded={'controlReplay','trajectory','contactForces','timeSeries','modelXml'}
def compact(x):
 if isinstance(x,dict):return {k:compact(v) for k,v in x.items() if k not in excluded}
 if isinstance(x,list):return [compact(v) for v in x]
 return x
files=['build-delivery.json','portable/summary.json','portable-package/summary.json','derivative-calibration.json','quiet-contact.json','acceptance-gate.json','fullbody/jump/report.json','external-refined-dynamics.json','baseline-chain.json','step-convergence.json','external-dynamics.json','HumanM-proxy.json','HumanM-dynamics.json',
 'independent-refined/squat/summary.json','independent-refined/landing/summary.json','independent-fullbody/rig0-squat-v1/summary.json','independent-fullbody/rig0-landing-v1/summary.json','independent-fullbody/rig1-squat-v1/summary.json','independent-fullbody/rig1-landing-v1/summary.json','fullbody/baseline-results.json','fullbody/rne-experiment-results.json','fullbody/results.json']
version=re.search(r'project\(Trickster VERSION ([0-9.]+)', (Path(__file__).resolve().parent.parent/'CMakeLists.txt').read_text()).group(1)
results={'baselineCommit':'d7ecb38','baselineProductVersion':'0.4.0','publicationProductVersion':version,
 'historicalEvidence':'https://github.com/Atmosaero/Trickster/releases/download/v0.5.0/Trickster-0.5.0-validation-evidence.zip',
 'acceptanceComplete':False,'measurements':{}}
for name in files:
 path=args.input/name
 if path.exists():results['measurements'][name]=compact(json.loads(path.read_text(encoding='utf-8-sig')))
(args.output/'physics-reliability-results.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
chain=args.input/'baseline-chain.json'
if chain.exists():
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 data=json.loads(chain.read_text())['cases']; folder=args.output/'physics-reliability';folder.mkdir(exist_ok=True)
 with (folder/'grid-study.csv').open('w',newline='') as f:
  writer=csv.writer(f);writer.writerow(['case','representation_fps','analysis_fps','native_position_inverse_rms_N','baked_inverse_rms_N','reopened_inverse_rms_N'])
  for kind,c in data.items():
   for a in c['experiments']:writer.writerow([kind,a['representationFps'],a['analysisFps'],a['nativePositions']['rootForceRmsN'],a['baked']['rootForceRmsN'],a['reopened']['rootForceRmsN']])
 fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
 for ax,(kind,c) in zip(axes,data.items()):
  same=[a for a in c['experiments'] if a['representationFps']==a['analysisFps']]
  x=[a['analysisFps'] for a in same]
  ax.plot(x,[a['nativePositions']['rootForceRmsN'] for a in same],'o-',label='Native positions, centered inverse')
  ax.plot(x,[a['baked']['rootForceRmsN'] for a in same],'x--',label='Linear bake, centered inverse')
  ax.set(title=kind, xlabel='Analysis / uniform representation FPS',ylabel='RMS root residual (N)',yscale='log');ax.grid(alpha=.3);ax.legend(fontsize=8)
 fig.savefig(folder/'inverse-grid.svg');plt.close(fig)
 fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
 for ax,(kind,c) in zip(axes,data.items()):
  linear=next(a for a in c['experiments'] if a['representationFps']==60 and a['analysisFps']==30)['representedImpulse']
  cubic=next(h for h in c['hermite'] if not h['representation']['adaptive'])['impulse']
  adaptive=next(h for h in c['hermite'] if h['representation']['adaptive'])['impulse']
  for name,a in [('Linear 60',linear),('Cubic 60',cubic),('Adaptive cubic, nominal 60',adaptive)]:
   t=a['timeSeries'];ax.plot([p['seconds'] for p in t],[p['rootForceN'] for p in t],label=name)
  ax.set(title=kind,xlabel='Time (s)',ylabel='Windowed force residual (N)');ax.grid(alpha=.3);ax.legend(fontsize=8)
 fig.savefig(folder/'represented-impulse.svg');plt.close(fig)
if args.publish_examples:
 target=args.output;target.mkdir(parents=True,exist_ok=True)
 # Publish complete projects as a separate release attachment, outside the Git checkout.
 with zipfile.ZipFile(target/'full-body-projects.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
  for rig,prefix in [(0,'mannequin'),(1,'helper-rig')]:
   for kind in ['squat','landing']:
    source=args.input/f'fullbody/rig{rig}-{kind}-v1'
    for name in ['source.trickster','result.trickster','source.glb','result.glb','result.fbx','expected.json']:
     path=source/name
     if path.exists():archive.write(path,f'{prefix}-{kind}/{name}')
    for name in [f'{prefix}-{kind}-source.trickster',f'{prefix}-{kind}-result.trickster',f'{prefix}-{kind}-import.glb']:
     previous=target/name
     if previous.is_file():previous.unlink()  # Only this publisher's previous generated copies.
print('Wrote',args.output/'physics-reliability-results.json')
