"""Convert a local TestCharacter source folder. Originals are never modified."""
from pathlib import Path
import argparse, json, shutil, subprocess, tempfile
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',type=Path,required=True,help='Folder containing TestCharacter.tscn, FBX and Animations/')
parser.add_argument('--godot',type=Path,required=True,help='Compatible Godot editor executable')
parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parent.parent/'library'/'TestCharacter')
args=parser.parse_args()
root=Path(__file__).resolve().parent.parent
artifacts=root/'artifacts';artifacts.mkdir(exist_ok=True)
source=args.source.resolve();engine=args.godot.resolve();output=args.output.resolve()
if not (source/'TestCharacter.tscn').is_file(): parser.error('TestCharacter.tscn was not found')
if not engine.is_file(): parser.error('Godot executable was not found')
if output==source or source in output.parents: parser.error('Output must be outside the original asset folder')
with tempfile.TemporaryDirectory(prefix='character-conversion-',dir=artifacts) as folder:
    stage=Path(folder).resolve()
    if artifacts.resolve() not in stage.parents: raise RuntimeError('Conversion stage escaped artifacts directory')
    shutil.copytree(source,stage/'Models'/'TestCharacter',ignore=shutil.ignore_patterns('*.import'))
    (stage/'project.godot').write_text('config_version=5\n[application]\nconfig/name="Trickster conversion"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n',encoding='utf-8')
    commands=[[str(engine),'--headless','--editor','--path',str(stage),'--import'],[str(engine),'--headless','--path',str(stage),'--script',str(root/'scripts'/'export-godot-character.gd'),'--','res://Models/TestCharacter/TestCharacter.tscn',str(output)]]
    with (artifacts/'character-conversion.log').open('w',encoding='utf-8') as log:
        for command in commands:
            result=subprocess.run(command,capture_output=True,timeout=180,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            log.write((result.stdout+result.stderr).decode('utf-8',errors='replace'))
            if result.returncode: raise RuntimeError('Godot conversion failed; see artifacts/character-conversion.log')
print(json.dumps({'output':str(output),'resources':len(json.loads((output/'catalog.json').read_text(encoding='utf-8'))['entries'])}))
