# CLAUDE_HANDOFF — ASPIRE

_Last updated: 2026-07-14 (late) — two tracks now._

## Track 2 result (2026-07-16): TREND REPRODUCED — M3 pilot complete

**The reproduction's core claim landed.** Against our own M1 CaP-Agent0 baseline
(runs/2026-07-15-m1-baseline-pilot/): two_arm_handover 30% -> **100%** (5/5 held-out,
via evosearch round-1 after the Stage-1 repair failed), two_arm_lift 10% -> **100%**
(single trace-guided repair). Paper's headline was 20% -> 92%. Full artifacts:
runs/2026-07-16-m3-aspire-pilot/ (results.json, skills, winner programs, ledger).
G5 done earlier same day (real CaP-X run_episode + golden trace + first live e2e run,
runs/2026-07-15-first-live-e2e/). Infra on epyc: LLM proxy launcher ~/start_llm_proxy.sh
(Anthropic OpenAI-compat, temperature patch in cap-x clone — diff archived at
docs/patches/), M1 script scripts/m1_baseline.sh (TRIALS=100 for paper scale),
M3 launcher ~/start_m3.sh. Remaining ideas: scale-up runs (TRIALS=100 / more val seeds),
M4 LIBERO-Pro + transfer study, per-seed replay affordance for actors (both live actors
filed BLOCKED.md about it), SOW M2 link work (NearLink kits + probe).

## Track 2 (superseded heading): gap-fix program G1–G4 + G6 COMPLETE — 149 tests

Third-party review (`docs/review_codex.md`) gap analysis vs the paper → 6-phase fix plan
(`docs/superpowers/plans/2026-07-15-review-codex-gap-fixes.md`). Executed with
subagent + two-stage review; every phase had a fix-first round, all re-approved:
- **G1** AuditedEngine choke point (every program audited incl. validation), judge dedup.
- **G2** Task dir materialized (traces/, task.md, skills.md via failure-token retrieval).
- **G3** Trace-conditioned evosearch (history carries summaries, task_analysis.md ledger,
  history_note), winner bundle durable BEFORE VALIDATION_DONE.
- **G4** ExtractValidatedPatterns (extraction actor over winner bundle); admission bound
  to the WINNING round's report (critical endswith bug caught in review); best-effort
  extraction; ranked dedup.
- **G6** Aliasing fix (validate a stable winner/program.py copy), BLOCKED.md + stale
  clear, seed-attempt discipline, EXTRACTION_FAILED marker, findings.md, --tasks-root
  campaign with progress.json.
- **G5 (remaining, P0)**: wire run_episode() to real CaP-X on epyc + golden trace +
  one real end-to-end Robosuite task. BLOCKED on connectivity: epyc lives on the
  Tailscale overlay (10.10.5.x); Tailscale on the Mac is STOPPED — start it from the
  menu bar, then check /etc/hosts (10.10.5.26) vs ~/.ssh/config (10.10.5.102) and fix
  the stale pin before rsync + m0_rig_up.sh.

## Track 2 (original): ASPIRE reproduction on original sim — branch `aspire_original_sim`

Spec: `docs/superpowers/specs/2026-07-14-aspire-original-sim-design.md`. Plan (14 TDD
tasks): `docs/superpowers/plans/2026-07-14-aspire-original-sim.md`. Executed via
subagent-driven development: every task group spec-reviewed + quality-reviewed; 5
fix-first rounds, all re-approved.

