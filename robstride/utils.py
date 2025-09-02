"""
Utility functions for RobStride motor communication.
"""

import struct

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
