# ASPIRE B601 机器人适配层技术索引

整理日期：2026-11-14。实现基线：`1c60803ea71c2250a250f82bc613d771b975a7f0`，原默认分支为 `b601_live`。
本次补充技术索引与无硬件测试记录，不新增台架试验或改变机器人程序。

| 功能 | 实现 | 技术证据 |
|---|---|---|
| Agent 到 B601 原语及 TraceRecord | [engine](../../../robot_b601/engine.py)、[node](../../../robot_b601/node.py) | [引擎测试](../../../tests/b601/test_engine.py)、[测试输出](verification/2026-11-14-tests.txt) |
| ROS2 驱动协议适配 | [ros_transport](../../../robot_b601/ros_transport.py) | [协议测试](../../../tests/b601/test_ros_transport.py) |
| 运动执行与结果状态 | [motion](../../../robot_b601/motion.py)、[limits](../../../robot_b601/limits.py) | [运动测试](../../../tests/b601/test_motion_fake.py)、[集成测试](../../../tests/b601/test_pipeline_integration_real.py) |
| 实机入口与假驱动验证 | [实机入口](../../../scripts/b601_real_first_light.py)、[假驱动](../../../scripts/b601_fake_vendor_driver.py) | [入口测试](../../../tests/b601/test_b601_execute_real.py)、[历史交接记录](../../../.project_notes/CLAUDE_HANDOFF.md) |

## 证据边界

2026-07-30 交接记录明确：软件路径与厂商驱动接口已通过假驱动检查，实机首次动作、标定、真实抓取与 capstone 仍需台架验证。文件名中的 `real` 表示被测实现路径，不表示测试实际驱动物理机器人。

[2026-11-14 测试输出](verification/2026-11-14-tests.txt) 记录上述 27 项测试通过；它们没有驱动物理机器人。`robot_b601/hand_eye.json` 等历史配置须按原交接记录理解，不能把占位配置当作实机标定结果。

本仓库证明 ASPIRE 到 B601 的适配实现；不能用它替代 HarnessVLA B601 仓库中的 ACT 实机试验或声称两套 pipeline 已被作为一个系统联合验证。

A2仿真的旧说明已移至[历史指南](../../history/agibot-a2-run-guide.md)；[仓库首页](../../../README.md)、本索引及 `robot_b601/` 是当前B601实现入口。

[manifest.csv](manifest.csv) 记录本目录新增技术文档与检查记录的哈希。

[implementation-commits.csv](implementation-commits.csv) 将每项功能对应到实现文件、最后修改该文件的历史提交、完整基线中的代码链接和附件路径。历史实现提交与本次证据整理提交分别保留，避免把文档整理称作新增实现。
