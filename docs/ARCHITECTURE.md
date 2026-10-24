# Trickster architecture

Current release: **0.5.0**, from CMake. Project schema **8** reads schemas **1-8**. Product and data-format versions are independent.

## Ownership and dependencies

`TricksterCore` links Qt Core/Gui, ufbx and native MuJoCo 3.3.7; it does not link Qt Widgets, OpenGLWidgets or the UI library. `TricksterMVPTests` uses QCoreApplication. Numerical evaluation, project I/O, edit operations, recovery and physics run without a window or OpenGL context. `TricksterUI` adds Qt Widgets, OpenGLWidgets and Network.

`Workspace` owns persistent `Document` instances with immutable UUIDs. Each document owns scene data, QUndoStack/clean index, revision, selection, frame, playback timer and output path. QUndoGroup follows the active document. Switching tabs changes the active pointer and rebinds Viewport/Timeline; it neither serializes scenes nor reconstructs histories/copies geometry. Cameras belong to the presentation. Source clip arrays are shared immutable objects; Qt image byte storage and QMap key storage retain their implicit sharing. Scene geometry is still ordinary value data when explicitly duplicating/staging a scene; there is no general asset database.

`Document` supplies the gesture transaction: begin, commit, cancel, one Undo entry, revision and notifications. Undo payloads contain editable state, profiles/layers/contacts and shared source clips, not mesh vertices/images. Explicit SceneSession snapshot helpers remain for legacy compatibility/tests; the workspace never uses them for tab switching.

`EditService` owns validated scene operations (FK/IK, pins, keys, profiles, layers, limits, contacts and physics parameters). Inspector and typed MCP edits call this service; viewport gestures use Document transactions and the same Scene pose/correction functions and validation. Batches stage all operations and commit once. Window owns native presentation, dialogs, action binding and pending widget input. EditorApi has no friend access to Window or private widget members. Its desktop adapter still references public presentation operations for camera, screenshots and generic UI automation; domain edits do not require a Window.

## Evaluation and editing

`evaluator.cpp`: source channels/sample keys → authored source curves → ordered correction layers and their curves → limits, pins and timed contacts → final pose. `motion.cpp` evaluates sparse keyed additive tracks and captures only changed channels. Rendering, diagnostics, export and physics targets call Scene::evaluate. Native glTF source seconds and LINEAR/STEP/CUBICSPLINE interpolation remain authored data. FBX takes are sampled through ufbx. `resampledCopy` evaluates the source at a selected output grid and produces an independent baked scene. Comparison is a view mode; baking/exporting includes enabled corrections even when Original is displayed.

Layers compose in vector order, parent first inside each layer. Local translation is in parent coordinates, local rotation postmultiplies the current local rotation, and scale offsets add locally. World translation is converted through the corrected parent inverse; world rotation premultiplies in scene space using that layer's corrected parent. Missing channels are neutral. Per-node sparse tracks linearly interpolate translation/scale/morphs and shortest-path slerp rotations; endpoint values hold within the envelope. Constraints follow all layers.

Capture solves affected ancestors first and explicitly inverts layers above the selected layer. It does not store neighboring layers in the selected one. Raw evaluation and the gesture's change relative to its constrained starting pose prevent unrelated constraint results being captured. Unsupported rotations beyond the shortest quaternion domain at partial influence produce a diagnostic; use Strength 1 outside fades. A conflict with contacts/limits can still prevent the final desired pose and is diagnosed separately.

`profile.cpp` uses stable node indices for reviewed humanoid roles, helper-aware root/bend/end IK chains, poles and mirror pairs. Name recognition only suggests initial bindings. `posing.cpp` defines directed hinge/swing-twist limits; the MuJoCo model preserves hinge axes/endpoints and separately measures its three-axis swing approximation; contact constraints preserve orientation when enabled, leave limits active and report residuals.

## Worker lifetime and persistence

`PhysicsJobs` owns a plain-data snapshot, worker, atomic progress/cancel and one result. It records source document UUID/revision. Switching tabs preserves the target; editing or closing that source invalidates the result. Workers never touch documents/widgets. UI-thread polling finalizes once. Applying copies a ready result into a new Document; status polling does not copy geometry. Window destruction requests cancellation; the service joins before its workspace is destroyed.

`RecoveryStore` writes separate QSaveFile snapshots for dirty committed documents, including unsaved ones. A pending gesture is not snapshotted. Recovery opens an unsaved new document with no original output path. Save/discard removes its associated recovery file. Original files are never autosave targets. Standard project saving is atomic through QSaveFile. A subprocess abrupt-exit test and a separate Qt recovery workflow exercise this path.

## Rendering and interoperability

Viewport is QOpenGLWidget with persistent indexed VBO/IBOs, eight-weight GPU skinning, cached morph staging and a CPU fallback, plus a native Qt control overlay. Cache invalidation follows document binding, edits and selection. Timeline shows immutable source events separately from selected-layer keys, copy/move/delete/navigation and contact bands. Graph Editor authors scalar/SO(3)/Euler and layer/IK channels; native imported channels remain inspectable and immutable.

`gltf.cpp` retains textures/materials, sparse/strided accessors, eight skin influences and morphs; exports sampled TRS/weights. `fbx_export.cpp` writes independent FBX 7.4 curves, skinning and blend shapes with texture sidecars. The independent Godot validator compares skin joints, world matrices when provided, and bidirectional CPU-deformed point clouds, including imported blend shapes. Matching importer bake FPS and disabling compression/track removal are precision-test settings, not changes to the export.


