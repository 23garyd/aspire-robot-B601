# ASPIRE 到 reBot B601 的机器人适配

**软件适配与假驱动验证 · Gary 的机器人工程实习项目**

这是 Gary 实习中的 B601 适配层项目。它将机器人原语、ROS 2 厂商协议、动作状态和 TraceRecord 连接起来，先用假驱动验证软件行为，为实体台架联调准备执行入口。

**研究问题：** 如何把 ASPIRE 的同步机器人动作调用，接到 B601 的异步运动、状态反馈和有界执行接口？

**已有结果：** 已提供 B601 引擎、运动状态、ROS 2 协议和执行入口；归档软件检查为27项通过。这些测试没有驱动物理机器人，不能当作实机标定、抓取或完整巡检成功。 [查看原始分析与边界](docs/evidence/oct-m3/README.md)。

## 演示与图像

![B601软件适配结构](docs/portfolio/assets/architecture.svg)

代码结构示意，不是运行截图或实机演示。厂商假驱动用于验证软件边界，实体台架仍待验。 [查看软件测试与证据](docs/evidence/oct-m3/README.md)。

## Gary 的实习工程工作

以下说明项目中的复现、实现、集成与分析工作。上游 ASPIRE／HarnessVLA 的论文方法不作为实习生原创方法；共享代码历史与本次文档整理不重复计为新增实现。

| 工作 | 具体内容 | 可检查入口 |
|---|---|---|
| 建立机器人原语与轨迹接口 | 把 ASPIRE 动作转为 B601 引擎调用，保留可追踪结果。 | [代码或证据](robot_b601/engine.py) |
| 适配 ROS 2 厂商协议 | 分离协议、传输与执行状态，便于替换真实或假驱动。 | [代码或证据](robot_b601/ros_transport.py) |
| 实现运动状态和边界 | 支持有界执行、状态反馈与异常处理；物理安全仍需台架验证。 | [代码或证据](robot_b601/motion.py) |
| 准备实体入口并做假驱动检查 | 入口名称 real 表示面向真实路径；本次归档测试使用假驱动。 | [代码或证据](scripts/b601_real_first_light.py) |

这些材料可供评审检查机器人接口、状态机、实验设计、日志追踪与结果分析能力。实际实现提交见[代码与证据映射](docs/evidence/oct-m3/implementation-commits.csv)，不以证据整理提交替代实现贡献。

## 里程碑与当前状态

| 阶段 | 技术成果入口 | 如何理解完成范围 |
|---|---|---|
| 基础复现与接口准备 | 下方代码目录、[原技术说明](docs/history/agibot-a2-run-guide.md) | 按各项目区分仿真、软件验证和实体实验 |
| October／M3 集成 | [实现与验证索引](docs/evidence/oct-m3/README.md) | 有可复核实现和所列测试，不能推定所有合同条款已验收 |
| November／M4 比较 | [对照与演示索引](docs/evidence/nov-m4/README.md) | 既有结果与失败分析；无线比较和两项工业演示仍有缺口 |
| December／M5 准备 | [复现、归档与后续工程](docs/evidence/dec-m5/README.md) | 准备／部分证据；完整干净机器重建、最终演示和大文件取回尚未闭合 |

月份是交付组织标签，实验日期见原始记录。2026-11-14 的证据整理和无硬件测试不表示当日新增实机或仿真实验。完整说明见[评审阅读指南](docs/portfolio/README.md)。

## 结果限制与后续工作

首次实体动作、真实标定、抓取和 capstone 仍需台架验证。hand_eye 等配置不能因文件存在就认定为真实标定。HarnessVLA 的 B601 视频属于另一条 pipeline，不能作为本仓库的实机证明。

## 代码导航与复核

| 路径 | 内容 |
|---|---|
| `robot_b601/` | B601 引擎、协议、运动状态与边界 |
| `scripts/b601_*` | 台架入口和假厂商驱动 |
| `tests/b601/` | 无硬件测试 |
| `docs/evidence/` | 验证记录和未完成项 |

已有环境中的软件检查入口如下；准确依赖和平台条件按[复现说明](docs/evidence/dec-m5/reproduce.md)配置。本页面整理未重新运行完整实验，也不要求评审者驱动实体机械臂。

```sh
python3 -m pytest tests/b601/ -q -p no:anyio
```

## 四条项目轨道

| 项目 | 研究／验证环境 |
|---|---|
| [ASPIRE 技能积累复现](https://github.com/23garyd/aspire-sim-reproduction) | 仿真研究 |
| [ASPIRE 到 reBot B601 的机器人适配](https://github.com/23garyd/aspire-robot-B601) | 软件适配与假驱动验证 |
| [HarnessVLA 固定策略与外层控制复现](https://github.com/23garyd/harnessvla-sim-reproduction) | LIBERO-Pro 仿真研究 |
| [HarnessVLA 在 reBot B601 上的实机实验](https://github.com/23garyd/harnessvla-rebot-b601) | B601 实机研究与工程验证 |

四个仓库是相关但不同的复现和工程项目，结果不混算。原始论文与框架归属见仓库中的引用及许可说明。商业审批报告、发票和付款信息不属于本技术展示页。
