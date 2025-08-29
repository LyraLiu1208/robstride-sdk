"""
Robstride Motor CAN Protocol Implementation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module implements the low-level CAN protocol for Robstride motors.
It handles the packing and unpacking of CAN frames according to the official protocol specification.

Protocol Overview:
- CAN 2.0 Extended Frame (29-bit ID)
- Bitrate: 1Mbps
- ID Structure: [28-24: comm_type] [23-8: host_id] [7-0: motor_id]
"""

import struct
from typing import TypedDict, Tuple

# Protocol physical quantity ranges
P_MIN, P_MAX = -12.57, 12.57  # rad
V_MIN, V_MAX = -50.0, 50.0    # rad/s
KP_MIN, KP_MAX = 0.0, 500.0
KD_MIN, KD_MAX = 0.0, 5.0
T_MIN, T_MAX = -5.5, 5.5      # Nm

# Parameter indices for read/write operations
PARAM_RUN_MODE = 0x7005
PARAM_IQ_REF = 0x7006
PARAM_SPD_REF = 0x700A
PARAM_LIMIT_TORQUE = 0x700B
PARAM_CUR_KP = 0x7010
PARAM_CUR_KI = 0x7011
PARAM_CUR_FILT_GAIN = 0x7014
PARAM_LOC_REF = 0x7016
PARAM_LIMIT_SPD = 0x7017
PARAM_LIMIT_CUR = 0x7018
PARAM_MECH_POS = 0x7019
PARAM_IQF = 0x701A
PARAM_MECH_VEL = 0x701B
PARAM_VBUS = 0x701C
PARAM_LOC_KP = 0x701E
PARAM_SPD_KP = 0x701F
PARAM_SPD_KI = 0x7020
PARAM_SPD_FILT_GAIN = 0x7021
PARAM_ACC_RAD = 0x7022
PARAM_VEL_MAX = 0x7024
PARAM_ACC_SET = 0x7025
PARAM_EPSCAN_TIME = 0x7026
PARAM_CAN_TIMEOUT = 0x7028
PARAM_ZERO_STA = 0x7029

# Run modes
RUN_MODE_MOTION_CONTROL = 0
RUN_MODE_POSITION_PP = 1
RUN_MODE_VELOCITY = 2
RUN_MODE_CURRENT = 3
RUN_MODE_POSITION_CSP = 5


class MotorStatus(TypedDict):
    """Motor status information parsed from feedback frames."""
    motor_id: int
    position: float      # rad
    velocity: float      # rad/s
    torque: float        # Nm
    temperature: float   # °C
    error_code: int
    mode: int           # 0: Reset, 1: Cali, 2: Motor


def build_can_id(comm_type: int, motor_id: int, host_id: int = 0xFD) -> int:
    """
    Build 29-bit extended CAN ID according to protocol specification.
    
    Args:
        comm_type: Communication type (5 bits, 0-31)
        motor_id: Target motor CAN ID (8 bits, 0-255)
        host_id: Host CAN ID (16 bits, 0-65535)
    
    Returns:
        29-bit CAN ID
    """
    return (comm_type << 24) | (host_id << 8) | motor_id


def float_to_uint(x: float, x_min: float, x_max: float, bits: int) -> int:
    """
    Convert float to unsigned integer with linear mapping.
    
    Args:
        x: Input float value
        x_min: Minimum value of the range
        x_max: Maximum value of the range
        bits: Number of bits for the output integer
    
    Returns:
        Mapped unsigned integer
    """
    span = x_max - x_min
    offset = x_min
    # Clamp input to valid range
    x = max(min(x, x_max), x_min)
    return int((x - offset) * ((1 << bits) - 1) / span)


def uint_to_float(x_int: int, x_min: float, x_max: float, bits: int) -> float:
    """
    Convert unsigned integer back to float with linear mapping.
    
    Args:
        x_int: Input unsigned integer
        x_min: Minimum value of the range
        x_max: Maximum value of the range
        bits: Number of bits for the input integer
    
    Returns:
        Mapped float value
    """
    span = x_max - x_min
    offset = x_min
    return float(x_int * span / ((1 << bits) - 1) + offset)


# Communication Type 0: Get Device ID
def pack_get_device_id_command(motor_id: int, host_id: int = 0xFD) -> Tuple[int, bytes]:
    """Pack communication type 0: Get device ID."""
    can_id = build_can_id(0x00, motor_id, host_id)
    return can_id, b'\x00' * 8


