# ASPIRE Adapter for reBot B601 — Reading Guide

This guide connects the research question, implementation, evidence and limitations. See the [project overview](../../README.md) for demos and a summary.

## Current Scope

This project connects ASPIRE robot primitives, the ROS 2 vendor protocol, motion states and TraceRecord to a B601 adapter. Software behavior is checked with a fake driver before physical bench integration. AgiBot A2 belongs to an earlier simulation execution-layer trial; B601 is the current adaptation target, and the old A2 run guide is retained as historical documentation.

The B601 engine, motion states, ROS 2 protocol and execution entry points are implemented. Archived software checks report 27 passing tests. These tests did not move a physical robot and do not establish real calibration, grasping or a complete inspection task.

Physical first motion, real calibration, grasping and the capstone still require bench validation. The presence of hand_eye or other configuration files is not proof of real calibration. HarnessVLA B601 videos belong to a separate pipeline and cannot establish hardware execution for this repository.

## Software Architecture

![Software architecture illustration](assets/architecture.svg)

The diagram explains code boundaries. Claims about execution and measured behavior remain limited to the evidence described below.

## Work and Attribution

This project reproduces existing research and provides engineering implementation, experiments and analysis. Upstream paper methods remain attributed to their authors. The [implementation commit map](../evidence/oct-m3/implementation-commits.csv) separates code contributions from evidence packaging. The two ASPIRE repositories share history; identical files or simulation clips are not counted as separate achievements. This documentation update adds reading guidance and media entry points, with no new training, rollouts or robot actions.

## Evidence Levels

| Evidence | Supports | Does not establish |
|---|---|---|
| Source code and no-hardware tests | Interfaces, control logic, error handling and some boundaries | Physical arm motion, real calibration or physical safety |
| Simulation results and videos | Behavior in the specified simulated environment, conditions and examples | Physical B601 performance or industrial deployment |
| Hardware results, video and telemetry | The shown physical trial and its recorded outcome | Other pipelines, other tasks or unmeasured wireless performance |
| Pinned commits and hashes | Traceable source files and auditable packaged versions | Experiment timing, task success or final contractual acceptance |

See [media-provenance.json](media-provenance.json) for sources. Where present, preview images are frames extracted directly at 1 second from existing videos; generated imagery does not replace experimental footage. Architecture diagrams are explanatory illustrations, not execution evidence.

## Stages and Evidence

[October / M3](../evidence/oct-m3/README.md), [November / M4](../evidence/nov-m4/README.md) and [December / M5](../evidence/dec-m5/README.md) retain their technical scope and outstanding items. Original experiment dates are not reassigned to delivery months.

Repository access permissions are unchanged. Technical pages do not contain invoices, commercial contracts or payment information.
