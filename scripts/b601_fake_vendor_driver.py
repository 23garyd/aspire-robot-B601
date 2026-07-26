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

Run (needs the vendor ws for rebotarm_msgs):
  source /opt/ros/humble/setup.bash
  source ../rebotarm_ros2/install/setup.bash   # or the workspace's actual path
  python3 scripts/b601_fake_vendor_driver.py
This is a validation tool, not part of CI (CI stays ROS 2-free)."""
from __future__ import annotations

import math

import rclpy
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from control_msgs.action import FollowJointTrajectory
from rebotarm_msgs.msg import JointMotorState
from rebotarm_msgs.srv import SetGripper
from sensor_msgs.msg import JointState

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
        self.create_timer(1.0 / RATE_HZ, self._tick)
        self.get_logger().info("fake vendor driver up (no hardware)")

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
        if self._busy and max(abs(t - p) for t, p in zip(self._tgt, self._pos)) < SETTLE_TOL:
            self._busy = False
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
