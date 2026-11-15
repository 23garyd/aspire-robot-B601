# Recovery and Demonstration Boundaries of the ASPIRE Robot Adapter

Prepared on 2026-11-14. This update packages technical documents and no-hardware tests, with no new physical demonstration.

| Feature | Implementation | Verification material |
|---|---|---|
| Bounded motion and outcome states | [motion](../../../robot_b601/motion.py), [node](../../../robot_b601/node.py), [limits](../../../robot_b601/limits.py) | [Motion tests](../../../tests/b601/test_motion_fake.py), [27-test output](verification/2026-11-14-tests.txt) |
| Transport protocol and traces | [transport](../../../robot_b601/transport.py), [engine](../../../robot_b601/engine.py) | [Transport tests](../../../tests/b601/test_transport.py), [existing handoff record](../../../.project_notes/CLAUDE_HANDOFF.md) |
| Tools for future link tests | [50 Hz probe](../../../scripts/link_probe.py) | Tool code is not a measured Wi-Fi / Bluetooth / NearLink comparison |
| Hardware execution entry point | [Entry point](../../../scripts/b601_real_first_light.py), [fake driver](../../../scripts/b601_fake_vendor_driver.py) | Historical software-path verification; physical bench work remains outstanding |

The 27 tests check software and fake-driver behavior. They do not establish a physical safety abort, wireless fault recovery or a second industrial scenario demonstration. The ASPIRE pipeline and HarnessVLA ACT pipeline are presented separately; B601 video from the other repository cannot prove physical execution of this pipeline.

[implementation-commits.csv](implementation-commits.csv) lists related implementation commits; [manifest.csv](manifest.csv) checks this directory.
