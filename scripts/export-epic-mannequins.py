"""Unreal Python worker for import-epic-mannequins.py; exports rest meshes only."""
import json
import os
import struct
from pathlib import Path
import unreal

config = json.loads(Path(os.environ['TRICKSTER_EPIC_EXPORT_CONFIG']).read_text(encoding='utf-8'))
options = unreal.GLTFExportOptions()
options.export_uniform_scale = 0.01
options.export_vertex_skin_weights = True
options.export_animation_sequences = False
options.export_level_sequences = False
options.export_vertex_colors = False
options.use_mesh_quantization = False
options.default_level_of_detail = 0
options.bake_material_inputs = unreal.GLTFMaterialBakeMode.USE_MESH_DATA
options.default_material_bake_size = unreal.GLTFMaterialBakeSize(x=1024, y=1024, auto_detect=False)
options.texture_image_format = unreal.GLTFTextureImageFormat.PNG
reports = []
for name in ('Manny', 'Quinn'):
    destination = Path(config['output']) / (name + '.glb')
    if config.get('resume') and destination.is_file():
        with destination.open('rb') as stream:
            header = struct.unpack('<5I', stream.read(20))
            document = json.loads(stream.read(header[3]))
        if (header[0] == 0x46546C67 and header[1] == 2 and header[2] == destination.stat().st_size
                and header[4] == 0x4E4F534A and document.get('skins') and document.get('meshes')
                and not document.get('animations')):
            reports.append({'name': name, 'success': True, 'reused': True,
                            'warnings': ['Reused an existing validated skinned rest GLB.'], 'errors': []})
            continue
    asset = unreal.load_asset(config['asset_root'] + '/Meshes/SKM_' + name)
    if not isinstance(asset, unreal.SkeletalMesh):
        raise RuntimeError('Missing skeletal mesh: ' + name)
    # Unreal Python treats the native bool return as an optional-result flag:
    # success returns GLTFExportMessages; failure returns None.
    messages = unreal.GLTFExporter.export_to_gltf(asset, str(destination), options, set())
    success = messages is not None and destination.is_file()
    report = {'name': name, 'asset': asset.get_path_name(), 'success': success,
              'warnings': list(messages.warnings) if messages else [],
              'errors': list(messages.errors) if messages else ['Exporter returned no result']}
    reports.append(report)
    print('TRICKSTER_EPIC_EXPORT', json.dumps(report))
    if not success or report['errors']:
        raise RuntimeError('glTF export failed: ' + name)
Path(config['output'], 'export-report.json').write_text(json.dumps(reports, indent=2) + '\n', encoding='utf-8')