# Communication Type 1: Motion Control Command
def pack_motion_control_command(motor_id: int, pos: float, vel: float, kp: float, 
                               kd: float, torque: float, host_id: int = 0xFD) -> Tuple[int, bytes]:
    """
    Pack communication type 1: Motion control command.
    
    Args:
        motor_id: Target motor ID
        pos: Target position (-12.57 to 12.57 rad)
        vel: Target velocity (-50 to 50 rad/s)
        kp: Position gain (0 to 500)
        kd: Damping gain (0 to 5)
        torque: Feedforward torque (-5.5 to 5.5 Nm)
        host_id: Host CAN ID
    
    Returns:
        Tuple of (CAN ID, data bytes)
    """
    # Convert floats to 16-bit unsigned integers
    pos_int = float_to_uint(pos, P_MIN, P_MAX, 16)
    vel_int = float_to_uint(vel, V_MIN, V_MAX, 16)
    kp_int = float_to_uint(kp, KP_MIN, KP_MAX, 16)
    kd_int = float_to_uint(kd, KD_MIN, KD_MAX, 16)
    torque_int = float_to_uint(torque, T_MIN, T_MAX, 16)
    
    # Build CAN ID with torque in data field (according to C code example)
    can_id = build_can_id(0x01, motor_id, torque_int)
    
    # Pack data: high byte first (big-endian)
    data = struct.pack('>HHHH', pos_int, vel_int, kp_int, kd_int)
    
    return can_id, data


# Communication Type 3: Enable Motor
def pack_enable_motor_command(motor_id: int, host_id: int = 0xFD) -> Tuple[int, bytes]:
    """Pack communication type 3: Enable motor."""
    can_id = build_can_id(0x03, motor_id, host_id)
    return can_id, b'\x00' * 8


# Communication Type 4: Disable Motor
def pack_disable_motor_command(motor_id: int, host_id: int = 0xFD, 
                              clear_errors: bool = False) -> Tuple[int, bytes]:
    """
    Pack communication type 4: Disable motor.
    
    Args:
        motor_id: Target motor ID
        host_id: Host CAN ID
        clear_errors: If True, clear motor errors
    
    Returns:
        Tuple of (CAN ID, data bytes)
    """
    can_id = build_can_id(0x04, motor_id, host_id)
    data = b'\x01' + b'\x00' * 7 if clear_errors else b'\x00' * 8
    return can_id, data


# Communication Type 6: Set Motor Zero Position
def pack_set_zero_position_command(motor_id: int, host_id: int = 0xFD) -> Tuple[int, bytes]:
    """Pack communication type 6: Set motor mechanical zero position."""
    can_id = build_can_id(0x06, motor_id, host_id)
    data = b'\x01' + b'\x00' * 7
    return can_id, data


# Communication Type 7: Set Motor CAN ID
def pack_set_motor_id_command(motor_id: int, new_id: int, host_id: int = 0xFD) -> Tuple[int, bytes]:
    """Pack communication type 7: Set motor CAN ID."""
    can_id = build_can_id(0x07, motor_id, (new_id << 8) | host_id)
    return can_id, b'\x00' * 8


# Communication Type 17: Read Single Parameter
def pack_read_param_command(motor_id: int, param_index: int, host_id: int = 0xFD) -> Tuple[int, bytes]:
    """
    Pack communication type 17: Read single parameter.
    
    Args:
        motor_id: Target motor ID
        param_index: Parameter index (e.g., 0x7005 for run_mode)
        host_id: Host CAN ID
    
    Returns:
        Tuple of (CAN ID, data bytes)
    """
    can_id = build_can_id(0x11, motor_id, host_id)
    # Pack index in little-endian format
    data = struct.pack('<H6x', param_index)
    return can_id, data


# Communication Type 18: Write Single Parameter
def pack_write_param_command(motor_id: int, param_index: int, value: float, 
                           host_id: int = 0xFD) -> Tuple[int, bytes]:
    """
    Pack communication type 18: Write single parameter.
    
    Args:
        motor_id: Target motor ID
        param_index: Parameter index
        value: Parameter value (float or int)
        host_id: Host CAN ID
    
    Returns:
        Tuple of (CAN ID, data bytes)
    """
    can_id = build_can_id(0x12, motor_id, host_id)
    
    # Convert value to bytes based on parameter type
    if param_index == PARAM_RUN_MODE or param_index == PARAM_ZERO_STA:
        # uint8 parameters
        value_bytes = struct.pack('<I', int(value))
    elif param_index == PARAM_EPSCAN_TIME:
        # uint16 parameters
        value_bytes = struct.pack('<I', int(value))
    elif param_index == PARAM_CAN_TIMEOUT:
        # uint32 parameters
        value_bytes = struct.pack('<I', int(value))
    else:
        # float parameters (most common)
        value_bytes = struct.pack('<f', float(value))
    
    # Pack: index (little-endian) + 2 zero bytes + value
    data = struct.pack('<H2s4s', param_index, b'\x00\x00', value_bytes)
    return can_id, data


