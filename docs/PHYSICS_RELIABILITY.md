# Physics reliability and limitations

Physics is **experimental**. The supported MVP workflow is manual posing/correction. In the recorded full-body study, **62 gates remain open**: 12/12 calculations, 12/12 baked kinematics, 1/12 native control, 0/12 baked dynamics, 1/12 interval boundaries and 0/12 solved results. These are failed criteria, not skipped cases. Editor/UI/MCP regressions are independent of scientific acceptance.

## Measurement domains

- Native forward/inverse consistency checks the engine's own state; it is not independent evidence.
- Independent native replay sets qpos once, applies saved bounded internal controls and sums COM/orbital/spin momentum against gravity and measured ground impulses. It does not call inverse dynamics.
- Baked kinematics measures the actual saved evaluator trajectory and round trips.
- `centered-pose-inverse/1` uses sampled pose derivatives on a stated common grid. Before/after comparisons must share estimator, model, sampling and scope. Impact under-resolution remains visible.
- `represented-forward-impulse/2` differentiates actual evaluator poses and recomputes contacts under frozen internal controls. Windowed balance is not continuous point-acceleration or motor-feasibility certification.
- Interval boundaries and independent external geometry/dynamics are separate gates. Geometric export agreement alone does not prove dynamics.

Reports retain method versions, grids, source/model hashes, settings, budgets, stop reasons and measured CPU/process peak memory. Peak memory is the process high-water mark, not isolated task allocation. Mechanical models, goals, contact schedules and duration stay fixed during optimization. No root-force residual is zeroed or applied as an actuator.

## Confirmed boundaries

The historical seven-body squat and landing native traces reproduce geometry, but common-grid centered inverse force RMS remains about **608.82 N / 83659 N** after correction. Landing is worse on this estimator. Accurate configuration round trips and reopened curves did not remove these residuals. Finite-difference controls calibrate the smooth regime; compliant impacts still require explicit resolution/representation studies.

Refining the numerical timestep and using adaptive quaternion Hermite event keys improves represented window balance on seven-body examples. This is a controlled convergence study, not proof for full-body rigs or arbitrary derivatives. Uniform linear/cubic and adaptive curves retain different errors.

Full-body experiments use two imported synthetic rigs (21 bodies/66 DOF), differing proportions/local bases and helpers, with independently moving arms/torso. The nominal first-rig squat passes native control/goal/rest checks; other variants and the full takeoff/flight/landing case retain open goal/rest/boundary/dynamics gates. Bounded support-control seeds and landing-reference preparation are local heuristics, not planners.

Constant active scale differing from rest may be prepared as an explicit measured rigid proxy. Animated nonrigid transforms can remain unsupported. The source stays intact. Fitting estimated masses or accepting a geometry-preserving proxy does not validate human biomechanics.

## Independent consumer

Measured Godot 4.7.2 checks compare joints, matrices and deformed geometry with a fixed **1-mm geometry tolerance**. Import FPS, compression and retained keys are part of the evidence. Refined landing GLB regeneration loses event density and fails a matrix criterion despite sub-millimetre geometry. Full-body nominal landing GLBs also exceed geometry/matrix tolerances; tested FBX geometry agrees more closely. FBX Step conversion has a separate discontinuity failure. These tests do not justify a universal claim about all consumers.

## Reproduce

See [Testing](TESTING.md) for regression, replay and acceptance commands. Full reliability tests generate `artifacts/reliability`, including source/result projects, actual MJCF/controls and failed variants. For refined external measurements, after generation run:

```powershell
python scripts/validate-motion-godot.py --godot 'C:\Tools\Godot\Godot.exe' --basename result --input-dir artifacts/reliability/refined/squat-2 --work-dir artifacts/reliability/independent-refined/squat --bake-fps 60 --trajectory-fps 3840
python scripts/validate-motion-godot.py --godot 'C:\Tools\Godot\Godot.exe' --basename result --input-dir artifacts/reliability/refined/landing-2 --work-dir artifacts/reliability/independent-refined/landing --bake-fps 60 --trajectory-fps 7680
$env:TRICKSTER_RELIABILITY_EXTERNAL_REFINED = '2'
.\build\TricksterReliabilityTests.exe independentImportedDynamics -o artifacts/reliability-external.txt,txt
Remove-Item Env:TRICKSTER_RELIABILITY_EXTERNAL_REFINED
python scripts/check-physics-reliability.py
```

The landing consumer check and acceptance checker return nonzero while criteria fail. Do not omit failures or use `TRICKSTER_RELIABILITY_QUICK=1` for a complete study.

The [evidence archive](https://github.com/Atmosaero/Trickster/releases/download/v0.5.0/Trickster-0.5.0-validation-evidence.zip) preserves original reports/scalars and build identities, including unsuccessful runs. [Synthetic projects](../examples/reliability/README.md) are a separate release download. Only the measured Windows native CPU/OpenGL environment is supported by this evidence; there is no other-platform, GPU-compute or bitwise cross-platform claim. Fixed thresholds remain in [PHYSICS_ACCEPTANCE.md](PHYSICS_ACCEPTANCE.md).
