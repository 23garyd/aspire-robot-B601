#!/usr/bin/env python3
"""Fake reBotArmController_ROS2 driver: mimics the vendor interface exactly
(source-verified 2026-07-26) so the REAL live path of B601RosTransport and the
b601_* live scripts can be exercised end-to-end on a PC with NO arm attached.

Mimicked (namespace /rebotarm):
  /rebotarm/joint_states               sensor_msgs/JointState @100Hz, names
                                       [joint1..joint6, gripper_joint1, gripper_joint2]
  /rebotarm/gripper/state              rebotarm_msgs/JointMotorState (MOTOR units)
  /rebotarm/follow_joint_trajectory    control_msgs/action/FollowJointTrajectory
                                       -- REJECTS goals while a move is in progress
                                       (like the real driver's TRAJ_RUNNING gate)
  /rebotarm/gripper/set                rebotarm_msgs/srv/SetGripper (MOTOR units)
  /rebotarm/move_to_pose               rebotarm_msgs/action/MoveToPose (the vendor
                                       IK+execute; here: fake EE tracks the target)
  /rebotarm/safe_home                  std_srvs/srv/Trigger (returns to START_POSE)
  TF base_link -> gripper_end          broadcast from the fake EE pose (for
                                       RealMotionBackend.ee_pose / TfGripperPose)

Run (needs the vendor ws for rebotarm_msgs):
  source /opt/ros/humble/setup.bash
  source ../rebotarm_ros2/install/setup.bash   # or the workspace's actual path
  python3 scripts/b601_fake_vendor_driver.py
This is a validation tool, not part of CI (CI stays ROS 2-free)."""
from __future__ import annotations

import math

import rclpy
import tf2_ros
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from control_msgs.action import FollowJointTrajectory
from geometry_msgs.msg import TransformStamped
from rebotarm_msgs.action import MoveToPose
from rebotarm_msgs.msg import JointMotorState
from rebotarm_msgs.srv import SetGripper
from sensor_msgs.msg import JointState
from std_srvs.srv import Trigger

ARM_JOINTS = ["joint1", "joint2", "joint3", "joint4", "joint5", "joint6"]
START_POSE = [0.3, 0.5, 0.8, 0.2, -0.4, 0.1]   # inside the RS URDF limits
START_GRIP = 2.5                               # motor units (RS: 0 closed .. 5 open)
GRIPPER_MAX_WIDTH = 0.09                       # vendor _GRIPPER_MAX_WIDTH
GRIPPER_OPEN_MOTOR = 5.0
RATE_HZ = 100.0
JOINT_STEP = 0.02                              # rad per tick toward target (~2 rad/s)
SETTLE_TOL = 5e-3


