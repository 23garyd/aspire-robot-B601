# CLAUDE_HANDOFF — ASPIRE

_Last updated: 2026-07-18 — work handed over to epyc; continue from there._

## ▣ SESSION SUMMARY (2026-07-18) — compacted

**Status:** Branch `aspire_original_sim` @ `12bc289`, pushed to `aspire_demo`.
`python3 -m pytest tests/ -q -p no:anyio` → **196 passed**. No campaign currently
running (`/tmp/lift_repeats.pid`, `/tmp/traces_ablation.pid` — check before
launching anything). LLM proxy on :8110 launched via `~/start_llm_proxy.sh`.

**What shipped this session (newest first):**
1. **Traces-vs-retry ablation infra** — BUILT + merged, NOT run (needs credits).
   Details in the section just below.
2. **Val-score gate on skill admission** — commit `f306e65`. Skills admitted only
   when held-out val ≥ `cfg.admission_min_val` (default 0.5; 0.0 disables). CLI
   `--admission-min-val`. Closes the M3X-val-0.0 / rep_5-val-0.10 skill-leak.
3. **Lift-repeats variance campaign (N=5)** — `runs/2026-07-17-lift-repeats/`.
   Finding: lift repair is high-variance-not-bimodal (7-run val
   1.0/0.0/1.0/0.95/0.80/0.85/0.10, mean 0.67); M3X 0/20 is the tail, not a fluke.
4. **Before/after demo video** — rendered rep_1 winner (reward 1.00, lifts pot)
   vs baseline (0.01, air-grasp) at seed 100 via CaP-X's frame recorder (no LLM).
   Clips in `runs/2026-07-17-lift-repeats/clips/` (+ `~/aspire_runs/lift_repeats/clips/`);
   render tools `scripts/render_clip.py`, `scripts/compose_sidebyside.py`.
5. **M1 deliverable updated** — `~/sow-2026-7-30w/deliverables/M1-Deliverable-Report-DRAFT-2026-07-16.md`
   now carries the honest variance finding + video + evidence index (@ `aa5f720`).
   Also wrote polished status note `~/sow-2026-7-30w/aspire_original_7_17_1.md`.

**Key decisions:** (a) lift-repeats used EMPTY per-repeat libraries + isolated
dirs (i.i.d. variance instrument, not learning). (b) The ablation deliberately
disables evosearch in BOTH arms (`--t 0`) so attribution is to the repair actor
alone; single manipulated variable = trace access. (c) Ablation control arm must
not leak traces at the filesystem level — the opus whole-branch review caught
that the capx replay raw dir sat inside the actor sandbox; fixed by scrubbing it
(`640a80b`).

**Changed/created files this session:** `aspire/config.py` (+ablate_traces,
admission_min_val), `aspire/coordinator.py` (gate + ablation wiring + t=0 guard),
`aspire/task_context.py` (scalar outcome.txt), `aspire/replay.py` (scalar output
+ raw-dir scrub), `aspire/run.py` (CLI flags), `prompts/actor_debug_blind.md`,
`scripts/{traces_ablation.sh,analyze_ablation.py,render_clip.py,compose_sidebyside.py,lift_repeats.sh}`,
`scripts/__init__.py`, tests across `tests/aspire/`, plus specs/plans in
`docs/superpowers/`, `runs/2026-07-17-lift-repeats/`. Home-dir launchers:
`~/start_lift_repeats.sh`, `~/start_traces_ablation.sh` (not versioned).

**Unresolved / watch:** ablation not yet run (credits); M1 deliverable + NearLink
kits + SOW sign-off are user-side; standing code backlog unchanged (coordinator
ignores `report.outcome`, replay-concurrency RMW comment-only, `FakeEngine.describe`
score leak, `_run_dir` unused). Minor deferred from ablation review: Task-4 test
could add an attempts.json assertion (property verified correct, just unlocked).

