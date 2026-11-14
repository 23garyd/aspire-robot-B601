# ASPIRE 机器人适配的恢复与演示边界

整理日期：2026-11-14。本次整理技术文档及无硬件测试，没有新增物理演示。

| 功能 | 实现 | 验证材料 |
|---|---|---|
| 有界运动与结果状态 | [motion](../../../robot_b601/motion.py)、[node](../../../robot_b601/node.py)、[limits](../../../robot_b601/limits.py) | [运动测试](../../../tests/b601/test_motion_fake.py)、[27 项测试输出](verification/2026-11-14-tests.txt) |
| 传输协议与轨迹 | [transport](../../../robot_b601/transport.py)、[engine](../../../robot_b601/engine.py) | [传输测试](../../../tests/b601/test_transport.py)、[既有交接记录](../../../.project_notes/CLAUDE_HANDOFF.md) |
| 未来链路测试工具 | [50 Hz probe](../../../scripts/link_probe.py) | 工具代码不等于 Wi-Fi／Bluetooth／NearLink 的实测比较 |
| 实机执行入口 | [入口](../../../scripts/b601_real_first_light.py)、[假驱动](../../../scripts/b601_fake_vendor_driver.py) | 历史软件路径验证；真实台架工作仍待完成 |

27 项测试验证的是软件与假驱动行为，不代表已完成安全中止、无线故障恢复或第二项工业场景演示。本仓库的 ASPIRE pipeline 与 HarnessVLA 的 ACT pipeline 分开列示，不能把另一个仓库的 B601 视频当作本 pipeline 已在实机完成的证明。

[implementation-commits.csv](implementation-commits.csv) 给出相关实现提交，[manifest.csv](manifest.csv) 校验本目录。
