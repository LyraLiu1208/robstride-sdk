"""
Test Suite for Robstride Protocol Implementation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains unit tests to verify the correctness of the protocol
data packing and unpacking functions. These tests ensure that the SDK
correctly implements the Robstride CAN protocol specification.

Run tests with: python -m pytest tests/
"""

import pytest
import struct
from robstride import protocol


class TestProtocolPacking:
    """Test protocol command packing functions."""
    
    def test_build_can_id(self):
        """Test CAN ID construction."""
        # Test basic ID construction
        can_id = protocol.build_can_id(0x01, 0x7F, 0xFD)
        expected = (0x01 << 24) | (0xFD << 8) | 0x7F
        assert can_id == expected
        
        # Test with different values
        can_id = protocol.build_can_id(0x12, 0x05, 0x1234)
        expected = (0x12 << 24) | (0x1234 << 8) | 0x05
        assert can_id == expected
    
    def test_float_to_uint_conversion(self):
        """Test float to unsigned integer conversion."""
        # Test position conversion (-12.57 to 12.57 rad -> 16-bit)
        # Middle value should map to middle of range
        result = protocol.float_to_uint(0.0, -12.57, 12.57, 16)
        expected = 32767  # Middle of 16-bit range
        assert abs(result - expected) <= 1  # Allow for rounding
        
        # Test min/max values
        result_min = protocol.float_to_uint(-12.57, -12.57, 12.57, 16)
        assert result_min == 0
        
        result_max = protocol.float_to_uint(12.57, -12.57, 12.57, 16)
        assert result_max == 65535
        
        # Test clamping
        result_clamp = protocol.float_to_uint(20.0, -12.57, 12.57, 16)
        assert result_clamp == 65535
    
    def test_uint_to_float_conversion(self):
        """Test unsigned integer to float conversion."""
        # Test round-trip conversion
        original = 5.0
        uint_val = protocol.float_to_uint(original, -12.57, 12.57, 16)
        recovered = protocol.uint_to_float(uint_val, -12.57, 12.57, 16)
        assert abs(recovered - original) < 0.01  # Small tolerance for rounding
        
        # Test edge cases
        recovered_min = protocol.uint_to_float(0, -12.57, 12.57, 16)
        assert abs(recovered_min - (-12.57)) < 0.01
        
        recovered_max = protocol.uint_to_float(65535, -12.57, 12.57, 16)
        assert abs(recovered_max - 12.57) < 0.01
    
    def test_enable_motor_command(self):
        """Test motor enable command packing."""
        can_id, data = protocol.pack_enable_motor_command(0x7F, 0xFD)
        
        # Check CAN ID
        expected_id = (0x03 << 24) | (0xFD << 8) | 0x7F
        assert can_id == expected_id
        
        # Check data (should be all zeros)
        assert data == b'\x00' * 8
    
    def test_disable_motor_command(self):
        """Test motor disable command packing."""
        # Test normal disable
        can_id, data = protocol.pack_disable_motor_command(0x7F, 0xFD, False)
        expected_id = (0x04 << 24) | (0xFD << 8) | 0x7F
        assert can_id == expected_id
        assert data == b'\x00' * 8
        
        # Test disable with error clearing
        can_id, data = protocol.pack_disable_motor_command(0x7F, 0xFD, True)
        assert can_id == expected_id
        assert data == b'\x01' + b'\x00' * 7
    
    def test_motion_control_command(self):
        """Test motion control command packing."""
        can_id, data = protocol.pack_motion_control_command(
            motor_id=0x7F,
            pos=1.0,
            vel=2.0, 
            kp=50.0,
            kd=1.0,
            torque=0.5,
            host_id=0xFD
        )
        
        # Convert expected values
        torque_int = protocol.float_to_uint(0.5, protocol.T_MIN, protocol.T_MAX, 16)
        expected_id = (0x01 << 24) | (torque_int << 8) | 0x7F
        assert can_id == expected_id
        
        # Check data packing (big-endian)
        pos_int = protocol.float_to_uint(1.0, protocol.P_MIN, protocol.P_MAX, 16)
        vel_int = protocol.float_to_uint(2.0, protocol.V_MIN, protocol.V_MAX, 16)
        kp_int = protocol.float_to_uint(50.0, protocol.KP_MIN, protocol.KP_MAX, 16)
        kd_int = protocol.float_to_uint(1.0, protocol.KD_MIN, protocol.KD_MAX, 16)
        
        expected_data = struct.pack('>HHHH', pos_int, vel_int, kp_int, kd_int)
        assert data == expected_data
    
    def test_write_param_command(self):
        """Test parameter write command packing."""
        can_id, data = protocol.pack_write_param_command(
            motor_id=0x7F,
            param_index=0x7005,  # RUN_MODE
            value=2.0,  # Velocity mode
            host_id=0xFD
        )
        
        expected_id = (0x12 << 24) | (0xFD << 8) | 0x7F
        assert can_id == expected_id
        
        # Check data format: index (little-endian) + 2 zeros + value
        expected_data = struct.pack('<H2sI', 0x7005, b'\x00\x00', int(2.0))
        assert data == expected_data