class FakeVendorDriver(Node):
    def __init__(self) -> None:
        super().__init__("fake_rebotarm_driver")
        self._pos = list(START_POSE)
        self._tgt = list(START_POSE)
        self._grip = START_GRIP
        self._grip_tgt = START_GRIP
        self._busy = False

        self._js_pub = self.create_publisher(
            JointState, "/rebotarm/joint_states", qos_profile_sensor_data)
        self._grip_pub = self.create_publisher(
            JointMotorState, "/rebotarm/gripper/state", qos_profile_sensor_data)
        ActionServer(
            self, FollowJointTrajectory, "/rebotarm/follow_joint_trajectory",
            execute_callback=self._execute_traj,
            goal_callback=self._goal_gate,
            cancel_callback=lambda _h: CancelResponse.ACCEPT)
        self.create_service(SetGripper, "/rebotarm/gripper/set", self._set_gripper)
        # M3c surface: vendor IK action + safe_home + TF (fake EE pose model)
        self._ee = [0.20, 0.0, 0.25, 0.0, 0.0, 0.0, 1.0]   # xyz + quat (identity)
        self._ee_tgt = list(self._ee)
        ActionServer(
            self, MoveToPose, "/rebotarm/move_to_pose",
            execute_callback=self._execute_pose,
            goal_callback=self._goal_gate,
            cancel_callback=lambda _h: CancelResponse.ACCEPT)
        self.create_service(Trigger, "/rebotarm/safe_home", self._safe_home)
        self._tf_bcast = tf2_ros.TransformBroadcaster(self)
        self.create_timer(1.0 / RATE_HZ, self._tick)
        self.get_logger().info("fake vendor driver up (no hardware)")

    def _execute_pose(self, goal_handle):
        p = goal_handle.request.target_pose
        self._ee_tgt = [p.position.x, p.position.y, p.position.z,
                        p.orientation.x, p.orientation.y, p.orientation.z,
                        p.orientation.w]
        self._busy = True
        goal_handle.succeed()          # fake EE keeps converging via the tick timer
        result = MoveToPose.Result()
        result.success = True
        result.message = "fake IK target accepted"
        result.final_pose = p
        return result

    def _safe_home(self, _request, response):
        self._tgt = list(START_POSE)
        self._ee_tgt = [0.20, 0.0, 0.25, 0.0, 0.0, 0.0, 1.0]
        response.success = True
        response.message = "fake safe home"
        return response

    def _goal_gate(self, _goal_request):
        if self._busy:      # the real driver rejects arm goals in TRAJ_RUNNING
            self.get_logger().info("rejecting goal: busy (TRAJ_RUNNING mimic)")
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    def _execute_traj(self, goal_handle):
        traj = goal_handle.request.trajectory
        point = traj.points[-1]
        by_name = dict(zip(traj.joint_names, point.positions))
        self._tgt = [float(by_name.get(n, t)) for n, t in zip(ARM_JOINTS, self._tgt)]
        self._busy = True
        goal_handle.succeed()          # motion continues via the tick timer
        result = FollowJointTrajectory.Result()
        result.error_code = FollowJointTrajectory.Result.SUCCESSFUL
        return result

    def _set_gripper(self, request, response):
        self._grip_tgt = float(request.position)
        response.success = True
        response.reached_position = float(self._grip)
        return response

    def _tick(self) -> None:
        for i in range(6):
            d = self._tgt[i] - self._pos[i]
            self._pos[i] += math.copysign(min(abs(d), JOINT_STEP), d) if d else 0.0
        for i in range(7):                       # fake EE glides to the pose target
            d = self._ee_tgt[i] - self._ee[i]
            self._ee[i] += math.copysign(min(abs(d), 0.005), d) if d else 0.0
        settled = (max(abs(t - p) for t, p in zip(self._tgt, self._pos)) < SETTLE_TOL
                   and max(abs(t - p) for t, p in zip(self._ee_tgt, self._ee)) < SETTLE_TOL)
        if self._busy and settled:
            self._busy = False

        tf = TransformStamped()
        tf.header.stamp = self.get_clock().now().to_msg()
        tf.header.frame_id = "base_link"
        tf.child_frame_id = "gripper_end"
        tf.transform.translation.x = self._ee[0]
        tf.transform.translation.y = self._ee[1]
        tf.transform.translation.z = self._ee[2]
        n = math.sqrt(sum(v * v for v in self._ee[3:7])) or 1.0
        (tf.transform.rotation.x, tf.transform.rotation.y,
         tf.transform.rotation.z, tf.transform.rotation.w) = [v / n for v in self._ee[3:7]]
        self._tf_bcast.sendTransform(tf)
        gd = self._grip_tgt - self._grip
        self._grip += math.copysign(min(abs(gd), 0.05), gd) if gd else 0.0

        now = self.get_clock().now().to_msg()
        js = JointState()
        js.header.stamp = now
        half_width = max(0.0, min(GRIPPER_MAX_WIDTH / 2,
                                  self._grip / GRIPPER_OPEN_MOTOR * GRIPPER_MAX_WIDTH / 2))
        js.name = ARM_JOINTS + ["gripper_joint1", "gripper_joint2"]
        js.position = [float(p) for p in self._pos] + [half_width, half_width]
        js.velocity = [0.0] * 8
        js.effort = [0.0] * 8
        self._js_pub.publish(js)

        gm = JointMotorState()
        gm.header.stamp = now
        gm.joint_name = "gripper"
        gm.position = float(self._grip)
        self._grip_pub.publish(gm)


def main() -> None:
    rclpy.init()
    node = FakeVendorDriver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
