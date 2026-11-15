# ASPIRE B601 Robot Adapter Technical Index

Prepared on 2026-11-14. Implementation baseline: `1c60803ea71c2250a250f82bc613d771b975a7f0`; the original default branch was `b601_live`.
This update adds technical indexes and no-hardware test records, with no new bench trials or changes to robot control programs.

| Feature | Implementation | Technical evidence |
|---|---|---|
| Agent-to-B601 primitives and TraceRecord | [engine](../../../robot_b601/engine.py), [node](../../../robot_b601/node.py) | [Engine tests](../../../tests/b601/test_engine.py), [test output](verification/2026-11-14-tests.txt) |
| ROS 2 driver protocol adaptation | [ros_transport](../../../robot_b601/ros_transport.py) | [Protocol tests](../../../tests/b601/test_ros_transport.py) |
| Motion execution and outcome states | [motion](../../../robot_b601/motion.py), [limits](../../../robot_b601/limits.py) | [Motion tests](../../../tests/b601/test_motion_fake.py), [integration tests](../../../tests/b601/test_pipeline_integration_real.py) |
| Hardware entry points and fake-driver verification | [Hardware entry point](../../../scripts/b601_real_first_light.py), [fake driver](../../../scripts/b601_fake_vendor_driver.py) | [Entry-point tests](../../../tests/b601/test_b601_execute_real.py), [historical handoff](../../../.project_notes/CLAUDE_HANDOFF.md) |

## Evidence Boundaries

The 2026-07-30 handoff explicitly states that the software path and vendor driver interface passed fake-driver checks; physical first motion, calibration, real grasping and the capstone still require bench validation. The word `real` in a filename identifies the implementation path under test, not physical robot movement during a test.

The [2026-11-14 test output](verification/2026-11-14-tests.txt) records 27 passing tests; they did not move a physical robot. Historical configurations such as `robot_b601/hand_eye.json` must be interpreted using the original handoff, not treated as real calibration results merely because the files exist.

This repository provides the ASPIRE-to-B601 adapter implementation. It cannot substitute for ACT hardware trials in the HarnessVLA B601 repository or establish that both pipelines have been jointly validated as one system.

The old A2 simulation instructions are now in the [historical guide](../../history/agibot-a2-run-guide.md). The [project overview](../../../README.md), this index and `robot_b601/` are the current B601 entry points.

[manifest.csv](manifest.csv) records hashes for the technical documents and verification records added here.

[implementation-commits.csv](implementation-commits.csv) maps each feature to its implementation files, the historical commits that last changed them, code links at the full baseline, and artifact paths. Historical implementation commits remain separate from evidence-packaging commits so documentation work is not presented as new implementation.
