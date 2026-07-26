import pytest
from robot_b601.transport import JointCommand, JointState
from robot_b601.limits import JointLimits

def test_module_imports_without_ros2():
    import robot_b601.ros_transport as rt      # rclpy is deferred; must import with no ROS 2
    assert hasattr(rt, "B601RosTransport")

def test_positions_from_cmd_clamps():
    from robot_b601.ros_transport import _positions_from_cmd
    lim = JointLimits(lo=[-1.0]*6, hi=[1.0]*6)
    out = _positions_from_cmd(JointCommand([2.0]*6, 0.0), lim)
    assert out == [1.0]*6                        # SAFETY: clamped before the wire

def test_state_from_positions_shape():
    from robot_b601.ros_transport import _state_from_positions
    st = _state_from_positions([0.1]*6, 0.03)
    assert isinstance(st, JointState)
    assert st.joint_positions == [0.1]*6 and st.gripper_position == 0.03

def test_publish_before_connect_raises():
    from robot_b601.ros_transport import B601RosTransport
    t = B601RosTransport()
    with pytest.raises(RuntimeError):
        t.publish(JointCommand([0.0]*6, 0.0))    # not connected -> refuse (no silent no-op)


# --- vendor-interface helpers (source-verified against reBotArmController_ROS2) ---

def test_arm_positions_keyed_by_name_not_position():
    from robot_b601.ros_transport import _arm_positions_from_msg
    # vendor msg carries gripper joints too, and order must not be trusted
    names = ["gripper_joint1", "joint3", "joint1", "joint2", "gripper_joint2",
             "joint6", "joint4", "joint5"]
    pos = [0.01, 3.0, 1.0, 2.0, 0.01, 6.0, 4.0, 5.0]
    assert _arm_positions_from_msg(names, pos) == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]

def test_arm_positions_missing_joint_returns_none():
    from robot_b601.ros_transport import _arm_positions_from_msg
    names = ["joint1", "joint2", "joint3", "joint4", "joint5"]   # joint6 absent
    assert _arm_positions_from_msg(names, [0.0]*5) is None

def test_split_duration():
    from robot_b601.ros_transport import _split_duration
    assert _split_duration(2.0) == (2, 0)
    assert _split_duration(2.5) == (2, 500000000)

def test_diff_target_dedupes_restream():
    from robot_b601.ros_transport import _diff_target
    last = ([0.1]*6, 0.5)
    assert _diff_target(None, [0.1]*6, 0.5) == (True, True)      # first send: both
    assert _diff_target(last, [0.1]*6, 0.5) == (False, False)    # identical re-stream
    assert _diff_target(last, [0.2]*6, 0.5) == (True, False)     # arm-only change
    assert _diff_target(last, [0.1]*6, 0.6) == (False, True)     # gripper-only change

def test_latest_gates_on_real_gripper_state():
    # SAFETY: with a gripper expected, latest() must stay None until the REAL
    # gripper value has arrived -- else M3a's hold would capture a fake 0.0 and
    # slam the physical gripper shut.
    from robot_b601.ros_transport import B601RosTransport
    t = B601RosTransport()
    assert t.latest() is None
    t._latest_arm = [0.1]*6
    assert t.latest() is None                     # arm alone is NOT enough
    t._latest_grip = 2.5
    st = t.latest()
    assert st.joint_positions == [0.1]*6 and st.gripper_position == 2.5

def test_latest_arm_only_mode():
    from robot_b601.ros_transport import B601RosTransport
    t = B601RosTransport(expect_gripper=False)
    t._latest_arm = [0.1]*6
    st = t.latest()
    assert st is not None and st.gripper_position == 0.0
