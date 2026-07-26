"""Real B601-RS transport over ROS 2 against the vendor reBotArmController_ROS2
driver, behind the SAME B601Transport seam (so B601Node/B601Engine are unchanged).
rclpy + message imports are DEFERRED (inside connect/publish) so this module and its
pure helpers import and test WITHOUT ROS 2. Every command is clamped to joint limits
before the wire (safety).

Vendor interface (source-verified 2026-07-26 from reBotArmController_ROS2, built at
../../rebotarm_ros2):
  state:      /{ns}/joint_states        sensor_msgs/JointState, names
              [joint1..joint6, gripper_joint1, gripper_joint2] (arm radians; the
              gripper_joint* entries are METERS, converted by the driver). Joint
              order is NOT guaranteed -- always key off msg.name.
  gripper:    /{ns}/gripper/state       rebotarm_msgs/JointMotorState, MOTOR units
              (RS: close=0.0, open=5.0 per rebotarm_hardware.yaml).
  arm cmd:    /{ns}/follow_joint_trajectory
              control_msgs/action/FollowJointTrajectory (the vendor-blessed path;
              their examples/move_to.py does exactly this). The driver REJECTS arm
              goals while a trajectory is running, so publish() retries rejected
              goals on the next re-stream tick.
  gripper cmd: /{ns}/gripper/set        rebotarm_msgs/srv/SetGripper, MOTOR units.

UNITS NOTE: this transport's gripper_position (both JointCommand and JointState) is
in VENDOR MOTOR units, NOT meters: state comes from /gripper/state and commands go
to gripper/set unchanged, so M3a's hold-in-place (read the real value, command that
same value back) is exact with no conversion. Higher layers (M3c RealMotionBackend)
map to physical width with the measured grip_lo/grip_hi from cube_lift_real.json.
"""
from __future__ import annotations

from robot_b601.limits import DEFAULT_LIMITS, clamp_to_limits
from robot_b601.transport import JointState

ARM_JOINT_NAMES = ("joint1", "joint2", "joint3", "joint4", "joint5", "joint6")


def _positions_from_cmd(cmd, limits) -> list:
    clamped, _ = clamp_to_limits(cmd.joint_positions, limits)
    return clamped


def _state_from_positions(positions, gripper) -> JointState:
    return JointState(joint_positions=list(positions), gripper_position=float(gripper))


def _arm_positions_from_msg(names, positions, joint_names=ARM_JOINT_NAMES):
    """Order the arm joints by NAME (the /joint_states gate from the M3a review:
    never trust positional ordering -- the vendor message also carries
    gripper_joint1/gripper_joint2). Returns None until every arm joint is present."""
    by_name = dict(zip(list(names), list(positions)))
    try:
        return [float(by_name[n]) for n in joint_names]
    except KeyError:
        return None


def _split_duration(seconds: float):
    sec = int(seconds)
    return sec, int(round((float(seconds) - sec) * 1e9))


def _diff_target(last, positions, gripper):
    """(arm_changed, gripper_changed) vs the last target actually sent. B601Node
    re-streams the identical setpoint every poll tick; equality here collapses that
    stream into one action goal / one service call per real change."""
    if last is None:
        return True, True
    last_pos, last_grip = last
    return list(positions) != list(last_pos), float(gripper) != float(last_grip)


