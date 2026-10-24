#!/usr/bin/env python3
"""Generate reference exports with TricksterMotionTests userMannequinWorkflow first.
Uses only staged copies and does not change the character source or an existing Godot project.
"""
from pathlib import Path
import shutil, subprocess, json, math, itertools, argparse, struct
parser=argparse.ArgumentParser(description="Independently verify the optional HumanM motion export using Godot.")
parser.add_argument('--godot',required=True,type=Path)
parser.add_argument('--bake-fps',type=float,default=30)
parser.add_argument('--trajectory-fps',type=int,default=0,help='Also capture actual imported world bone transforms on a dense grid for dynamics analysis')
parser.add_argument('--basename',default='HumanM-correction')
parser.add_argument('--input-dir',type=Path,default=Path('artifacts/motion-demo'))
parser.add_argument('--work-dir',type=Path,default=Path('artifacts/motion-independent'))
args=parser.parse_args()
if not args.godot.is_file():parser.error('Godot executable not found')

root=args.work_dir;root.mkdir(parents=True,exist_ok=True)
root.joinpath('project.godot').write_text('config_version=5\n[application]\nconfig/name="Trickster motion validation"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
for ext in ['glb','fbx']:
 shutil.copy2(args.input_dir/(args.basename+'.'+ext),root/('motion.'+ext))
side=args.input_dir/(args.basename+'.fbm')
if side.exists():shutil.copytree(side,root/side.name,dirs_exist_ok=True)
shutil.copy2(args.input_dir/'expected.json',root/'expected.json')
root.joinpath('inspect.gd').write_text('''extends SceneTree
var skeletons: Array = []
var meshes: Array = []
var players: Array = []
var trajectories = {}
func visit(node: Node):
    if node is Skeleton3D: skeletons.append(node)
    if node is MeshInstance3D: meshes.append(node)
    if node is AnimationPlayer: players.append(node)
    for child in node.get_children(): visit(child)
func v3(v: Vector3): return [v.x,v.y,v.z]
func _initialize(): call_deferred("inspect")
func inspect():
    var expected = JSON.parse_string(FileAccess.get_file_as_string("res://expected.json"))
    var output = {}
    for ext in ["glb","fbx"]:
        skeletons.clear(); meshes.clear(); players.clear()
        var scene: Node
        if ext == "glb":
            var document = GLTFDocument.new(); var state = GLTFState.new()
            state.bake_fps = BAKE_FPS
            if document.append_from_file("res://motion.glb",state,64|16) != OK: quit(2); return
            scene=document.generate_scene(state,BAKE_FPS,false,false)
        else:
            var document = FBXDocument.new(); var state = FBXState.new()
            state.bake_fps = BAKE_FPS
            if document.append_from_file("res://motion.fbx",state,64|16) != OK: quit(2); return
            scene=document.generate_scene(state,BAKE_FPS,false,false)
        root.add_child(scene); visit(scene)
        if players.is_empty(): quit(3); return
        var player: AnimationPlayer = players[0]
        var animation_name = ""
        for name in player.get_animation_list():
            if name != "RESET": animation_name = name; break
        if animation_name.is_empty(): quit(4); return
        player.get_animation(animation_name).loop_mode = Animation.LOOP_NONE
        player.play(animation_name)
        var frames = []
        for frame in expected:
            player.seek(frame.seconds,true); player.advance(0)
            var joints = {}; var transforms_by_name = {}; var vertices = []
            for skeleton in skeletons:
                skeleton.force_update_all_bone_transforms()
                for i in skeleton.get_bone_count():
                    var transform = skeleton.global_transform*skeleton.get_bone_global_pose(i)
                    joints[skeleton.get_bone_name(i)] = v3(transform.origin)
                    var b = transform.basis
                    transforms_by_name[skeleton.get_bone_name(i)] = [b.x.x,b.x.y,b.x.z,0,b.y.x,b.y.y,b.y.z,0,b.z.x,b.z.y,b.z.z,0,transform.origin.x,transform.origin.y,transform.origin.z,1]
            for mesh_node in meshes:
                var skeleton = mesh_node.get_node_or_null(mesh_node.skeleton) as Skeleton3D
                var skin: Skin = mesh_node.skin
                for surface in mesh_node.mesh.get_surface_count():
                    var arrays = mesh_node.mesh.surface_get_arrays(surface)
                    var points: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
                    # Apply imported blend shapes before CPU skinning, using the actual imported mode.
                    var shapes = mesh_node.mesh.surface_get_blend_shape_arrays(surface)
                    var basis_points = points.duplicate()
                    for shape in mesh_node.mesh.get_blend_shape_count():
                        var amount = mesh_node.get_blend_shape_value(shape)
                        if absf(amount) < 0.0000001: continue
                        var deltas: PackedVector3Array = shapes[shape][Mesh.ARRAY_VERTEX]
                        for i in points.size():
                            points[i] += deltas[i]*amount if mesh_node.mesh.blend_shape_mode == Mesh.BLEND_SHAPE_MODE_RELATIVE else (deltas[i]-basis_points[i])*amount
                    var bones: PackedInt32Array = arrays[Mesh.ARRAY_BONES] if arrays[Mesh.ARRAY_BONES] != null else PackedInt32Array()
                    var weights: PackedFloat32Array = arrays[Mesh.ARRAY_WEIGHTS] if arrays[Mesh.ARRAY_WEIGHTS] != null else PackedFloat32Array()
                    var transforms = []
                    if skeleton != null and skin != null:
                        for bind in skin.get_bind_count():
                            var bone = skin.get_bind_bone(bind)
                            if bone < 0: bone = skeleton.find_bone(skin.get_bind_name(bind))
                            if bone < 0: quit(5); return
                            transforms.append(skeleton.global_transform*skeleton.get_bone_global_pose(bone)*skin.get_bind_pose(bind))
                    var influences = int(bones.size()/maxi(1,points.size()))
                    for i in points.size():
                        var p = Vector3.ZERO; var total = 0.0
                        if not transforms.is_empty() and influences > 0:
                            for j in influences:
                                var weight = weights[i*influences+j]
                                if weight > 0:
                                    p += (transforms[bones[i*influences+j]]*points[i])*weight; total+=weight
                            if total > 0: p/=total
                            else: p=mesh_node.global_transform*points[i]
                        else: p=mesh_node.global_transform*points[i]
                        vertices.append(v3(p))
            frames.append({"seconds":frame.seconds,"joints":joints,"transforms":transforms_by_name,"vertices":vertices})
        output[ext]=frames
        if TRAJECTORY_FPS > 0:
            var dense = []
            var duration = player.current_animation_length
            var count = int(round(duration*TRAJECTORY_FPS))
            for i in range(count+1):
                var time = minf(duration,float(i)/maxi(1,TRAJECTORY_FPS))
                player.seek(time,true); player.advance(0)
                var transforms = {}
                for skeleton in skeletons:
                    skeleton.force_update_all_bone_transforms()
                    for bone in skeleton.get_bone_count():
                        var t = skeleton.global_transform*skeleton.get_bone_global_pose(bone)
                        var b = t.basis
                        transforms[skeleton.get_bone_name(bone)] = [b.x.x,b.x.y,b.x.z,0,b.y.x,b.y.y,b.y.z,0,b.z.x,b.z.y,b.z.z,0,t.origin.x,t.origin.y,t.origin.z,1]
                dense.append({"seconds":time,"transforms":transforms})
            trajectories[ext]=dense
        scene.queue_free(); await process_frame
    var file = FileAccess.open("res://observed.json",FileAccess.WRITE)
    file.store_string(JSON.stringify(output,"",true,true)); file.close()
    if TRAJECTORY_FPS > 0:
        var trajectory_file = FileAccess.open("res://trajectory.json",FileAccess.WRITE)
        trajectory_file.store_string(JSON.stringify({"consumer":Engine.get_version_info().string,"sampleFps":TRAJECTORY_FPS,"bakeFps":BAKE_FPS,"formats":trajectories,"captureMethod":"godot-world-transforms-full-precision/2"},"",true,true))
        trajectory_file.close()
    print("Independent skeleton and CPU skin samples written")
    quit(0)
'''.replace('BAKE_FPS',str(args.bake_fps)).replace('TRAJECTORY_FPS',str(args.trajectory_fps)))
exe=str(args.godot.resolve())
for command in [[exe,'--headless','--path',str(root.resolve()),'--editor','--import'],[exe,'--headless','--path',str(root.resolve()),'--script','res://inspect.gd']]:
 r=subprocess.run(command,capture_output=True,timeout=120);root.joinpath('import.log' if '--editor' in command else 'inspect.log').write_bytes(r.stdout+r.stderr)
 print('Godot exit',r.returncode,(r.stdout+r.stderr).decode(errors='replace')[-1200:])
 if r.returncode:raise SystemExit(r.returncode)
expected=json.loads((root/'expected.json').read_text());observed=json.loads((root/'observed.json').read_text())
exported=(root/'motion.glb').read_bytes();length=struct.unpack_from('<I',exported,12)[0]
asset=json.loads(exported[20:20+length]);required={asset['nodes'][n]['name'] for skin in asset['skins'] for n in skin['joints']}
def distance(a,b):return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
def cloud_error(source,target,tol=.001):
 bins={}
 for v in target:bins.setdefault(tuple(math.floor(x/tol) for x in v),[]).append(v)
 worst=0
 for v in source:
  key=tuple(math.floor(x/tol) for x in v)
  candidates=itertools.chain.from_iterable(bins.get(tuple(a+b for a,b in zip(key,d)),[]) for d in itertools.product([-1,0,1],repeat=3))
  error=min((distance(v,c) for c in candidates),default=float('inf'))
  if not math.isfinite(error) and target:error=min(distance(v,c) for c in target)
  worst=max(worst,error)
 return worst
summary={}
for ext,frames in observed.items():
 assert len(frames)==len(expected) and len(frames)>=5
 joint_error=0;geo_error=0;matrix_error=0;count=0
 for ref,got in zip(expected,frames):
  assert abs(ref['seconds']-got['seconds'])<1e-6
  common=ref['joints'].keys()&got['joints'].keys();assert len(common)>=len(required),(ext,len(common))
  assert required<=common,(ext,required-common)
  count=len(common);joint_error=max(joint_error,max(distance(ref['joints'][n],got['joints'][n]) for n in common))
  if 'transforms' in ref:
   matrix_error=max(matrix_error,max(abs(a-b) for n in required for a,b in zip(ref['transforms'][n],got['transforms'][n])))
  geo_error=max(geo_error,cloud_error(ref['vertices'],got['vertices']),cloud_error(got['vertices'],ref['vertices']))
 summary[ext]={'frames':len(frames),'bones':count,'max_joint_error_m':joint_error,'max_vertex_error_m':geo_error,'max_transform_component_error':matrix_error,'consumer_bake_fps':args.bake_fps,'consumer_method':'state-bake-fps-before-append-and-generate/2'}
 summary[ext]['passed']=joint_error<.001 and geo_error<.001 and matrix_error<.001
 print(ext,summary[ext])
(root/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False))
if not all(m['passed'] for m in summary.values()):raise SystemExit('Independent import PARTIAL: see summary.json')
print('Independent import PASS')
