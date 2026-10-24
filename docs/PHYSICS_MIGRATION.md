# Project migration

Trickster 0.5.0 reads project schemas **1-8** and saves schema **8**. Product, project and physics-report versions are independent. Save a copy before opening a new-format project in an older application; saving does not downgrade its schema.

Existing baked keys, source clips, correction layers, morphs, pins, contacts and profile/node IDs are retained. Old physics projects receive a persistent warning about changed recalculation semantics. The redistributable `examples/physics/legacy-v4.trickster` exercises load/save/reopen, preview and export.

## Legacy physics data

| Authored data | Migration meaning |
|---|---|
| Mass, capsule radius/tip, local COM, scale, gravity, ground | Preserved numerically with existing units; MuJoCo receives SI conversions |
| Inertia absent | Analytic capsule estimate, estimated=true; custom SI principal moments/orientation can be authored |
| Bullet restitution | Preserved as archival authored data; not treated as an equivalent MuJoCo parameter |
| Contact response | New explicit time constant 0.01 s and damping ratio 1 by default; this is a new compliant model, not a conversion of Bullet ERP/restitution |
| Friction | Preserved as the sliding coefficient; MuJoCo elliptic contact cone, default torsional/rolling coefficients documented in MJCF |
| Stiffness/damping/max torque | Authored Nm/rad, Nm s/rad and per-axis Nm retained as starting drive settings; numerical responses differ |
| Iterations/substeps/self-collision/Follow | Author preferences retained; Newton solver iterations are not equivalent to Bullet sequential impulses |
| Pins and timed contacts | Authored data retained. Legacy preview starts with externalAnchors=true and reports its constraint forces. New dynamics optimization always uses actual geometry, not welded feet |
| Directed limits | Original axes/asymmetric endpoints retained; the three-hinge swing approximation and exact-domain residual are reported |
| New foot boxes, per-body drive overrides | Absent/zero boxes use the existing capsule; -1 drive values inherit global settings |

Each recalculation owns fresh native data. No Bullet cache or MJB is migrated or required. MJCF can be exported for debugging, while portable Trickster data remains the source of truth. Unsupported animated scale/rigid-offset changes are diagnosed rather than silently distorted. The old animation remains viewable/exportable even when a new physical model cannot represent it.

## Schema 6: physical joint identity

`physics.jointModel` retains the physical directed/ball joint definitions independently of the authoring projection maps. A baked clip can disable authoring projection without turning a physical hinge into a ball joint when reopened. Baking also preserves the numerical integration rate by changing substeps when the output FPS changes. Incompatible rate ratios are diagnosed. The numerical limit is now 512 substeps, exposed through Qt and MCP.

A schema-5 result with a saved replay remains reproducible through its frozen MJCF/control record. If its physical joint definitions were already lost during baking, migration cannot infer them reliably: a persistent warning retains this limitation. No legacy result is reclassified as solved. Recalculate from the source project to generate a current-schema result.

Report schema 2 is separate from project schema 6. Deprecated `beforeRootForceRmsN` / `afterRootForceRmsN` now both refer to the common-grid sampled-animation inverse measurement. Older reports used different domains; their aliases must not be interpreted as a comparable improvement. New consumers should read `measurements`, `validationDomains` and method versions. Native consistency, native impulse replay, represented-motion impulse balance, centered inverse diagnostics, interval boundaries and external consumer checks remain separate.

## Schema 7: independent correction components

Schema 7 adds `channels` to each keyed correction transform: Position=1, Rotation=2, Scale=4, combined with bitwise OR. An absent field means 7, preserving the legacy all-TRS interpolation exactly. The reader rejects zero/unknown masks and orphan mask entries. Keyed morph offsets remain separate and are preserved when moving/deleting only a bone's transform channels. This change does not alter physical joint definitions, result validation domains or the product version. A schema-7 reader cannot open a schema-8 project.

## Schema 8: authored curves and context

Schema 8 stores editable scalar/SO(3)/Euler and layer/controller channels, context annotations with stable UUIDs and key attachments, and reusable retarget profiles. Legacy correction component masks retain their meaning. Missing annotation/curve data is not synthesized into motion or constraints. Notes are metadata; free text never creates a physical contact or successful validation result.

The reader retains older motion semantics. Saving writes schema 8; builds supporting only schemas 1-7 cannot reopen that file. Physics report schema 2 and the frozen native MJCF/control record retain their separate interpretation. No migration promotes an approximate/stale result to solved.
