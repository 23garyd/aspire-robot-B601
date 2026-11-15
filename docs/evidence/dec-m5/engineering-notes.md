# Technical recommendations and follow-up engineering for robot adaptation

References: [B601 engine](../../../robot_b601/engine.py), [Motion backend](../../../robot_b601/motion.py), and [historical handoff records](../../../.project_notes/CLAUDE_HANDOFF.md).

- Keep the algorithm layer separate from the driver/transport layer, and record actions using consistent state, result, and trajectory structures. Fake drivers support software verification but do not replace physical calibration, first motion, or safety demonstrations.
- Check physical driver units, joint names, action rejection, and timeouts individually; an entry script containing real does not imply that all of its tests use a physical robot.
- Verify placeholders in the original hand_eye and other configurations against the handoff records; video of another ACT pipeline cannot serve as bench evidence for this ASPIRE pipeline.

Follow-up engineering: Complete the arm zero-position conventions, gripper units, camera calibration, and controlled first motion; retain the actual run configuration, telemetry, and video; then verify the end-to-end ASPIRE repair loop. Only code and hardware-free software evidence are currently provided.
