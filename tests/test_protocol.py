"""
Protocol tests for RobStride Motor SDK
"""

import unittest
from robstride.protocol import (
    ProtocolType, ControlMode, CommunicationType, ParameterAddress,
    P_MIN, P_MAX, V_MIN, V_MAX, KP_MIN, KP_MAX, KD_MIN, KD_MAX, T_MIN, T_MAX
)

class TestProtocol(unittest.TestCase):
    """Test protocol constants and enumerations"""
    
    def test_protocol_type(self):
        """Test protocol type enumeration"""
        self.assertEqual(ProtocolType.PRIVATE.value, "private")
        self.assertEqual(ProtocolType.MIT.value, "mit")
    
    def test_control_mode(self):
        """Test control mode enumeration"""
        self.assertEqual(ControlMode.MOTION_CONTROL, 0)
        self.assertEqual(ControlMode.POSITION, 1)
        self.assertEqual(ControlMode.VELOCITY, 2)
        self.assertEqual(ControlMode.CURRENT, 3)
        self.assertEqual(ControlMode.CSP, 1)  # Same as POSITION
        self.assertEqual(ControlMode.SET_ZERO, 6)
    
    def test_communication_type(self):
        """Test communication type constants"""
        self.assertEqual(CommunicationType.GET_SINGLE_PARAMETER, 17)
        self.assertEqual(CommunicationType.SET_SINGLE_PARAMETER, 18)
        self.assertEqual(CommunicationType.MOTION_CONTROL, 1)
        self.assertEqual(CommunicationType.MOTOR_ENABLE, 3)
        self.assertEqual(CommunicationType.MOTOR_STOP, 4)
        self.assertEqual(CommunicationType.SET_POS_ZERO, 6)
        self.assertEqual(CommunicationType.GET_ID, 0)
    
    def test_parameter_addresses(self):
        """Test parameter address constants"""
        self.assertEqual(ParameterAddress.RUN_MODE, 0x7005)
        self.assertEqual(ParameterAddress.TARGET_CURRENT, 0x7006)
        self.assertEqual(ParameterAddress.TARGET_VELOCITY, 0x700A)
        self.assertEqual(ParameterAddress.TARGET_POSITION, 0x7016)
        self.assertEqual(ParameterAddress.LIMIT_VELOCITY, 0x7017)
        self.assertEqual(ParameterAddress.LIMIT_CURRENT, 0x7018)
    
    def test_parameter_ranges(self):
        """Test parameter range constants"""
        # Position range
        self.assertEqual(P_MIN, -12.5)
        self.assertEqual(P_MAX, 12.5)
        
        # Velocity range
        self.assertEqual(V_MIN, -44.0)
        self.assertEqual(V_MAX, 44.0)
        
        # Kp range
        self.assertEqual(KP_MIN, 0.0)
        self.assertEqual(KP_MAX, 500.0)
        
        # Kd range
        self.assertEqual(KD_MIN, 0.0)
        self.assertEqual(KD_MAX, 5.0)
        
        # Torque range
        self.assertEqual(T_MIN, -17.0)
        self.assertEqual(T_MAX, 17.0)

if __name__ == '__main__':
    unittest.main()
