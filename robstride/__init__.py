"""
Robstride Motor SDK
~~~~~~~~~~~~~~~~~~

A Python SDK for controlling Robstride motors via CAN bus communication.

Basic usage:

   >>> import robstride
   >>> motor = robstride.create_motor_from_can_interface(motor_id=1, interface='socketcan', channel='can0')
   >>> motor.enable()
   >>> motor.set_motion_control(pos=1.0, vel=0.0, kp=50.0, kd=1.0, torque=0.0)
   >>> status = motor.get_status()
   >>> print(f"Position: {status['position']:.3f} rad")
   >>> motor.disable()
   >>> motor.close()

For more control over the CAN bus:

   >>> import can
   >>> import robstride
   >>> 
   >>> bus = can.interface.Bus(channel='PCAN_USBBUS1', bustype='pcan', bitrate=1000000)
   >>> motor = robstride.Motor(motor_id=1, can_bus=bus)
   >>> # ... use motor ...
   >>> motor.close()
   >>> bus.shutdown()

:copyright: (c) 2025 by RobStride.
:license: MIT, see LICENSE for more details.
"""

from .motor import Motor, create_motor_from_can_interface
from .protocol import (
    MotorStatus,
    # Run modes
    RUN_MODE_MOTION_CONTROL,
    RUN_MODE_POSITION_PP,
    RUN_MODE_VELOCITY,
    RUN_MODE_CURRENT,
    RUN_MODE_POSITION_CSP,
    # Parameter indices (commonly used ones)
    PARAM_RUN_MODE,
    PARAM_IQ_REF,
    PARAM_SPD_REF,
    PARAM_LOC_REF,
    PARAM_LIMIT_SPD,
    PARAM_LIMIT_CUR,
    PARAM_LOC_KP,
    PARAM_SPD_KP,
    PARAM_SPD_KI,
)
from .exceptions import (
    RobstrideException,
    ConnectionError,
    TimeoutException,
    MotorFaultException,
    ParameterError,
    ProtocolError,
)

__version__ = '0.1.0'
__author__ = 'RobStride Team'
__email__ = 'support@robstride.com'

# For backwards compatibility and convenience
__all__ = [
    'Motor',
    'create_motor_from_can_interface',
    'MotorStatus',
    'RUN_MODE_MOTION_CONTROL',
    'RUN_MODE_POSITION_PP', 
    'RUN_MODE_VELOCITY',
    'RUN_MODE_CURRENT',
    'RUN_MODE_POSITION_CSP',
    'PARAM_RUN_MODE',
    'PARAM_IQ_REF',
    'PARAM_SPD_REF',
    'PARAM_LOC_REF',
    'PARAM_LIMIT_SPD',
    'PARAM_LIMIT_CUR',
    'PARAM_LOC_KP',
    'PARAM_SPD_KP',
    'PARAM_SPD_KI',
    'RobstrideException',
    'ConnectionError',
    'TimeoutException',
    'MotorFaultException',
    'ParameterError',
    'ProtocolError',
]