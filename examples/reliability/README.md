# Full-body reliability experiments

Download [full-body-projects.zip](https://github.com/Atmosaero/Trickster/releases/download/v0.5.0/full-body-projects.zip) and its [SHA-256 file](https://github.com/Atmosaero/Trickster/releases/download/v0.5.0/full-body-projects.zip.sha256) separately. The archive is not part of the checkout or runtime ZIP. Extract it, then open `source.trickster` or `result.trickster` in a case folder.

- `mannequin-{squat,landing}`: 21 bodies / 66 DOF with independent torso/arms.
- `helper-rig-{squat,landing}`: changed proportions/local bases and four helpers.
- Each case includes complete source/result projects, frozen native controls/MJCF, GLB/FBX and evaluator references. Geometry is original synthetic MIT-licensed content; no private assets are included.

These are **approximate experiments**, not certified dynamics. Contact, goal, end-rest, boundary and centered baked-inverse failures remain separately reported. Original project bytes are preserved; opening them in a newer editor does not certify them.

Regenerate with `TricksterReliabilityTests fullBodyImportedExperiments -o artifacts/reliability-fullbody.txt,txt`, then `python scripts/report-physics-reliability.py --publish-examples`. Generated material stays under `artifacts/reliability-publication`. See [Testing](../../docs/TESTING.md), [methods/limits](../../docs/PHYSICS_RELIABILITY.md) and [fixed tolerances](../../docs/PHYSICS_ACCEPTANCE.md).
