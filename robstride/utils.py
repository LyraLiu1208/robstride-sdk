"""
Utility functions for RobStride motor communication.
"""

import struct
from .protocol import P_MIN, P_MAX, V_MIN, V_MAX, KP_MIN, KP_MAX, KD_MIN, KD_MAX, T_MIN, T_MAX

def float_to_uint(x, x_min, x_max, bits):
    """
    Convert float to unsigned integer with specified bit width.
    
    Args:
        x: Input float value
        x_min: Minimum value of range
        x_max: Maximum value of range
        bits: Number of bits for encoding
        
    Returns:
        Encoded unsigned integer
    """
    span = x_max - x_min
    offset = x_min
    
    # Clamp to range
    if x > x_max:
        x = x_max
    elif x < x_min:
        x = x_min
    
    return int((x - offset) * ((1 << bits) - 1) / span)

def uint16_to_float(x, x_min, x_max, bits):
    """
    Convert unsigned integer to float with specified bit width.
    
    Args:
        x: Input unsigned integer
        x_min: Minimum value of range
        x_max: Maximum value of range
        bits: Number of bits for decoding
        
    Returns:
        Decoded float value
    """
    span = (1 << bits) - 1
    x &= span
    offset = x_max - x_min
    return offset * x / span + x_min

def bytes_to_float(byte_data):
    """
    Convert 4-byte array to float (little endian to match C++ implementation).
    C++ code: uint32_t data = bytedata[7]<<24|bytedata[6]<<16|bytedata[5]<<8|bytedata[4];
    This suggests big-endian byte order, but we need to check actual usage.
    
    Args:
        byte_data: List of 4 bytes
        
    Returns:
        Float value
    """
    # Default to little endian (most common for embedded systems)
    return struct.unpack('<f', bytes(byte_data))[0]

def float_to_bytes(value):
    """
    Convert float to 4-byte array (little endian).
    
    Args:
        value: Float value
        
    Returns:
        List of 4 bytes
    """
    return list(struct.pack('<f', value))

def map_faults(fault16):
    """
    Map MIT 16-bit error code to private protocol 8-bit error code.
    
    Args:
        fault16: 16-bit MIT error code
        
    Returns:
        8-bit private protocol error code
    """
    fault8 = 0
    
    if fault16 & (1 << 14):  # Overload protection
        fault8 |= (1 << 4)
    if fault16 & (1 << 7):   # Not calibrated
        fault8 |= (1 << 5)
    if fault16 & (1 << 3):   # Encoder error
        fault8 |= (1 << 3)
    if fault16 & (1 << 2):   # Under voltage protection
        fault8 |= (1 << 0)
    if fault16 & (1 << 1):   # Over current protection
        fault8 |= (1 << 1)
    if fault16 & (1 << 0):   # Locked rotor
        fault8 |= (1 << 2)
    
    return fault8

def validate_parameter_range(param_name, value, min_val, max_val):
    """
    Validate parameter is within acceptable range.
    
    Args:
        param_name: Name of parameter for error messages
        value: Value to validate
        min_val: Minimum acceptable value
        max_val: Maximum acceptable value
        
    Raises:
        ValueError: If value is outside acceptable range
    """
    if value < min_val or value > max_val:
        raise ValueError(f"{param_name} must be between {min_val} and {max_val}, got {value}")

def clamp(value, min_val, max_val):
    """
    Clamp value to specified range.
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Clamped value
    """
    return max(min_val, min(max_val, value))
