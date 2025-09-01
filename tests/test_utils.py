"""
Unit tests for RobStride Motor SDK utilities
"""

import unittest
import struct
from robstride.utils import (
    float_to_uint, uint16_to_float, bytes_to_float, float_to_bytes,
    map_faults, validate_parameter_range, clamp
)
from robstride.protocol import P_MIN, P_MAX, V_MIN, V_MAX, KP_MIN, KP_MAX

class TestUtils(unittest.TestCase):
    """Test utility functions"""
    
    def test_float_to_uint(self):
        """Test float to unsigned integer conversion"""
        # Test position encoding (16-bit)
        self.assertEqual(float_to_uint(0.0, P_MIN, P_MAX, 16), 32768)  # Mid-range
        self.assertEqual(float_to_uint(P_MIN, P_MIN, P_MAX, 16), 0)     # Minimum
        self.assertEqual(float_to_uint(P_MAX, P_MIN, P_MAX, 16), 65535) # Maximum
        
        # Test clamping
        self.assertEqual(float_to_uint(P_MAX + 1, P_MIN, P_MAX, 16), 65535)  # Over max
        self.assertEqual(float_to_uint(P_MIN - 1, P_MIN, P_MAX, 16), 0)      # Under min
    
    def test_uint16_to_float(self):
        """Test unsigned integer to float conversion"""
        # Test position decoding (16-bit)
        self.assertAlmostEqual(uint16_to_float(32768, P_MIN, P_MAX, 16), 0.0, places=3)
        self.assertAlmostEqual(uint16_to_float(0, P_MIN, P_MAX, 16), P_MIN, places=3)
        self.assertAlmostEqual(uint16_to_float(65535, P_MIN, P_MAX, 16), P_MAX, places=3)
    
    def test_round_trip_conversion(self):
        """Test float->uint->float round trip conversion"""
        test_values = [0.0, 1.0, -1.0, 5.5, -7.3]
        
        for value in test_values:
            if P_MIN <= value <= P_MAX:
                encoded = float_to_uint(value, P_MIN, P_MAX, 16)
                decoded = uint16_to_float(encoded, P_MIN, P_MAX, 16)
                self.assertAlmostEqual(value, decoded, places=2)
    
    def test_bytes_to_float(self):
        """Test byte array to float conversion"""
        # Test known float value
        test_value = 3.14159
        byte_data = list(struct.pack('<f', test_value))
        result = bytes_to_float(byte_data)
        self.assertAlmostEqual(result, test_value, places=5)
    
    def test_float_to_bytes(self):
        """Test float to byte array conversion"""
        test_value = 2.71828
        byte_data = float_to_bytes(test_value)
        expected = list(struct.pack('<f', test_value))
        self.assertEqual(byte_data, expected)
    
    def test_map_faults(self):
        """Test MIT to private protocol error mapping"""
        # Test individual fault bits
        self.assertEqual(map_faults(1 << 14), 1 << 4)  # Overload -> bit 4
        self.assertEqual(map_faults(1 << 7), 1 << 5)   # Not calibrated -> bit 5
        self.assertEqual(map_faults(1 << 3), 1 << 3)   # Encoder error -> bit 3
        self.assertEqual(map_faults(1 << 2), 1 << 0)   # Under voltage -> bit 0
        self.assertEqual(map_faults(1 << 1), 1 << 1)   # Over current -> bit 1
        self.assertEqual(map_faults(1 << 0), 1 << 2)   # Locked rotor -> bit 2
        
        # Test combined faults
        combined_fault = (1 << 14) | (1 << 1) | (1 << 0)
        expected = (1 << 4) | (1 << 1) | (1 << 2)
        self.assertEqual(map_faults(combined_fault), expected)
    
    def test_validate_parameter_range(self):
        """Test parameter validation"""
        # Valid parameters should not raise exceptions
        validate_parameter_range("test", 5.0, 0.0, 10.0)
        validate_parameter_range("test", 0.0, 0.0, 10.0)
        validate_parameter_range("test", 10.0, 0.0, 10.0)
        
        # Invalid parameters should raise ValueError
        with self.assertRaises(ValueError):
            validate_parameter_range("test", -1.0, 0.0, 10.0)
        
        with self.assertRaises(ValueError):
            validate_parameter_range("test", 11.0, 0.0, 10.0)
    
    def test_clamp(self):
        """Test value clamping"""
        self.assertEqual(clamp(5.0, 0.0, 10.0), 5.0)   # Within range
        self.assertEqual(clamp(-1.0, 0.0, 10.0), 0.0)  # Below minimum
        self.assertEqual(clamp(15.0, 0.0, 10.0), 10.0) # Above maximum
        self.assertEqual(clamp(0.0, 0.0, 10.0), 0.0)   # At minimum
        self.assertEqual(clamp(10.0, 0.0, 10.0), 10.0) # At maximum

if __name__ == '__main__':
    unittest.main()
