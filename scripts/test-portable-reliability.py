#!/usr/bin/env python3
"""Windows local executable smoke through its authenticated MCP endpoint; no client SDK needed."""
import argparse, ctypes, json, os, subprocess, time, urllib.request
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--executable',type=Path,default=Path('build/Trickster.exe'))
p.add_argument('--source',type=Path,default=Path('artifacts/reliability/fullbody/rig0-squat-v1/source.trickster'))
p.add_argument('--output',type=Path,default=Path('artifacts/reliability/portable'))
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);config=(a.output/'connection.json').resolve()
if config.exists():config.unlink()
env=os.environ.copy();windir=env.get('WINDIR','C:/Windows');env['PATH']=windir+'/System32;'+windir
for key in ('QT_PLUGIN_PATH','QML2_IMPORT_PATH'):env.pop(key,None)
checks=[];process=None
with (a.output/'stdout.txt').open('wb') as stdout,(a.output/'stderr.txt').open('wb') as stderr:
 try:
  process=subprocess.Popen([str(a.executable.resolve()),'--mcp','--mcp-port','0','--mcp-config',str(config)],env=env,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
  for _ in range(200):
   if config.exists():break
   if process.poll() is not None:raise RuntimeError(f'Editor exited: {process.returncode}')
   time.sleep(.05)
  connection=json.loads(config.read_text(encoding='utf-8-sig'))['mcpServers']['trickster']
  opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
  def rpc(method,params={}):
   headers=dict(connection['headers']);headers.update({'Content-Type':'application/json','Accept':'application/json, text/event-stream','MCP-Protocol-Version':'2025-11-25'})
   request=urllib.request.Request(connection['url'],json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params}).encode(),headers)
   with opener.open(request,timeout=60) as response:result=json.load(response)
   assert 'error' not in result,result.get('error')
   return result['result']
  rpc('initialize',{'protocolVersion':'2025-11-25','capabilities':{},'clientInfo':{'name':'PortableReliabilitySmoke','version':'1'}})
  tools=rpc('tools/list')['tools'];assert len(tools)>=42;checks.append(f'{len(tools)} tools discovered')
  def call(name,arguments={}):
   r=rpc('tools/call',{'name':name,'arguments':arguments});assert not r.get('isError'),r
   return r.get('structuredContent',{})
  state=call('editor_state',{'nodes':False});assert state['nodeCount']==0;checks.append('default empty startup')
  call('scene',{'operation':'open','path':str(a.source.resolve())});call('physics_analyze',{'operation':'measure'});checks.append('full-body source load and native model measurement')
  call('physics_analyze',{'operation':'proxy_preview'});call('physics_analyze',{'operation':'proxy_create'});checks.append('explicit proxy preview/create')
  output=(a.output/'project.trickster').resolve();call('scene',{'operation':'save','path':str(output)})
  assert json.loads(output.read_text())['version']==8
  for ext in ('glb','fbx'):
   destination=(a.output/f'project.{ext}').resolve();call('scene',{'operation':'export','path':str(destination)});assert destination.stat().st_size>1000
  checks.append('schema-8 project save and GLB/FBX export')
  call('scene',{'operation':'switch','index':0});call('scene',{'operation':'switch','index':1});checks.append('proxy scene/camera switching')
  call('editor_action',{'id':'mcpStopAction'});time.sleep(.15)
  stopped=False
  try:rpc('tools/list')
  except (OSError,urllib.error.URLError):stopped=True
  assert stopped;checks.append('MCP Stop disconnects')
  user32=ctypes.windll.user32
  @ctypes.WINFUNCTYPE(ctypes.c_bool,ctypes.c_void_p,ctypes.c_void_p)
  def close_owned_window(hwnd,_):
   pid=ctypes.c_ulong();user32.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
   if pid.value==process.pid and user32.IsWindowVisible(hwnd):user32.PostMessageW(hwnd,0x0010,0,0)
   return True
  user32.EnumWindows(close_owned_window,0);assert process.wait(timeout=15)==0;checks.append('clean window close')
  (a.output/'summary.json').write_text(json.dumps({'passed':True,'executable':str(a.executable),'systemOnlyPath':True,'checks':checks},indent=2)+'\n',encoding='utf8')
  print('PASS:',', '.join(checks))
 finally:
  if process is not None and process.poll() is None:process.terminate();process.wait(timeout=10)
  if config.exists():config.unlink()