**Built (all on the branch):** `aspire/` package — config ([RECONSTRUCTED] K/T/θ,
logged per run by the CLI), schemas (pinned result.json / report.json contracts), audit
(forbidden-API wall), markdown skill library, engines (FakeEngine + CapxEngine subprocess
boundary), actors (headless `claude -p` wrappers, shim-tested; exact yes/no judge),
evosearch (Algorithm 1, atomic checkpoints, crash-resume), coordinator (single-use S_val
with STARTED/DONE/TAINTED markers, resume short-circuit, audit→judge admission),
`python -m aspire.run` CLI (clean JSON line, exit 2 on domain errors). `prompts/` (3
files, verbatim Appendix E excerpts + [RECONSTRUCTED] markers). `scripts/capx_execute.py`
(GPU-box runner half of the engine contract, --selftest), `scripts/m0_rig_up.sh`,
`scripts/m1_baseline.sh` (CAPX_MODEL mandatory). **93 tests green on Mac AND epyc**
(box needs `-p no:anyio`); contract selftest verified on epyc.

**Next operational steps (M0→M3):**
1. On epyc: `cd ~/aspire_robot_engine && ./scripts/m0_rig_up.sh` — installs CaP-X,
   GPU smoke, selftest; then the guided step: wire `run_episode()` in
   `scripts/capx_execute.py` to the real CaP-X API, capture the golden episode, add the
   golden regression test (`tests/aspire/golden/`).
2. `CAPX_MODEL=<confirmed id> ./scripts/m1_baseline.sh` — OUR CaP-Agent0 baseline
   numbers into `~/aspire_runs/m1_baseline/results.json`.
3. M2: real actor runs via `python -m aspire.run --engine capx ...` per task — requires
   materializing task context (traces/, skills.md, task.md) in the runner (documented
   gap, see backlog). M3: evosearch on plateaued tasks (bimanual handover headline),
   compare vs results.json.

**M2 backlog (from reviews, all documented in code):** coordinator ignores
`report.outcome` (a fail-report without fix_code.py surfaces as EngineError, exit 2 —
should skip execution instead); task-context materialization (traces/skills.md/task.md)
is the runner's job; evosearch M1 note (`_run_dir` multi-run generality unused);
CapxEngine M2/M3 deferred minors (stdout buffering, stale result.json across restarts
— mitigated by numbered exec dirs per instance).

---

## Track 1: AgiBot A2 execution layer — branch `aspire_a2_sim` (DONE, stable)

_Last updated: 2026-07-14_

## Mission

Implement the robot-execution layer of the **ASPIRE** paper (`Aspire.pdf`, 43 pp, read in
full) on the **octos** agentic OS, driving a **live AgiBot A2** (26-joint bimanual humanoid)
**simulation**. Prove the full pipeline end-to-end: agent-facing sync API → traced primitives
→ transport → commanded joint move on the standing robot.

ASPIRE = 3 layers: (1) robot execution engine with per-primitive multimodal traces,
(2) skill library, (3) evolutionary search. This work builds **layer 1** and the transport
wall down to the A2.

## Current status — WORKING / SOLVED, migrated to new box `epyc`

**2026-07-14: migrated to the new sim box `epyc` (10.10.5.102). Package pushed, whole stack
re-verified from a cold start. Nothing outstanding.**