# Communication Type 22: Save Motor Data
def pack_save_data_command(motor_id: int, host_id: int = 0xFD) -> Tuple[int, bytes]:
    """Pack communication type 22: Save motor data to flash."""
    can_id = build_can_id(0x16, motor_id, host_id)
    data = bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])
    return can_id, data


# Communication Type 23: Modify Motor Baudrate
def pack_set_baudrate_command(motor_id: int, baudrate_code: int, host_id: int = 0xFD) -> Tuple[int, bytes]:
    """
    Pack communication type 23: Modify motor baudrate.
    
    Args:
        motor_id: Target motor ID
        baudrate_code: 1=1M, 2=500K, 3=250K, 4=125K
        host_id: Host CAN ID
    
    Returns:
        Tuple of (CAN ID, data bytes)
    """
    can_id = build_can_id(0x17, motor_id, host_id)
    data = bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, baudrate_code])
    return can_id, data


# Communication Type 24: Motor Active Report
def pack_set_active_report_command(motor_id: int, enable: bool, host_id: int = 0xFD) -> Tuple[int, bytes]:
    """
    Pack communication type 24: Enable/disable motor active reporting.
    
    Args:
        motor_id: Target motor ID
        enable: True to enable, False to disable active reporting
        host_id: Host CAN ID
    
    Returns:
        Tuple of (CAN ID, data bytes)
    """
    can_id = build_can_id(0x18, motor_id, host_id)
    cmd = 0x01 if enable else 0x00
    data = bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, cmd])
    return can_id, data


# Communication Type 25: Modify Motor Protocol
def pack_set_protocol_command(motor_id: int, protocol_type: int, host_id: int = 0xFD) -> Tuple[int, bytes]:
    """
    Pack communication type 25: Modify motor protocol.
    
    Args:
        motor_id: Target motor ID
        protocol_type: 0=Private, 1=CANopen, 2=MIT
        host_id: Host CAN ID
    
    Returns:
        Tuple of (CAN ID, data bytes)
    """
    can_id = build_can_id(0x19, motor_id, host_id)
    data = bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, protocol_type])
    return can_id, data


def unpack_feedback_frame(can_id: int, data: bytes) -> MotorStatus:
    """
    Unpack communication type 2 or 24: Motor feedback data.
    
    Args:
        can_id: 29-bit CAN ID
        data: 8-byte data payload
    
    Returns:
        MotorStatus dictionary with current motor state
    """
    # Extract information from CAN ID
    motor_id = (can_id >> 8) & 0xFFFF  # Sender is in bit15-8 of data field
    error_flags = (can_id >> 16) & 0x3F  # bit21-16
    mode = (can_id >> 22) & 0x03  # bit23-22
    
    # Unpack data: high byte first (big-endian)
    pos_int, vel_int, torque_int, temp_int = struct.unpack('>HHHh', data)
    
    # Convert integers back to physical values
    position = uint_to_float(pos_int, P_MIN, P_MAX, 16)
    velocity = uint_to_float(vel_int, V_MIN, V_MAX, 16)
    torque = uint_to_float(torque_int, T_MIN, T_MAX, 16)
    temperature = float(temp_int / 10.0)
    
    return MotorStatus(
        motor_id=motor_id,
        position=position,
        velocity=velocity,
        torque=torque,
        temperature=temperature,
        error_code=error_flags,
        mode=mode
    )


def unpack_device_id_response(data: bytes) -> bytes:
    """
    Unpack communication type 0 response: 64-bit MCU unique identifier.
    
    Args:
        data: 8-byte data payload
    
    Returns:
        64-bit unique identifier as bytes
    """
    return data


def unpack_read_param_response(data: bytes) -> Tuple[int, float]:
    """
    Unpack communication type 17 response: Parameter read result.
    
    Args:
        data: 8-byte data payload
    
    Returns:
        Tuple of (parameter_index, parameter_value)
    """
    # Unpack: index (little-endian) + 2 bytes + value
    index = struct.unpack('<H', data[:2])[0]
    
    # Try to unpack as float first, fall back to int
    try:
        value = struct.unpack('<f', data[4:8])[0]
    except struct.error:
        value = struct.unpack('<I', data[4:8])[0]
    
    return index, value


def unpack_fault_frame(data: bytes) -> Tuple[int, int]:
    """
    Unpack communication type 21: Fault feedback frame.
    
    Args:
        data: 8-byte data payload
    
    Returns:
        Tuple of (fault_value, warning_value)
    """
    fault_value = struct.unpack('<I', data[:4])[0]
    warning_value = struct.unpack('<I', data[4:8])[0]
    return fault_value, warning_value