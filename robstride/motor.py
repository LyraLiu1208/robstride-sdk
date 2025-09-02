"""
RobStride Motor control class.
"""

import time
import logging
from typing import Optional, Union
from threading import Lock

from .protocol import (
    ControlMode, CommunicationType, ParameterAddress,
    P_MIN, P_MAX, V_MIN, V_MAX, KP_MIN, KP_MAX, KD_MIN, KD_MAX, T_MIN, T_MAX
)
from .utils import (
    float_to_uint, uint16_to_float, bytes_to_float, float_to_bytes, 
    validate_parameter_range
)
from .can_interface import CANInterface

logger = logging.getLogger(__name__)

class RobStrideMotor:
    """RobStride motor controller"""
    
    def __init__(self, 
                 can_id: int, 
                 interface: str = 'can0',
                 master_id: int = 0xFD,
                 timeout: float = 1.0):
        """
        Initialize RobStride motor.
        
        Args:
            can_id: Motor CAN ID (1-255)
            interface: CAN interface name (e.g., 'can0', 'can1')
            master_id: Master controller ID (default: 0xFD)
            timeout: Response timeout in seconds
        """
        self.can_id = can_id
        self.master_id = master_id
        self.timeout = timeout
        
        # CAN interface
        self.can_interface = CANInterface(interface)
        
        # Motor state
        self.position = 0.0
        self.velocity = 0.0
        self.torque = 0.0
        self.temperature = 0.0
        self.error_code = 0
        self.run_mode = 0
        self.unique_id = None
        
        # Response handling
        self._response_lock = Lock()
        self._last_response = None
        self._waiting_for_response = False
        
        # Status
        self._connected = False
        self._enabled = False
        
    def connect(self):
        """Connect to motor via CAN bus"""
        try:
            self.can_interface.connect()
            self.can_interface.add_message_callback(self._on_can_message)
            self._connected = True
            logger.info(f"Connected to motor {self.can_id} on {self.can_interface.interface_name}")
            
            # Get device ID to verify connection
            self.get_device_id()
            
        except Exception as e:
            logger.error(f"Failed to connect to motor {self.can_id}: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from motor"""
        if self._connected:
            try:
                self.disable()
            except Exception:
                pass  # Ignore errors during shutdown
            
            self.can_interface.disconnect()
            self._connected = False
            logger.info(f"Disconnected from motor {self.can_id}")
    
    def enable(self):
        """Enable motor"""
        if not self._connected:
            raise RuntimeError("Motor not connected")
        
        can_id = (CommunicationType.MOTOR_ENABLE << 24) | (self.master_id << 8) | self.can_id
        data = [0x00] * 8
        is_extended = True
        
        self._send_can_message(can_id, data, is_extended)
        self._enabled = True
        logger.info(f"Motor {self.can_id} enabled")
    
    def disable(self, clear_error: bool = False):
        """
        Disable motor.
        
        Args:
            clear_error: Clear error flags when disabling
        """
        if not self._connected:
            return
        
        can_id = (CommunicationType.MOTOR_STOP << 24) | (self.master_id << 8) | self.can_id
        data = [int(clear_error)] + [0x00] * 7
        is_extended = True
        
        self._send_can_message(can_id, data, is_extended)
        self._enabled = False
        logger.info(f"Motor {self.can_id} disabled")
    
    def set_zero_position(self):
        """Set current position as zero"""
        if not self._enabled:
            raise RuntimeError("Motor not enabled")
        
        can_id = (CommunicationType.SET_POS_ZERO << 24) | (self.master_id << 8) | self.can_id
        data = [0x01] + [0x00] * 7
        is_extended = True
        
        self._send_can_message(can_id, data, is_extended)
        logger.info(f"Set zero position for motor {self.can_id}")
    
    def set_motion_control(self, 
                          position: float = 0.0,
                          velocity: float = 0.0, 
                          kp: float = 0.0,
                          kd: float = 0.0,
                          torque: float = 0.0):
        """
        Send motion control command using private protocol.
        
        Args:
            position: Target position (radians)
            velocity: Target velocity (rad/s)
            kp: Position gain
            kd: Velocity gain  
            torque: Feed-forward torque (Nm)
        """
        if not self._enabled:
            raise RuntimeError("Motor not enabled")
        
        # Validate parameters
        validate_parameter_range("position", position, P_MIN, P_MAX)
        validate_parameter_range("velocity", velocity, V_MIN, V_MAX)
        validate_parameter_range("kp", kp, KP_MIN, KP_MAX)
        validate_parameter_range("kd", kd, KD_MIN, KD_MAX)
        validate_parameter_range("torque", torque, T_MIN, T_MAX)
        
        self._private_motion_control(position, velocity, kp, kd, torque)
    
    def set_position_control(self, position: float, speed_limit: float = 5.0):
        """
        Set position control mode.
        
        Args:
            position: Target position (radians)
            speed_limit: Speed limit (rad/s)
        """
        if not self._enabled:
            raise RuntimeError("Motor not enabled")
        
        validate_parameter_range("position", position, -4*3.14159, 4*3.14159)
        validate_parameter_range("speed_limit", speed_limit, 0, 44.0)
        
        # Set to position control mode
        self.set_parameter(ParameterAddress.RUN_MODE, ControlMode.POSITION)
        time.sleep(0.01)
        # Set target position
        self.set_parameter(ParameterAddress.TARGET_POSITION, position)
        time.sleep(0.01)
        # Set speed limit
        self.set_parameter(ParameterAddress.LIMIT_VELOCITY, speed_limit)
    
    def set_velocity_control(self, velocity: float, current_limit: float = 10.0):
        """
        Set velocity control mode.
        
        Args:
            velocity: Target velocity (rad/s)
            current_limit: Current limit (A)
        """
        if not self._enabled:
            raise RuntimeError("Motor not enabled")
        
        validate_parameter_range("velocity", velocity, -30.0, 30.0)
        validate_parameter_range("current_limit", current_limit, 0, 23.0)
        
        # Set to velocity control mode
        self.set_parameter(ParameterAddress.RUN_MODE, ControlMode.VELOCITY)
        time.sleep(0.01)
        # Set target velocity
        self.set_parameter(ParameterAddress.TARGET_VELOCITY, velocity)
        time.sleep(0.01)
        # Set current limit
        self.set_parameter(ParameterAddress.LIMIT_CURRENT, current_limit)
    
    def set_current_control(self, current: float):
        """
        Set current control mode.
        
        Args:
            current: Target current (A)
        """
        if not self._enabled:
            raise RuntimeError("Motor not enabled")
        
        validate_parameter_range("current", current, -23.0, 23.0)
        
        # Set to current control mode
        self.set_parameter(ParameterAddress.RUN_MODE, ControlMode.CURRENT)
        time.sleep(0.01)
        # Set target current
        self.set_parameter(ParameterAddress.TARGET_CURRENT, current)
    
    def set_parameter(self, address: int, value: Union[int, float]):
        """
        Set motor parameter.
        
        Args:
            address: Parameter address
            value: Parameter value
        """
        can_id = (CommunicationType.SET_SINGLE_PARAMETER << 24) | (self.master_id << 8) | self.can_id
        
        if isinstance(value, int) and 0 <= value < 256:
            # uint8_t parameter
            data = [
                address & 0xFF, (address >> 8) & 0xFF,
                0x00, 0x00,
                value, 0x00, 0x00, 0x00
            ]
        else:
            # float parameter
            value_bytes = float_to_bytes(float(value))
            data = [
                address & 0xFF, (address >> 8) & 0xFF,
                0x00, 0x00
            ] + value_bytes
        
        self._send_can_message(can_id, data, True)
        logger.debug(f"Set parameter 0x{address:04X} = {value}")
    
    def get_parameter(self, address: int, timeout: Optional[float] = None) -> Union[int, float]:
        """
        Get motor parameter.
        
        Args:
            address: Parameter address
            timeout: Response timeout (uses default if None)
            
        Returns:
            Parameter value
        """
        can_id = (CommunicationType.GET_SINGLE_PARAMETER << 24) | (self.master_id << 8) | self.can_id
        data = [
            address & 0xFF, (address >> 8) & 0xFF,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00
        ]
        
        response = self._send_and_wait_response(can_id, data, True, timeout)
        if response:
            return self._parse_parameter_response(response, address)
        else:
            raise TimeoutError(f"No response for parameter 0x{address:04X}")
    
    def get_device_id(self, timeout: Optional[float] = None) -> Optional[bytes]:
        """
        Get device unique ID.
        
        Args:
            timeout: Response timeout (uses default if None)
            
        Returns:
            Device unique ID (8 bytes) or None if no response
        """
        can_id = (CommunicationType.GET_ID << 24) | (self.master_id << 8) | self.can_id
        data = [0x00] * 8
        
        response = self._send_and_wait_response(can_id, data, True, timeout)
        if response:
            return bytes(response['data'])
        return None
    
    def _private_motion_control(self, position: float, velocity: float, kp: float, kd: float, torque: float):
        """Private protocol motion control"""
        # Encode torque in CAN ID
        torque_encoded = float_to_uint(torque, T_MIN, T_MAX, 16)
        can_id = (CommunicationType.MOTION_CONTROL << 24) | (torque_encoded << 8) | self.can_id
        
        # Encode other parameters in data
        pos_encoded = float_to_uint(position, P_MIN, P_MAX, 16)
        vel_encoded = float_to_uint(velocity, V_MIN, V_MAX, 16)
        kp_encoded = float_to_uint(kp, KP_MIN, KP_MAX, 16)
        kd_encoded = float_to_uint(kd, KD_MIN, KD_MAX, 16)
        
        data = [
            (pos_encoded >> 8) & 0xFF, pos_encoded & 0xFF,
            (vel_encoded >> 8) & 0xFF, vel_encoded & 0xFF,
            (kp_encoded >> 8) & 0xFF, kp_encoded & 0xFF,
            (kd_encoded >> 8) & 0xFF, kd_encoded & 0xFF
        ]
        
        self._send_can_message(can_id, data, True)
    
    def _send_can_message(self, can_id: int, data: list, is_extended: bool):
        """Send CAN message"""
        try:
            self.can_interface.send_message(can_id, data, is_extended)
        except Exception as e:
            logger.error(f"Failed to send CAN message to motor {self.can_id}: {e}")
            raise
    
    def _send_and_wait_response(self, can_id: int, data: list, is_extended: bool, timeout: Optional[float] = None) -> Optional[dict]:
        """Send message and wait for response"""
        if timeout is None:
            timeout = self.timeout
        
        with self._response_lock:
            self._last_response = None
            self._waiting_for_response = True
            
            self._send_can_message(can_id, data, is_extended)
            
            # Wait for response
            start_time = time.time()
            while self._waiting_for_response and (time.time() - start_time) < timeout:
                time.sleep(0.001)  # 1ms polling
            
            self._waiting_for_response = False
            return self._last_response
    
    def _on_can_message(self, can_id: int, data: list, is_extended: bool):
        """Handle received CAN message"""
        try:
            self._parse_private_feedback(can_id, data, is_extended)
        except Exception as e:
            logger.error(f"Error parsing CAN message: {e}")
    
    def _parse_private_feedback(self, can_id: int, data: list, is_extended: bool):
        """Parse private protocol feedback"""
        if not is_extended:
            return
        
        comm_type = (can_id & 0x3F000000) >> 24
        error_code = (can_id & 0x3F0000) >> 16
        motor_id = (can_id & 0xFF00) >> 8
        
        # Check if message is for this motor
        if motor_id != self.can_id and (can_id & 0xFF) != 0xFE:
            return
        
        if comm_type == 2:  # Status feedback
            self.position = uint16_to_float((data[0] << 8) | data[1], P_MIN, P_MAX, 16)
            self.velocity = uint16_to_float((data[2] << 8) | data[3], V_MIN, V_MAX, 16)
            self.torque = uint16_to_float((data[4] << 8) | data[5], T_MIN, T_MAX, 16)
            self.temperature = ((data[6] << 8) | data[7]) * 0.1
            self.error_code = error_code
            
        elif comm_type == 17:  # Parameter response
            if self._waiting_for_response:
                self._last_response = {'can_id': can_id, 'data': data}
                self._waiting_for_response = False
                
        elif (can_id & 0xFF) == 0xFE:  # Device ID response
            self.unique_id = bytes(data)
            if self._waiting_for_response:
                self._last_response = {'can_id': can_id, 'data': data}
                self._waiting_for_response = False
    
    def _parse_parameter_response(self, response: dict, address: int) -> Union[int, float]:
        """Parse parameter response"""
        data = response['data']
        param_address = (data[1] << 8) | data[0]
        
        if param_address != address:
            raise ValueError(f"Response address mismatch: expected 0x{address:04X}, got 0x{param_address:04X}")
        
        if address == ParameterAddress.RUN_MODE:
            return data[4]
        else:
            return bytes_to_float(data[4:8])
    
    @property
    def is_connected(self) -> bool:
        """Check if motor is connected"""
        return self._connected
    
    @property
    def is_enabled(self) -> bool:
        """Check if motor is enabled"""
        return self._enabled
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