## MuJoCo tools

`mujoco_backend.cpp` privately owns compiled MJCF, RAII mjSpec/mjModel/mjData and node/body/joint/site maps. Each task has independent mutable data and never mutates a compiled model. `whole_body.cpp` uses site/COM Jacobians and tangent-space updates; `flight.cpp` solves COM boundaries and angular momentum; `dynamics_optimizer.cpp` optimizes legal control knots through repeated forward integration. `physics_settings.cpp` parses shared UI/MCP settings. `physics_ui.cpp` is presentation only. `physics_telemetry.cpp` records the actual CPU/OS and process peak memory. The renderer remains Qt/OpenGL.

Reports and source identity persist in project schema 6 and later as `physicsResult`, without native engine pointers/caches. Physics authoring marks old validation stale; Undo restores the prior report. Worker results remain bound to the source UUID/revision. Contact forces, native forward/inverse consistency, sampled-motion residuals, goal deviations and replay errors are distinct. See PHYSICS.md, PHYSICS_MIGRATION.md and the fixed PHYSICS_ACCEPTANCE.md criteria.

`physics_provenance.cpp` records input/model hashes and portable settings plus compressed, bounded native control replay data. `physics_replay.cpp` independently reconstructs body momenta/contact impulses and verifies replay without the evaluator/backend conversion/inverse dynamics. The standalone verifier links only Qt Core and MuJoCo. Authoring requests (goals, budgets, important frames, end rest) persist separately from mechanical parameters and participate in Undo.

## Physics reliability boundaries

`physics_validation.cpp` owns the common-grid centered-pose inverse estimator, represented-motion forward impulse balance and one-sided interval continuity checks. Every measurement records its method version, time grid and scope. The represented-motion check differentiates the actual evaluator poses and recomputes contacts with bounded saved internal controls; it does not substitute saved native velocities or accelerations. Windowed impulse agreement is distinct from continuous point acceleration certification.

`physics_trajectory.cpp` reconstructs poses from native configurations and emits normalized quaternion-component Hermite channels with explicit derivative units. Adaptive event knots retain short contact transients at a nominal result FPS. Ordinary glTF channels can retain their original interpolation. Physics engine-compatible export samples event intervals at four subdivisions and exports linear glTF/FBX tracks, because an independent consumer can resample cubic quaternion tracks at its nominal import FPS. Export sample times use canonical float seconds to avoid duplicate glTF timestamps. Extra keys are reported.

`preservePhysicsTimebase` retains simulation timestep independently of output FPS and snapshots physical joint definitions before authoring constraints are removed. `physics.jointModel` is the backend source when present. Qt/MCP directed-limit edits use the same edit service and update this physical definition explicitly. A result remains stale after authored model/evaluator changes.

`physics_proxy.cpp` creates an independent approximate active-clip copy. It measures scale variation, absorbs constant scale into reference transforms, adjusts inverse binds and unskinned geometry/morph deltas, checks world geometry and rigid model poses, and reports measured mapping error. Original documents and other clips remain available in the source document. Qt provides two comparison viewports, preview FPS and a source-revision guard; MCP exposes the same preparation through `physics_analyze`.

## Scoped timeline and symmetry

Correction keys in schema 7 carry optional per-node channel masks (position=1, rotation=2, scale=4). A missing mask means legacy TRS=7. Each component samples only its own keyed times; removing or retiming Rotation cannot introduce a Position/Scale interpolation knot. Morph tracks remain separate. Shared key operations stage affected nodes/channels and reject collisions atomically, retaining other nodes and morphs. An IK controller row explicitly groups its configured root/mid/end; whole-layer and raw-pose bundles remain visibly distinct.

The Qt timeline resolves the clicked row before hit testing keys. Imported source events are immutable; expanded correction tracks and selected-only navigation share the same scope. Viewport, Outliner, inspector and track labels share Document selection. Symmetry is session state: viewport gestures preview both sides within one Document transaction, and inspector/MCP FK/IK calls mirror through EditService. Reflection uses each pair's rest axes and the moving common ancestor, including pin targets. Missing named side pairs never silently self-reflect. See [Motion editing](MOTION.md) and [Testing](TESTING.md).

Document maintains selection sets with one active bone, retained by session snapshots and persistent Workspace documents. Timeline stores selected key scopes independently of its active insertion row. `key_editing.cpp` canonicalizes overlapping correction scopes into component masks and stages removal/merge so adjacent moves, collisions and clipboard edits remain atomic. Every GUI insertion entry point uses Timeline scope; typed MCP arguments remain explicit. Component symmetry reuses rest-frame reflection with a per-node component mask; explicit pose copy still uses TRS=7. World numeric rotations convert through the current parent global quaternion while project transforms stay local. Selection and presentation state do not change the project format.

## Authored motion and analysis

Schema 8 retains scalar/SO(3)/Euler channels, layer/controller curves, context UUIDs/key attachments and retarget profiles. Evaluation is source/native data, authored source curves, ordered correction layers and their curves, then contacts/IK/limits. Metadata Undo does not rewind animation.

Analysis jobs own immutable snapshots and revision identities, budgets, cancellation and paged output. Trajectory, comparison, geometric validation and retargeting share the evaluator. Results state their measured/approximate/uncertain scope. Directed anatomical domains must be authored; humanoid role bindings do not infer them. Retarget results are independent documents. Notes are metadata, not generated constraints. See [Motion analysis](MOTION_ANALYSIS.md).
