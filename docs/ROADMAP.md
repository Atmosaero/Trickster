# Roadmap

Current release: 0.5.0. The supported workflow is manual posing and motion correction, curve authoring, analysis, retargeting and export. Physics remains experimental. Versions change for planned releases, not individual tasks; see [CHANGELOG.md](../CHANGELOG.md).

## Priorities

Open work is tracked in [GitHub Issues](https://github.com/Atmosaero/Trickster/issues).

1. [Physics reliability #1](https://github.com/Atmosaero/Trickster/issues/1): close physical reliability gates on imported full-body squat, landing and takeoff/flight/landing: native goal/end-rest tracking, represented/baked dynamics, interval boundaries and independent consumer dynamics. Keep existing tolerances and failed evidence. Recorded status: **62 open gates, 0/12 solved full-body variants**.
2. [Independent consumers #2](https://github.com/Atmosaero/Trickster/issues/2): preserve continuous motion and derivatives through bake/reopen/export. Resolve the Godot GLB event/matrix discrepancy and FBX Step compatibility without hiding failed consumers.
3. [Rig calibration #3](https://github.com/Atmosaero/Trickster/issues/3): improve reviewed rig setup: calibrated directed anatomical joint domains, explicit permitted contacts and retarget calibration. Current diagnostics do not infer human anatomical validity. Automatic spine/twist redistribution and general contact/balance planning are not implemented.
4. [Group editing #4](https://github.com/Atmosaero/Trickster/issues/4): extend editing usability: reusable user track groups and shared-pivot group manipulation. Continue compact/high-DPI checks and selection/Undo consistency.
5. [Deployment/platforms #5](https://github.com/Atmosaero/Trickster/issues/5): validate clean-machine installation, more hardware and other platforms before expanding support claims. Performance claims require reproducible CPU/GPU measurements.

Scientific acceptance and user-facing behavior have separate checks. See [Physics reliability](PHYSICS_RELIABILITY.md), [Motion analysis](MOTION_ANALYSIS.md) and [Testing](TESTING.md). This roadmap contains outstanding work. Historical measurement evidence is preserved separately in the release attachments.
