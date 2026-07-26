import importlib
import pytest
from robot_b601.motion import EePose, FakeMotionBackend
from robot_b601.limits import GripperLimits


def test_move_to_pose_sets_ee():
    m = FakeMotionBackend()
    m.move_to_pose(0.4, 0.1, 0.2)
    ee = m.ee_pose()
    assert (round(ee.x, 3), round(ee.y, 3), round(ee.z, 3)) == (0.4, 0.1, 0.2)


def test_set_gripper_clamps_to_limits():
    m = FakeMotionBackend(gripper_limits=GripperLimits(0.0, 0.08))
    m.set_gripper(0.5)                     # over-open
    assert m.gripper_position() == 0.08
    m.set_gripper(-0.2)                    # over-closed
    assert m.gripper_position() == 0.0


def test_gripper_stalls_on_object_when_ee_near_it():
    # object 3cm wide at (0.4,0,0.02); closing at the object stalls the gripper at 0.03
    m = FakeMotionBackend(object_xyz=(0.4, 0.0, 0.02), object_width=0.03, grasp_tol=0.03)
    m.move_to_pose(0.4, 0.0, 0.02)         # EE at the object
    m.set_gripper(0.0)                     # command fully closed
    assert m.gripper_position() == 0.03    # stalled on the object


def test_gripper_fully_closes_when_ee_far_from_object():
    m = FakeMotionBackend(object_xyz=(0.4, 0.0, 0.02), object_width=0.03, grasp_tol=0.03)
    m.move_to_pose(0.0, 0.0, 0.30)         # EE far away
    m.set_gripper(0.0)
    assert m.gripper_position() == 0.0     # nothing to stall on


def test_reset_restores_start_state():
    m = FakeMotionBackend(start_ee=(0.0, 0.0, 0.30), start_grip=0.08)
    m.move_to_pose(0.4, 0.1, 0.2)
    m.set_gripper(0.0)
    m.reset()
    assert m.ee_pose().z == 0.30 and m.gripper_position() == 0.08


def test_motion_module_imports_without_rclpy():
    mod = importlib.import_module("robot_b601.motion")     # rclpy deferred in RealMotionBackend
    assert hasattr(mod, "RealMotionBackend") and hasattr(mod, "FakeMotionBackend")


def test_real_backend_before_connect_raises():
    from robot_b601.motion import RealMotionBackend
    with pytest.raises(RuntimeError):
        RealMotionBackend().move_to_pose(0.4, 0.0, 0.02)


# --- RealMotionBackend pure helpers (vendor units/orientation, no ROS 2) ---

def test_width_motor_round_trip_and_clamp():
    from robot_b601.motion import _motor_to_width, _width_to_motor
    # RS map: close=0.0, open=5.0 motor units over 0.09 m width
    assert _width_to_motor(0.0, 0.0, 5.0, 0.09) == 0.0
    assert _width_to_motor(0.09, 0.0, 5.0, 0.09) == 5.0
    assert abs(_width_to_motor(0.045, 0.0, 5.0, 0.09) - 2.5) < 1e-12
    assert abs(_motor_to_width(2.5, 0.0, 5.0, 0.09) - 0.045) < 1e-12
    assert _width_to_motor(1.0, 0.0, 5.0, 0.09) == 5.0      # over-wide clamps
    assert _motor_to_width(9.0, 0.0, 5.0, 0.09) == 0.09     # over-travel clamps
    assert _motor_to_width(2.5, 0.0, 0.0, 0.09) == 0.0      # zero span -> no div/0

def test_width_motor_inverted_map():
    from robot_b601.motion import _motor_to_width, _width_to_motor
    # DM-style inverted map (open=-5.0 < close=0.0) must still round-trip
    m = _width_to_motor(0.045, 0.0, -5.0, 0.09)
    assert abs(m - (-2.5)) < 1e-12
    assert abs(_motor_to_width(m, 0.0, -5.0, 0.09) - 0.045) < 1e-12

def test_rpy_quat_round_trip():
    from robot_b601.motion import _quat_to_rpy, _rpy_to_quat
    rpy = (0.1, -0.4, 1.2)
    assert all(abs(a - b) < 1e-9 for a, b in zip(_quat_to_rpy(*_rpy_to_quat(*rpy)), rpy))

def test_rpy_convention_matches_vendor_sxyz():
    # the vendor decodes with tf_transformations.euler_from_quaternion (sxyz);
    # scipy extrinsic 'xyz' must produce the identical quaternion for a pure yaw
    import math
    from robot_b601.motion import _rpy_to_quat
    qx, qy, qz, qw = _rpy_to_quat(0.0, 0.0, math.pi / 2)
    assert abs(qz - math.sin(math.pi / 4)) < 1e-9 and abs(qw - math.cos(math.pi / 4)) < 1e-9