class B601RosTransport:
    def __init__(self, namespace: str = "rebotarm", limits=None,
                 node_name: str = "b601_aspire", move_duration_s: float = 2.0,
                 expect_gripper: bool = True, server_wait_s: float = 5.0):
        self._ns = namespace.strip("/")
        self._limits = limits or DEFAULT_LIMITS
        self._node_name = node_name
        self._move_duration_s = float(move_duration_s)
        self._expect_gripper = bool(expect_gripper)
        self._server_wait_s = float(server_wait_s)
        self._node = None
        self._traj_client = None
        self._grip_client = None
        self._latest_arm = None      # [6] radians, name-ordered
        self._latest_grip = None     # motor units (RS: 0.0 closed .. 5.0 open)
        self._last_sent = None       # (positions, gripper) actually put on the wire

    def connect(self) -> None:
        """Live only: rclpy node + vendor subscriptions/clients + spin thread.
        FAIL-LOUD if the vendor action server / gripper service is absent -- never
        pretend to be connected to a driver that is not running."""
        import threading

        import rclpy
        from rclpy.action import ActionClient
        from rclpy.node import Node
        from rclpy.qos import qos_profile_sensor_data
        from control_msgs.action import FollowJointTrajectory
        from rebotarm_msgs.msg import JointMotorState
        from rebotarm_msgs.srv import SetGripper
        from sensor_msgs.msg import JointState as RosJointState

        rclpy.init(args=None)
        self._node = Node(self._node_name)

        def _on_state(msg):
            arm = _arm_positions_from_msg(msg.name, msg.position)
            if arm is not None:
                self._latest_arm = arm

        def _on_grip(msg):
            self._latest_grip = float(msg.position)

        self._node.create_subscription(
            RosJointState, f"/{self._ns}/joint_states", _on_state,
            qos_profile_sensor_data)
        self._node.create_subscription(
            JointMotorState, f"/{self._ns}/gripper/state", _on_grip,
            qos_profile_sensor_data)
        self._traj_client = ActionClient(
            self._node, FollowJointTrajectory, f"/{self._ns}/follow_joint_trajectory")
        if not self._traj_client.wait_for_server(timeout_sec=self._server_wait_s):
            raise RuntimeError(
                f"B601RosTransport: /{self._ns}/follow_joint_trajectory action server "
                f"not available within {self._server_wait_s}s -- is "
                f"`ros2 launch rebotarm_bringup driver.launch.py model:=rs channel:=can0` "
                f"running?")
        self._grip_client = self._node.create_client(
            SetGripper, f"/{self._ns}/gripper/set")
        if self._expect_gripper and not self._grip_client.wait_for_service(
                timeout_sec=self._server_wait_s):
            raise RuntimeError(
                f"B601RosTransport: /{self._ns}/gripper/set service not available "
                f"within {self._server_wait_s}s (pass expect_gripper=False for an "
                f"arm with no gripper configured)")
        threading.Thread(target=rclpy.spin, args=(self._node,), daemon=True).start()

    def publish(self, cmd) -> None:
        positions = _positions_from_cmd(cmd, self._limits)     # SAFETY: clamp before wire
        if self._node is None:
            raise RuntimeError(
                "B601RosTransport.connect() must be called before publish (live ROS 2 only)")
        arm_changed, grip_changed = _diff_target(
            self._last_sent, positions, cmd.gripper_position)
        if not arm_changed and not grip_changed:
            return                                             # re-stream dedupe
        if arm_changed:
            self._send_trajectory_goal(positions)
        if grip_changed:
            from rebotarm_msgs.srv import SetGripper
            req = SetGripper.Request()
            req.position = float(cmd.gripper_position)         # MOTOR units (see header)
            self._grip_client.call_async(req)                  # fire-and-forget; state
        self._last_sent = (list(positions), float(cmd.gripper_position))  # feedback closes the loop

    def _send_trajectory_goal(self, positions) -> None:
        from builtin_interfaces.msg import Duration
        from control_msgs.action import FollowJointTrajectory
        from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

        sec, nanosec = _split_duration(self._move_duration_s)
        goal = FollowJointTrajectory.Goal()
        goal.trajectory = JointTrajectory(
            joint_names=list(ARM_JOINT_NAMES),
            points=[JointTrajectoryPoint(positions=list(positions),
                                         time_from_start=Duration(sec=sec, nanosec=nanosec))])

        def _on_response(future):
            handle = future.result()
            if handle is None or not handle.accepted:
                # Driver gates goals (e.g. TRAJ_RUNNING): clear last-sent so the
                # node's next re-stream tick retries instead of silently stalling.
                self._last_sent = None

        self._traj_client.send_goal_async(goal).add_done_callback(_on_response)

    def latest(self):
        arm = self._latest_arm
        if arm is None:
            return None
        grip = self._latest_grip
        if grip is None:
            if self._expect_gripper:
                return None      # SAFETY: never report gripper 0.0 (= commanded slam
            grip = 0.0           # shut on hold) before the real value has arrived
        return _state_from_positions(arm, grip)
