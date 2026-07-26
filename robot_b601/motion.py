"""MotionBackend seam for the B601 real cube-lift (M3c). The task calls Cartesian/gripper
primitives through a backend: FakeMotionBackend is a deterministic model (CI, no
hardware); RealMotionBackend drives the vendor MoveIt2/IK over ROS 2 (on-bench, rclpy
deferred). Swapping the backend swaps sim<->real; the task logic above is unchanged."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from robot_b601.limits import DEFAULT_GRIPPER_LIMITS, GripperLimits, clamp_gripper
from robot_b601.node import MoveResult


@dataclass
class EePose:
    x: float
    y: float
    z: float
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0


class MotionBackend(Protocol):
    def move_to_pose(self, x, y, z, roll=0.0, pitch=0.0, yaw=0.0) -> MoveResult: ...
    def move_to_joints(self, joints) -> MoveResult: ...
    def set_gripper(self, pos) -> MoveResult: ...
    def gripper_position(self) -> float: ...
    def ee_pose(self) -> EePose: ...
    def reset(self) -> None: ...


class FakeMotionBackend:
    """Deterministic motion model for CI. move_to_pose sets the EE directly (IK assumed to
    solve). set_gripper clamps to gripper limits; if a graspable object is configured and
    the EE is within grasp_tol of it, a commanded close stalls the gripper at object_width
    (modelling the fingers meeting the object) so grasp detection has a realistic reading."""

    def __init__(self, gripper_limits: GripperLimits = DEFAULT_GRIPPER_LIMITS,
                 start_ee=(0.0, 0.0, 0.30), start_grip=0.08,
                 object_xyz=None, object_width=0.0, grasp_tol=0.03):
        self._glim = gripper_limits
        self._start_ee = tuple(start_ee)
        self._start_grip = float(start_grip)
        self._object_xyz = tuple(object_xyz) if object_xyz is not None else None
        self._object_width = float(object_width)
        self._grasp_tol = float(grasp_tol)
        self.reset()

    def reset(self) -> None:
        self._ee = EePose(*self._start_ee)
        self._grip = self._start_grip

    def move_to_pose(self, x, y, z, roll=0.0, pitch=0.0, yaw=0.0) -> MoveResult:
        self._ee = EePose(float(x), float(y), float(z),
                          float(roll), float(pitch), float(yaw))
        return MoveResult(reached=True, residual=0.0, status="ok", iterations=1)

    def move_to_joints(self, joints) -> MoveResult:
        return MoveResult(reached=True, residual=0.0, status="ok", iterations=1)

    def set_gripper(self, pos) -> MoveResult:
        target, _ = clamp_gripper(pos, self._glim)
        if self._object_xyz is not None:
            ox, oy, oz = self._object_xyz
            d = ((self._ee.x - ox) ** 2 + (self._ee.y - oy) ** 2
                 + (self._ee.z - oz) ** 2) ** 0.5
            if d <= self._grasp_tol and target < self._object_width:
                target = self._object_width          # fingers meet the object -> stall
        self._grip = target
        return MoveResult(reached=True, residual=0.0, status="ok", iterations=1)

    def gripper_position(self) -> float:
        return self._grip

    def ee_pose(self) -> EePose:
        return self._ee


def _width_to_motor(width: float, close_motor: float, open_motor: float,
                    max_width: float) -> float:
    """Physical full gripper width (m) -> vendor motor units. Linear over the
    measured close/open motor positions; input clamped to [0, max_width]."""
    w = max(0.0, min(float(width), float(max_width)))
    return close_motor + (w / max_width) * (open_motor - close_motor)


def _motor_to_width(motor: float, close_motor: float, open_motor: float,
                    max_width: float) -> float:
    """Inverse of _width_to_motor; output clamped to [0, max_width]."""
    span = open_motor - close_motor
    ratio = 0.0 if span == 0.0 else (float(motor) - close_motor) / span
    return max(0.0, min(ratio * max_width, float(max_width)))


def _rpy_to_quat(roll: float, pitch: float, yaw: float):
    """xyzw quaternion, extrinsic xyz -- same convention as the vendor driver's
    tf_transformations.euler_from_quaternion (sxyz)."""
    from scipy.spatial.transform import Rotation
    return [float(v) for v in Rotation.from_euler("xyz", [roll, pitch, yaw]).as_quat()]


def _quat_to_rpy(x: float, y: float, z: float, w: float):
    from scipy.spatial.transform import Rotation
    return [float(v) for v in Rotation.from_quat([x, y, z, w]).as_euler("xyz")]


class RealMotionBackend:
    """Live backend against the vendor reBotArmController_ROS2 driver (source-verified
    2026-07-26; validated against scripts/b601_fake_vendor_driver.py):
      move_to_pose   -> /{ns}/move_to_pose        rebotarm_msgs/action/MoveToPose
                        (the vendor's own IK+execute -- no MoveIt2 needed)
      move_to_joints -> /{ns}/follow_joint_trajectory (control_msgs FJT action)
      set_gripper    -> /{ns}/gripper/set          rebotarm_msgs/srv/SetGripper
      gripper state  <- /{ns}/gripper/state        (MOTOR units -> width via the
                        measured close/open motor map; VALIDATE the map on-bench)
      ee_pose        <- TF base_frame -> gripper_frame (robot_state_publisher)
      reset          -> /{ns}/safe_home Trigger + open the gripper
    The backend API stays in METERS for the gripper (grip_lo/grip_hi from the run
    config); clamp-before-wire is preserved: the CLAMPED width is converted and sent,
    never the raw request. rclpy deferred in connect(); guards rclpy.ok() so it
    composes with TfGripperPose/D405 in the same process."""

    def __init__(self, gripper_limits: GripperLimits = DEFAULT_GRIPPER_LIMITS,
                 base_frame="base_link", gripper_frame="gripper_end",
                 namespace: str = "rebotarm", move_duration_s: float = 3.0,
                 action_timeout_s: float = 30.0, server_wait_s: float = 5.0,
                 gripper_open_motor: float = 5.0, gripper_close_motor: float = 0.0,
                 gripper_max_width: float = 0.09, node_name: str = "b601_motion"):
        self._glim = gripper_limits
        self._base_frame = base_frame
        self._gripper_frame = gripper_frame
        self._ns = namespace.strip("/")
        self._move_duration_s = float(move_duration_s)
        self._action_timeout_s = float(action_timeout_s)
        self._server_wait_s = float(server_wait_s)
        self._g_open = float(gripper_open_motor)
        self._g_close = float(gripper_close_motor)
        self._g_maxw = float(gripper_max_width)
        self._node_name = node_name
        self._connected = False
        self._node = None
        self._spin_thread = None
        self._latest_grip_motor = None

    def connect(self) -> None:
        import threading

        import rclpy
        import tf2_ros
        from rclpy.action import ActionClient
        from rclpy.node import Node
        from rclpy.qos import qos_profile_sensor_data
        from control_msgs.action import FollowJointTrajectory
        from rebotarm_msgs.action import MoveToPose
        from rebotarm_msgs.msg import JointMotorState
        from rebotarm_msgs.srv import SetGripper
        from std_srvs.srv import Trigger

        if not rclpy.ok():
            rclpy.init(args=None)
        self._node = Node(self._node_name)
        self._node.create_subscription(
            JointMotorState, f"/{self._ns}/gripper/state",
            lambda m: setattr(self, "_latest_grip_motor", float(m.position)),
            qos_profile_sensor_data)
        self._pose_client = ActionClient(
            self._node, MoveToPose, f"/{self._ns}/move_to_pose")
        self._traj_client = ActionClient(
            self._node, FollowJointTrajectory, f"/{self._ns}/follow_joint_trajectory")
        self._grip_client = self._node.create_client(
            SetGripper, f"/{self._ns}/gripper/set")
        self._home_client = self._node.create_client(
            Trigger, f"/{self._ns}/safe_home")
        for client, what in ((self._pose_client, "move_to_pose action"),
                             (self._traj_client, "follow_joint_trajectory action")):
            if not client.wait_for_server(timeout_sec=self._server_wait_s):
                raise RuntimeError(
                    f"RealMotionBackend: vendor {what} not available within "
                    f"{self._server_wait_s}s -- is the rebotarm driver running?")
        for client, what in ((self._grip_client, "gripper/set"),
                             (self._home_client, "safe_home")):
            if not client.wait_for_service(timeout_sec=self._server_wait_s):
                raise RuntimeError(
                    f"RealMotionBackend: vendor {what} service not available within "
                    f"{self._server_wait_s}s")
        self._tf_buffer = tf2_ros.Buffer()
        self._tf_listener = tf2_ros.TransformListener(self._tf_buffer, self._node)
        self._spin_thread = threading.Thread(
            target=rclpy.spin, args=(self._node,), daemon=True)
        self._spin_thread.start()
        self._connected = True

    def close(self) -> None:
        """Stop rclpy cleanly (process-global: call once, at teardown, after every
        other node in this process is done)."""
        if self._node is None:
            return
        import rclpy
        try:
            rclpy.shutdown()
        except Exception:
            pass
        if self._spin_thread is not None:
            self._spin_thread.join(timeout=2.0)
            self._spin_thread = None
        self._node = None
        self._connected = False

    def _require_connected(self):
        if not self._connected:
            raise RuntimeError("RealMotionBackend.connect() must be called before use")

    def _call_action_blocking(self, client, goal) -> "tuple[str, object]":
        """send_goal_async + bounded wait. -> (status, result): status is 'ok',
        'REJECTED', or 'TIMEOUT'. Callbacks run on the spin thread."""
        import threading
        done = threading.Event()
        box = {"status": "TIMEOUT", "result": None}

        def _on_goal(fut):
            handle = fut.result()
            if handle is None or not handle.accepted:
                box["status"] = "REJECTED"
                done.set()
                return

            def _on_result(rf):
                box["status"] = "ok"
                box["result"] = rf.result().result
                done.set()

            handle.get_result_async().add_done_callback(_on_result)

        client.send_goal_async(goal).add_done_callback(_on_goal)
        done.wait(self._action_timeout_s)
        return box["status"], box["result"]

    def _call_service_blocking(self, client, request):
        future = client.call_async(request)
        import threading
        done = threading.Event()
        future.add_done_callback(lambda _f: done.set())
        if not done.wait(self._action_timeout_s):
            return None
        return future.result()

    def move_to_pose(self, x, y, z, roll=0.0, pitch=0.0, yaw=0.0) -> MoveResult:
        self._require_connected()
        from geometry_msgs.msg import Pose
        from rebotarm_msgs.action import MoveToPose

        goal = MoveToPose.Goal()
        pose = Pose()
        pose.position.x, pose.position.y, pose.position.z = float(x), float(y), float(z)
        qx, qy, qz, qw = _rpy_to_quat(roll, pitch, yaw)
        pose.orientation.x, pose.orientation.y = qx, qy
        pose.orientation.z, pose.orientation.w = qz, qw
        goal.target_pose = pose
        goal.duration = self._move_duration_s
        status, result = self._call_action_blocking(self._pose_client, goal)
        ok = status == "ok" and result is not None and bool(result.success)
        return MoveResult(reached=ok, residual=0.0 if ok else float("inf"),
                          status="ok" if ok else (status if status != "ok" else "FAILED"),
                          iterations=1)

    def move_to_joints(self, joints) -> MoveResult:
        self._require_connected()
        from builtin_interfaces.msg import Duration
        from control_msgs.action import FollowJointTrajectory
        from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

        sec = int(self._move_duration_s)
        nanosec = int(round((self._move_duration_s - sec) * 1e9))
        goal = FollowJointTrajectory.Goal()
        goal.trajectory = JointTrajectory(
            joint_names=[f"joint{i + 1}" for i in range(len(list(joints)))],
            points=[JointTrajectoryPoint(positions=[float(j) for j in joints],
                                         time_from_start=Duration(sec=sec, nanosec=nanosec))])
        status, _result = self._call_action_blocking(self._traj_client, goal)
        ok = status == "ok"
        return MoveResult(reached=ok, residual=0.0 if ok else float("inf"),
                          status="ok" if ok else status, iterations=1)

    def set_gripper(self, pos) -> MoveResult:
        self._require_connected()
        target, _ = clamp_gripper(pos, self._glim)   # SAFETY: clamp BEFORE the wire --
        from rebotarm_msgs.srv import SetGripper     # the crush hazard closes here
        req = SetGripper.Request()
        req.position = _width_to_motor(target, self._g_close, self._g_open, self._g_maxw)
        resp = self._call_service_blocking(self._grip_client, req)
        ok = resp is not None and bool(resp.success)
        return MoveResult(reached=ok, residual=0.0 if ok else float("inf"),
                          status="ok" if ok else "FAILED", iterations=1)

    def gripper_position(self) -> float:
        self._require_connected()
        m = self._latest_grip_motor
        if m is None:
            raise RuntimeError(
                "RealMotionBackend: no /gripper/state received yet -- refusing to "
                "fabricate a gripper reading (grasp detection depends on it)")
        return _motor_to_width(m, self._g_close, self._g_open, self._g_maxw)

    def ee_pose(self) -> EePose:
        self._require_connected()
        from rclpy.duration import Duration
        from rclpy.time import Time
        tr = self._tf_buffer.lookup_transform(
            self._base_frame, self._gripper_frame, Time(),
            timeout=Duration(seconds=2.0))
        t, q = tr.transform.translation, tr.transform.rotation
        roll, pitch, yaw = _quat_to_rpy(q.x, q.y, q.z, q.w)
        return EePose(float(t.x), float(t.y), float(t.z), roll, pitch, yaw)

    def reset(self) -> None:
        self._require_connected()
        from std_srvs.srv import Trigger
        resp = self._call_service_blocking(self._home_client, Trigger.Request())
        if resp is None or not bool(resp.success):
            raise RuntimeError(f"RealMotionBackend.reset: safe_home failed "
                               f"({getattr(resp, 'message', 'no response')})")
        res = self.set_gripper(self._glim.hi)        # open to the configured max
        if not res.reached:
            raise RuntimeError("RealMotionBackend.reset: gripper open failed")
