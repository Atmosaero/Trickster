# Physics acceptance specification (fixed before demonstrations)

SI internally: m, kg, s, N, Nm, kg m/s, kg m²/s. H is rest character height in metres, M is authored total mass, g is authored gravity (normalization uses max(g, 1 m/s²)). World +Y up, ground normal +Y. Position reports include absolute metres and fractions of H. Torque scale M g H, force scale M g; angular momentum scale M H sqrt(g H). No model change is allowed during optimization.

| Quantity | Fixed acceptance tolerance | Reason |
|---|---|---|
| Analytical mass / COM / inertia | relative 1e-5 / 1e-6 m / relative 2e-4 | double engine math, float authoring |
| Pose round trip | 1e-5 H, 0.02 degrees | float transforms and SO(3) conversion |
| Ballistic COM position | max 1e-4 H | analytical trajectory sampled into float keys |
| Flight endpoint velocity compatibility | 0.01 sqrt(g H) | explicit authored boundary tolerance |
| Flight angular momentum drift | 1% of max(initial magnitude, 0.01 momentum scale) | finite-difference segment motion and time integration |
| Whole-body hard support / target | 0.002 H / 0.005 H | millimetre-scale editing precision |
| Whole-body directed joint violation | 0.5 degrees | nonlinear finite iteration solve |
| Physical penetration / planted slip | 0.005 H / 0.01 H | compliant contacts, not welded supports |
| Root inverse force / moment | RMS 0.03 M g / 0.03 M g H; peak 0.10 scales | numerical sampled inverse dynamics and compliant impacts; impacts reported separately |
| Torque limits / unilateral contacts / friction | 1% / normal >= -1e-6 M g / tangential <= 1.02 mu normal | solver precision and friction cone margin |
| Forward rollout position / orientation discrepancy | RMS 0.02 H / 3 degrees; peak 0.05 H / 8 degrees | short interval reproduction with admissible controls |
| Important goal deviation | <= 0.02 H, 5 degrees | preserve intent; duration and schedule unchanged |
| Controlled corruption improvement | >= 30% RMS root residual reduction; meaningful motion preserved | reject zero-motion substitutes |
| Requested end rest (new explicit goal, fixed before testing it) | COM speed <= 0.01 sqrt(g H), maximum segment angular speed <= 0.1 rad/s | small residual motion, separately reported |
| Independent export consumer | max joint/vertex 0.001 m | prior MVP export accuracy threshold |

A kinematic COM/support check is a static hint, never a dynamic certificate. Explicit world anchors are external supports with measured forces, not physical foot contacts. Three-axis joint approximations must report deviation from the editor swing/twist domain; a domain violation cannot be marked solved. Physically checked status requires the dynamics, contact, torque, goal and independent forward checks simultaneously. Approximate and infeasible are distinct from solved. Runtime and peak process memory are measured, not pass thresholds; iteration/time budgets are recorded per run. No bitwise cross-platform claim.


## Current acceptance status

The recorded full-body study remains **incomplete: 62 open gates**. Across 12 imported variations: calculations 12/12, baked kinematics 12/12, native control 1/12, baked dynamics 0/12, interval boundaries 1/12, solved 0/12. Passing editor regressions does not close these scientific gates.

Static posing, ballistic COM and flight angular-momentum checks have their own narrower scope. Native control replay, represented-motion window balance and centered sampled inverse diagnostics are separate measurements. Supported squat/landing results remain approximate where baked inverse residuals fail. No threshold above has been relaxed.

[Physics reliability](PHYSICS_RELIABILITY.md) explains methods and known failures. [Testing](TESTING.md) lists reproduction commands. Original per-case tables, hardware/resources, input hashes and raw scalar reports are preserved in the [historical evidence archive](https://github.com/Atmosaero/Trickster/releases/download/v0.5.0/Trickster-0.5.0-validation-evidence.zip); complete synthetic projects are a [separate attachment](../examples/reliability/README.md). These records identify their stated builds; they are not new certification of 0.5.0.