class TestProtocolUnpacking:
    """Test protocol response unpacking functions."""
    
    def test_feedback_frame_unpacking(self):
        """Test motor feedback frame unpacking."""
        # Create test data
        pos_int = protocol.float_to_uint(1.5, protocol.P_MIN, protocol.P_MAX, 16)
        vel_int = protocol.float_to_uint(-2.0, protocol.V_MIN, protocol.V_MAX, 16)
        torque_int = protocol.float_to_uint(0.8, protocol.T_MIN, protocol.T_MAX, 16)
        temp_int = int(45.0 * 10)  # 45.0°C -> 450
        
        test_data = struct.pack('>HHHh', pos_int, vel_int, torque_int, temp_int)
        
        # Create test CAN ID with status info
        motor_id = 0x7F
        error_code = 0x02  # Some error
        mode = 0x02        # Motor mode
        can_id = (0x02 << 24) | (mode << 22) | (error_code << 16) | (motor_id << 8)
        
        status = protocol.unpack_feedback_frame(can_id, test_data)
        
        # Check unpacked values
        assert status['motor_id'] == motor_id
        assert abs(status['position'] - 1.5) < 0.01
        assert abs(status['velocity'] - (-2.0)) < 0.01
        assert abs(status['torque'] - 0.8) < 0.01
        assert abs(status['temperature'] - 45.0) < 0.1
        assert status['error_code'] == error_code
        assert status['mode'] == mode
    
    def test_device_id_response(self):
        """Test device ID response unpacking."""
        test_data = b'\x12\x34\x56\x78\x9A\xBC\xDE\xF0'
        result = protocol.unpack_device_id_response(test_data)
        assert result == test_data
    
    def test_read_param_response(self):
        """Test parameter read response unpacking."""
        # Test float parameter
        param_index = 0x701E  # LOC_KP
        param_value = 30.5
        test_data = struct.pack('<H2sf', param_index, b'\x00\x00', param_value)
        
        index, value = protocol.unpack_read_param_response(test_data)
        assert index == param_index
        assert abs(value - param_value) < 0.001


class TestProtocolConstants:
    """Test protocol constants and ranges."""
    
    def test_parameter_indices(self):
        """Test that parameter indices are correct."""
        assert protocol.PARAM_RUN_MODE == 0x7005
        assert protocol.PARAM_IQ_REF == 0x7006
        assert protocol.PARAM_LOC_KP == 0x701E
        assert protocol.PARAM_SPD_KP == 0x701F
    
    def test_run_mode_constants(self):
        """Test run mode constants."""
        assert protocol.RUN_MODE_MOTION_CONTROL == 0
        assert protocol.RUN_MODE_POSITION_PP == 1
        assert protocol.RUN_MODE_VELOCITY == 2
        assert protocol.RUN_MODE_CURRENT == 3
        assert protocol.RUN_MODE_POSITION_CSP == 5
    
    def test_physical_ranges(self):
        """Test that physical ranges match protocol specification."""
        assert protocol.P_MIN == -12.57
        assert protocol.P_MAX == 12.57
        assert protocol.V_MIN == -50.0
        assert protocol.V_MAX == 50.0
        assert protocol.T_MIN == -5.5
        assert protocol.T_MAX == 5.5


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"])
