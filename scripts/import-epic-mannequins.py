"""Copy local Epic mannequin assets into an isolated Unreal project; export unanimated GLBs.

Source assets are never changed. Outputs stay in the ignored local library.
Requires an installed Unreal editor with PythonScriptPlugin and GLTFExporter.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True, help='Mannequins folder containing Meshes, Materials and Textures')
parser.add_argument('--engine', type=Path, required=True, help='Unreal installation root, e.g. UE_5.8')
parser.add_argument('--asset-root', default='/Game/DeformableSnowSystem/Demo/Characters/Mannequins', help='Original package mount path')
parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent.parent / 'library' / 'EpicMannequins')
parser.add_argument('--resume', action='store_true', help='Reuse existing validated rest GLBs')
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
source, output = args.source.resolve(), args.output.resolve()
editor = args.engine.resolve() / 'Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
for name in ('Manny', 'Quinn'):
    if not (source / 'Meshes' / ('SKM_' + name + '.uasset')).is_file():
        parser.error('Missing full skeletal mesh: ' + name)
if not editor.is_file():
    parser.error('UnrealEditor-Cmd.exe was not found')
mount = Path(args.asset_root.removeprefix('/Game/'))
if not args.asset_root.startswith('/Game/') or '..' in mount.parts:
    parser.error('--asset-root must be an absolute /Game package path')
if output == source or source in output.parents:
    parser.error('Output must be outside the source asset folder')
stage = root / 'artifacts' / 'epic-export'
stage.mkdir(parents=True, exist_ok=True)
shutil.copytree(source, stage / 'Content' / mount, dirs_exist_ok=True)
project = stage / 'TricksterAssetExport.uproject'
project.write_text(json.dumps({'FileVersion': 3, 'Plugins': [
    {'Name': name, 'Enabled': True} for name in ('PythonScriptPlugin', 'GLTFExporter')
]}, indent=2), encoding='utf-8')
output.mkdir(parents=True, exist_ok=True)
config = stage / 'export-config.json'
config.write_text(json.dumps({'asset_root': args.asset_root, 'output': str(output), 'resume': args.resume}), encoding='utf-8')
env = dict(os.environ, TRICKSTER_EPIC_EXPORT_CONFIG=str(config))
log = stage / 'export.log'
with log.open('w', encoding='utf-8') as stream:
    result = subprocess.run([str(editor), str(project), '-run=pythonscript',
        '-script=' + str(root / 'scripts' / 'export-epic-mannequins.py'),
        '-unattended', '-nop4', '-nosplash', '-AllowCommandletRendering', '-stdout',
        '-FullStdOutLogOutput'], env=env, stdout=stream, stderr=subprocess.STDOUT,
        timeout=1800, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
if result.returncode:
    raise RuntimeError('Unreal export failed; see ' + str(log))
entries = []
for name in ('Manny', 'Quinn'):
    file = output / (name + '.glb')
    with file.open('rb') as stream:
        magic, version, length, json_length, kind = struct.unpack('<5I', stream.read(20))
        document = json.loads(stream.read(json_length))
    if magic != 0x46546C67 or version != 2 or kind != 0x4E4F534A or length != file.stat().st_size:
        raise RuntimeError('Invalid GLB: ' + name)
    if document.get('animations') or not document.get('skins') or not document.get('meshes'):
        raise RuntimeError('Expected a skinned rest mesh without animation: ' + name)
    entries.append({'name': name, 'file': file.name, 'category': 'Characters',
                    'description': 'Epic Games ' + name + '. Rigged rest pose; no animation.'})
(output / 'catalog.json').write_text(json.dumps({'title': 'Epic mannequins', 'entries': entries}, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'output': str(output), 'characters': len(entries), 'log': str(log)}))