The full stiff commanded arm move runs end-to-end on the live A2 sim:
- Robot stands (Load-key keyframe init), holds `RL_LOCOMOTION_DEFAULT` balanced.
- Enters `RL_LOCOMOTION_ARM_EXT_JOINT_SERVO`, arm tracks commanded position and stays
  balanced. Joint limit ~1.65 rad on `idx14_left_arm_joint2` (matches old box's 1.657).
- **27/27 unit tests pass** on Mac and on `epyc` (needs `-p no:anyio` there).
- `scripts/start_a2_sim.sh` now runs cold-start → `ROBOT STANDING` → arm move, **exit 0**.

The old box (192.168.1.152) is gone — the network hunt in the previous handoff is moot.

Two docs now exist for operators:
- `README.md` (repo root) — the run guide (created this session).
- `octos/octos_aspire.md` (Obsidian, "octos" folder) — design notes, feasibility, API spike.

## Ground-truth facts (hard-won, do not re-derive)

- **A2 uses HTTP-RPC on `:56322`, NOT ROS2 topics**, for actions/state.
  URL form: `http://{host}:56322/rpc/aimdk.protocol.{Service}/{Method}`.
  Services: `McActionService` (SetAction/GetAction/GetAvailableActions),
  `McDataService/GetJointState`, `McMotionService`, `McBaseService/GetState`.
- **Arm joint commands DO go over ROS2**: topic `/motion/control/arm_joint_command`,
  `sensor_msgs/JointState`, **BEST_EFFORT** QoS. 14 arm joints
  `idx13_left_arm_joint1..idx26_right_arm_joint7`.
- **SetAction envelope**: `{"command":{"action":"McAction_USE_EXT_CMD","ext_action":"<ACTION>"}}`.
- **FSM path** (`action_manager/default.yaml`, `allow_action_indirect_transition: false`):
  `DEFAULT → STAND_UP → RL_JOINT_DEFAULT → (Load key) → RL_LOCOMOTION_DEFAULT →
  RL_LOCOMOTION_ARM_EXT_JOINT_SERVO`.
- **"Load key" is mandatory**: loads the `home_default` keyframe (base z=0.95) via MuJoCo's
  `mj_resetDataKeyframe`. No keyboard shortcut → automated with `xdotool` pixel click at
  `(68,547)` on the Xvfb `:99` framebuffer. Without it the robot reverts to DEFAULT and falls.
- **`RL_LOCOMOTION_ARM_EXT_JOINT_SERVO` has a sub-1s deadman watchdog**: must stream arm
  setpoints (50 Hz) BEFORE entering and keep streaming, or it faults back to DEFAULT.
- **A2 sim lacks** camera, grasp, IK, and reward interfaces (relevant to ASPIRE layers 2/3).

## Key decisions

- **Transport abstraction via DI**: `RosTransport` Protocol with `FakeRosTransport` (tests) and
  `RclpyTransport` (live). `AimdkNode` is a sync facade over it. Enables TDD without hardware.
- **Injectable clock** (`clock.py`, RealClock/ManualClock) so blocking poll loops are testable.
- **`move_to_joints` streams the setpoint every poll iteration** (not once) — required by the
  joint-servo deadman.
- **TDD throughout** (Red-Green-Refactor); mocks only at the transport boundary.
- Deliberately did **not** touch `/home/demo/run.txt` (sudo password) — security.

## Changed / created files (this project)

**Engine (`robot_engine/`)**: `clock.py`, `ros_transport.py`, `aimdk_node.py`, `trace.py`,
`tracing.py`, `robot_engine.py`, `rclpy_transport.py`, `a2_rpc.py`, `a2_ros_binding.py`.

**Examples (`examples/`)**: `live_a2_arm_move2.py` (**VERIFIED** move; assumes standing),
`live_a2_arm_move.py` (stands robot itself), `a2_servo_probe.py`, `a2_mode_probe.py`,
`live_a2_readloop.py`, `live_a2_commanded_move.py`, `run_demo.py`.

**Tests (`tests/`)**: `test_a2_ros_binding.py`, `test_a2_rpc.py`, `test_aimdk_node.py`,
`test_rclpy_transport.py`, `test_robot_engine.py`, `test_trace.py` (27 total).

**Scripts**: `scripts/start_a2_sim.sh` — one-command bring-up + stand.

**Docs (this session)**: `README.md`, `.project_notes/CLAUDE_HANDOFF.md`.

## Commands run (canonical)

```bash
# Unit tests (any machine, no robot):
python3 -m pytest -q                       # 27 pass

# Live bring-up on Ubuntu box:
cd ~/aspire_robot_engine && ./scripts/start_a2_sim.sh   # wait for "ROBOT STANDING"

# Verified arm move (in container):
docker exec -u 0 a2-ultra-sim bash -c \
  'source /opt/ros/humble/setup.bash; cd /tmp/aspire; \
   PYTHONPATH=.:$PYTHONPATH python3 examples/live_a2_arm_move2.py'

# Inspect standing screenshot:
docker cp a2-ultra-sim:/tmp/stand.png ./stand.png

# Manual iceoryx purge (post-reboot):
docker exec -u 0 a2-ultra-sim bash -c \
  'rm -f /tmp/iox* /tmp/*.lock; rm -rf /dev/shm/iceoryx* /dev/shm/iox*'
```

## Environments

- **Mac** (dev, this box): runs unit tests only; no ROS2. Repo at `/Users/Shared/github_aspire`.
- **`epyc` — the sim box** (`ssh demo@epyc`, **key-based, no password**; 10.10.5.102, reachable
  over the VPN/Tailscale tunnel `utun15`; box also has Tailscale IP 100.107.163.59).
  ROS2 Humble + `a2-ultra-sim` container (`mujoco_sim_ultra_1.3`, `motion_control_ultra_1.3.26`
  — same versions as the old box). Package at `~/aspire_robot_engine/` (persistent), re-staged
  to `/tmp/aspire` (container, ephemeral) by the startup script.
  - **Do NOT force password auth** — `-o PubkeyAuthentication=no` breaks the login.
  - Container needed `xvfb xdotool imagemagick x11-utils` installed (done). Writable layer:
    survives `docker start/stop`, lost on `docker rm`.
  - pytest there needs `-p no:anyio` (stray `~/.local` anyio plugin breaks system pytest).

## Bugs found & fixed on migration (2026-07-14)

1. **`GetAction` had no `Content-Type` header** (`start_a2_sim.sh` lines 25/39). curl defaults to
   `x-www-form-urlencoded`, which aimrt rejects outright → the script could never read the action,
   silently printed an empty `current action:` and claimed `ROBOT STANDING` regardless. Fixed via
   a `getact()` helper that always sends `application/json`.
2. **`pkill -9 motion_control` does not match the process** — only `pkill -9 -f "[m]otion_control"`
   (full cmdline) does. A stale `motion_control` survived every restart, kept `:56322` bound (so
   "RPC up" looked fine) while its iceoryx link to the killed RouDi was dead → `SecurityGuard:
   HAL data is lost` and **every SetAction refused**. This was the real cause of the failed
   bring-up. Purge now uses `-f` + `[b]racket` trick (avoids self-kill) and **verifies zero
   survivors**.
3. **Script claimed success unconditionally.** Now verifies each step and exits non-zero:
   fails if RPC absent, if `RL_JOINT_DEFAULT` won't engage, or if the robot doesn't **hold**
   `RL_LOCOMOTION_DEFAULT` for 5s (SecurityGuard reverts within ~1s of a fall, so surviving 5s
   is the real proof it's standing). Settle times lengthened 2s→3s / 3s→4s.

## Gotchas worth keeping

- **`Load key` must be clicked while the controller is ACTIVE** (`RL_JOINT_DEFAULT`). Clicking it
  in passive `DEFAULT` resets the robot to standing and it immediately flops — nothing holds it.
- **After `Load key` the robot leaves the camera view** (teleports to origin; camera still points
  where it fell). Not a fault — verify via RPC, never the camera.
- The `terminate called without an active exception` / core dump at the end of
  `live_a2_arm_move2.py` is the **known-benign rclpy double-shutdown**, fires after work completes.

## Unresolved issues

1. Camera/grasp/IK/reward interfaces absent in this A2 sim — limits ASPIRE layers 2 (skill lib)
   and 3 (evolutionary search) until a richer sim or real hardware is available.
2. Container tooling (xvfb/xdotool/imagemagick) lives only in the writable layer — a `docker rm`
   loses it. Worth a `docker commit` or a Dockerfile if the container is ever recreated.

## Next steps

1. (Longer term) build ASPIRE layer 2 (skill library) atop the traced primitives; investigate a
   sim variant exposing camera/grasp for layer 3.
2. Optionally `docker commit` the container so the installed tooling survives a recreate.
