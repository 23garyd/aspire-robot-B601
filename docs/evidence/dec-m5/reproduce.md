# Technical notes on reproduction and archiving

Preparation date: 2026-11-14. This directory supports preparation of the December technical delivery; it does not establish December acceptance or completion of all final work.

Checked-out source commit: `7d2f78efcba0299d01aaa3cf29e35b44ebc2791a`. For every code file and existing attachment, [archive-manifest.csv](archive-manifest.csv) provides a pinned GitHub link, byte count, and SHA-256. The archive covers all tracked files in that source commit; it excludes the newly created dec-m5 directory itself, whose integrity is recorded separately in [manifest.csv](manifest.csv) to avoid circular hashes.

```bash
git clone https://github.com/23garyd/aspire-robot-B601.git
cd aspire-robot-B601
git checkout 7d2f78efcba0299d01aaa3cf29e35b44ebc2791a
```

Paths in the archive CSV are relative to the repository root. Verify each item using SHA-256 after downloading/checking out; the evidence directory Git attributes protect file bytes. The repository remains private, and access uses existing authorization.

[Test commands and actual output from the existing environment](../nov-m4/verification/2026-11-14-tests.txt) establish only that the specified hardware-free software subset runs. Prepare the full software dependencies, GPU, vendor SDK, models, and raw data separately according to the [repository documentation](../../../README.md) and the original environment lock files.

This work checked out code from the existing private source and verified attachments and a software subset; it did not rebuild the full system on a clean machine or verify that a third party can independently launch physical experiments. Do not execute physical robot entry points directly on an unmeasured/uncalibrated machine; the current software checks do not require powering on the arm.

The [historical handoff records](../../../.project_notes/CLAUDE_HANDOFF.md) list pending bench validation and placeholder configurations; do not describe existing fake-driver tests as completion of physical first motion. The vendor ROS workspace is an external dependency and requires a separately pinned version.