**Next step (recommended):** when credits are approved, run the ablation
(staged N=5/arm first) — it's the experiment that would prove ASPIRE's trace
layer is causal. Then the skill-transfer test.

## ⚑ RAN — STAGE 1 (2026-07-20): skill-transfer test (layer 2), N=5/arm — NEGATIVE/NULL

Harness built + merged (ec09ae7..f9ce596, spec/plan in `docs/superpowers/`).
**Stage-1 (N=5/arm) ran clean** (10/10, no failures). Results +
logs: `runs/2026-07-19-skill-transfer/results/results.json`.
- **Held-out val, S (seeded w/ 2 handover skills)**: 0.0, 0.25, 0.35, 0.70, 0.90
  — mean **0.44**, median 0.35, P(≥0.80)=0.20.
- **Held-out val, E (empty library)**: 0.0, 0.50, 0.75, 0.90, 1.00 — mean
  **0.63**, median 0.75, P(≥0.80)=0.40.
- **Mann-Whitney U(S vs E)=8.0, z=-0.946** — the SEEDED arm ranks LOWER. No
  metric favors seeding; the point estimate is a (non-significant) NEGATIVE
  transfer. Not significant either way (same variance wall as the ablation).
- **VERDICT: no evidence ASPIRE's skill layer transfers across these tasks** — a
  legitimate negative for layer 2. NOT a plumbing failure: the transfer channel
  fired (verified live — all 5 S reps' skills.md contained both handover skills;
  E's were `(none)`).
- **Likely why**: both arms independently ADMITTED grasp-orientation skills during
  their own runs — the actor re-derives the needed geometry from THIS run's
  traces, so pre-seeded cross-task skills add little. Coheres with the ablation:
  the repair power lives in per-run trace-guided repair, not (yet demonstrably)
  in cross-task skill accumulation.
- **Recommend**: do NOT brute-force N (a null/negative is unlikely to flip). If
  pursued, redesign (positive control with a genuinely-missing-info skill +
  a target the actor can't solve from its own traces; paired seeds). Report the
  honest negative.
- Mechanism recap: seed fixture `runs/2026-07-19-skill-transfer/seed_library/`
  (handover-only); launcher `scripts/skill_transfer.sh`; analysis
  `scripts/analyze_skill_transfer.py`.

## ⚑ RAN — FINAL (2026-07-19): traces-vs-retry ablation, N=8/arm — SUGGESTIVE, NOT CONCLUSIVE

Infra built + merged (64bf8f5..640a80b, 196 tests). Full ablation ran clean
(16/16 runs across staged N=5 then +3, no credit/crash failures). Results +
logs: `runs/2026-07-18-traces-ablation/results.json`.
- **Held-out val, T (traces), n=8**: 0.05,0.15,0.30,0.80,0.90,0.90,0.95,1.00 —
  mean **0.63**, median 0.85, P(≥0.80)=**0.62** (5/8).
- **Held-out val, C (retry / --ablate-traces), n=8**: 0.00,0.05,0.10,0.20,0.35,
  0.60,1.00,1.00 — mean **0.41**, median 0.275, P(≥0.80)=**0.25** (2/8).
- **Primary test (pre-registered Mann-Whitney U)**: NOT significant. N=5 z=0.949
  p≈0.17; N=8 U=39.5 z=0.791 p≈0.21 — and z did NOT grow with N (variance
  dominates; both arms occasionally hit 1.0 and often ~0).
- **VERDICT**: traces lead on every summary stat (mean +0.22, median +0.58,
  ~2.5x the rate of a strong val≥0.80 program) — a consistent, moderate effect —
  but the rank test can't separate the arms at N≤8 and isn't converging. Honest
  read: **suggestive, not proven; not a null either.**
- **DO NOT brute-force N** (≈30–35/arm for p<0.05, ~60–70 runs, no guarantee). If
  a hard result is needed, redesign for power: paired seeds to cancel task
  variance, a lower-variance task, or a pre-declared binary "strong-program"
  proportion test. Otherwise the effect-size finding stands.
- Bonus (validated live over 16 runs): the val-score gate (f306e65) admitted
  zero skills on every val<0.5 repeat; t=0 confirmed (no evosearch either arm).
- Mechanism recap: `RunConfig.ablate_traces` / CLI `--ablate-traces` swaps the
  repair actor's per-primitive traces for a scalar `outcome.txt` + scalar
  `./replay` (blind prompt `prompts/actor_debug_blind.md`); `--t 0` off evosearch.
  Control-arm trace-leak (replay raw dir in sandbox) closed pre-run (640a80b).

## ✔ DONE (2026-07-18): lift-repeats variance campaign — 5/5 complete

TODO #2 complete: **N=5 campaign repeats on two_arm_lift**, the variance
instrument for the pilot-5/5 vs M3X-0/20 contradiction. Spec:
`docs/superpowers/specs/2026-07-17-lift-repeats-variance-design.md`. Runner
`scripts/lift_repeats.sh`; full results + archived logs in
`runs/2026-07-17-lift-repeats/`. (Ran across two sessions: reps 1-2 on
2026-07-17, then the Anthropic account ran out of credits mid-campaign; after a
top-up, reps 3-5 were wiped and re-run FRESH — the exit-2 failures on the first
attempt were credit exhaustion, NOT experiment outcomes.)

- **FINDING — lift repair is genuinely high-variance but NOT bimodal.** Held-out
  val scores across 7 independent runs (pilot, M3X, rep_1..5):
  **1.0, 0.0, 1.0, 0.95, 0.80, 0.85, 0.10** (mean 0.67). 5/7 land a strong
  program (val ≥ 0.80); 2/7 land in the weak tail (≤ 0.10). **M3X's 0/20 was
  NOT a fluke or a bug — it is the extreme end of a real continuous
  distribution, and rep_5 (0.10) independently reproduced the weak tail.** The
  representative outcome is strong-but-imperfect (median val ~0.85); neither
  extreme is "the truth."
- **Mechanism split**: Stage-1 trace-guided repair alone solved 3/5 (rep 1,2,4,
  all val ≥ 0.85). Evosearch was the winner on the 2 harder repeats — rescued
  rep_3 to 0.80, but plateaued on rep_5 (dbg 0.667, val 0.10). Evosearch
  reduces but does not eliminate the weak tail.
- **Reinforces backlog "val-score gate on admission"**: rep_5 admitted 4 skills
  at val 0.10 (M3X did the same at val 0.0). Two data points now argue for
  gating skill admission on the winning round's validation score.

## ⚑ HANDOVER TO EPYC (2026-07-17) — read this first

Development moves from the Mac to **epyc** (user will work via remote desktop).
Everything needed to continue lives on the box:

**Where things are on epyc**
- `~/aspire_robot_engine/` — THE repo, now a full git checkout (`.git` synced from the
  Mac), branch `aspire_original_sim`. **Canonical remote: `aspire_demo` =
  https://github.com/23garyd/aspire_demo — push/pull there.** (`origin` =
  23garyd/aspire_a2_sim is a legacy mirror; ignore it.) Run Claude Code from this
  directory.
- `~/cap-x/` — CaP-X clone, submodules initialized, `uv sync --extra robosuite` done,
  LLM-proxy temperature patch applied (diff archived at `docs/patches/`).
- `~/aspire_runs/` — all live-run state (golden, m1_baseline, m3, m3x, r3_*).
- `~/sow-2026-7-30w/` — SOW business folder (execution-map spec, M1 deliverable DRAFT,
  link-probe measurement); synced from the Mac, local-only git repo (no remote).
- Launcher scripts in `~/`: `start_llm_proxy.sh` (run FIRST for any LLM campaign; it
  extracts ANTHROPIC_API_KEY from ~/.bashrc because the export sits after the
  interactivity guard), `start_m1.sh`, `start_m3.sh`, `start_m3x.sh`,
  `start_link_echo.sh`. Pattern: launch detached daemons via an on-box script
  (inline `ssh setsid` dies with session teardown); liveness via pidfile
  (`kill -0 $(cat /tmp/<name>.pid)`), never `pgrep -f` (self-match trap).
- `claude` CLI at `~/.local/bin/claude` (works). `gh` at /usr/bin/gh, authenticated
  as **23garyd** (verified 2026-07-17, `gh auth setup-git` done): plain
  `git push aspire_demo aspire_original_sim` works directly from epyc. All git
  work uses user **23garyd** and repo **https://github.com/23garyd/aspire_demo**.

**Sanity check after taking over** (from `~/aspire_robot_engine/`):
`git log --oneline -1` matches GitHub; `python3 -m pytest tests/ -q -p no:anyio`
→ 196 passed (the `-p no:anyio` flag is required on this box).

**TODO queue (user-facing, in priority order)**
1. *User-side, blocking*: review the M1 deliverable report draft
   (`~/sow-2026-7-30w/deliverables/M1-Deliverable-Report-DRAFT-2026-07-16.md`) — two
   open decisions: include ASPIRE 100%/95% numbers at that detail level? offer
   Futurewei reviewers repo access? Also: order NearLink dev kits (WS63/BS21-class);
   optionally sign off the SOW execution-map spec.
2. ✔ DONE (2026-07-18): campaign repeats (N=5) on two_arm_lift — see the DONE
   section at the top. Result: lift repair is high-variance-not-bimodal; M3X 0/20
   was the tail, not a fluke.
3. ✔ DONE (2026-07-17): validation-score gate on skill admission. Skills admitted
   only when held-out val >= `cfg.admission_min_val` (default 0.5, 0.0 disables);
   gate precedes extraction (no wasted tokens), writes `ADMISSION_GATED` marker,
   CLI `--admission-min-val`. Commit f306e65, 184 tests. Closes the M3X-val-0.0 /
   rep_5-val-0.10 skill-leak.
4. *Deferred scale-up*: TRIALS=100 baseline re-run (expensive); M4 LIBERO-Pro +
   LIBERO-90→Long transfer study; BEHAVIOR-1K stretch.
5. *Watch*: NVIDIA ASPIRE open-source release — diff the `[RECONSTRUCTED]` markers
   in `aspire/config.py` when it lands.

**Standing code backlog** (tracked in plan docs): coordinator ignores
`report.outcome`; replay-concurrency RMW is comment-only; `FakeEngine.describe`
leaks scripted scores (test-only); `_run_dir` multi-run generality unused.

## Track 2 update (2026-07-16 late): replay affordance + M3X extended validation

**Replay affordance shipped** (spec/plan docs 2026-07-16): actors get `./replay <prog>
<seed>` (App E inner loop) — budgeted 3/seed, audited, S_val structurally unreachable.
Live-validated end-to-end; first-ever actor runs with outcome "success" and no
BLOCKED.md. R3 caught two only-live bugs: shim PYTHONPATH trailing-colon dual-import;
seed_attempts shape crash (the G2-predicted one). 182 tests.

**M3X (n=20 validation, replay-equipped actors)** — runs/2026-07-16-m3x-extended-validation/:
- handover: baseline 30% → **95% (19/20)**, Stage-1 ONLY (replay replaced evosearch —
  cheaper AND stronger than the pilot).
- lift: **0/20 this run** vs 5/5 in the pilot — same baseline, different session:
  agentic-repair variance dominates the hardest task; both debug rounds (9/9 replay
  attempts each) and 15 search candidates all failed. Honest finding, in the results.
- Backlog: consider val-score gate on skill admission (a skill was admitted from a
  val-0.0 run); campaign repeats (N runs/task) are the right instrument for variance.

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
