"""
RobStride Motor SDK
==================

A Python SDK for controlling RobStride motors via CAN bus.

Basic Usage:
-----------
>>> from robstride import RobStrideMotor, MotorType
>>> motor = RobStrideMotor(can_id=1, interface='can0', motor_type=MotorType.RS09)
>>> motor.enable()
>>> motor.set_position(1.0, 5.0)  # Move to 1 radian at 5 rad/s
>>> print(f"Position: {motor.position}, Velocity: {motor.velocity}")
>>> motor.disable()
"""

from .motor import RobStrideMotor
from .protocol import ControlMode, MotorType
from .utils import float_to_uint, uint16_to_float

__version__ = "1.0.0"
__author__ = "RobStride Team"
__all__ = [
    "RobStrideMotor", 
    "ControlMode",
    "MotorType",
    "float_to_uint",
    "uint16_to_float"
]
