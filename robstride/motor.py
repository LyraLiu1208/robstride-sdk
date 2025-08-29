"""
Robstride Motor Control Class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module provides the high-level Motor class for controlling Robstride motors.
It wraps the low-level CAN protocol and provides an intuitive Python API.
"""

import can
import time
import threading
from typing import Optional, Dict, Any, Callable
from . import protocol
from .exceptions import TimeoutException, ConnectionError, ProtocolError


class Motor:
    """
    High-level interface for controlling a single Robstride motor.
    
    This class manages the CAN communication, handles responses asynchronously,
    and provides easy-to-use methods for all motor operations.
    
    Example:
        >>> import can
        >>> from robstride import Motor
        >>> 
        >>> bus = can.interface.Bus(channel='can0', bustype='socketcan', bitrate=1000000)
        >>> motor = Motor(motor_id=1, can_bus=bus)
        >>> 
        >>> motor.enable()
        >>> motor.set_motion_control(pos=1.0, vel=0.0, kp=50.0, kd=1.0, torque=0.0)
        >>> time.sleep(2)
        >>> status = motor.get_status()
        >>> print(f"Position: {status['position']:.3f} rad")
        >>> motor.disable()
        >>> motor.close()
    """
    
    def __init__(self, motor_id: int, can_bus: can.Bus, host_id: int = 0xFD, 
                 response_timeout: float = 1.0):
        """
        Initialize a Motor instance.
        
        Args:
            motor_id: The CAN ID of the target motor (1-255)
            can_bus: python-can Bus instance for communication
            host_id: Host CAN ID (default: 0xFD)
            response_timeout: Default timeout for waiting responses (seconds)
        """
        self.motor_id = motor_id
        self.host_id = host_id
        self.bus = can_bus
        self.response_timeout = response_timeout
        
        # Thread-safe storage for motor status and responses
        self._status: Optional[protocol.MotorStatus] = None
        self._responses: Dict[int, Any] = {}  # comm_type -> response_data
        self._status_lock = threading.RLock()
        self._response_lock = threading.RLock()
        
        # Setup message reception
        self._stop_event = threading.Event()
        self.notifier = can.Notifier(self.bus, [self._on_message_received])
        
        # Callback for status updates
        self._status_callback: Optional[Callable[[protocol.MotorStatus], None]] = None
    
    def set_status_callback(self, callback: Callable[[protocol.MotorStatus], None]):
        """
        Set a callback function to be called whenever motor status is updated.
        
        Args:
            callback: Function that takes a MotorStatus as argument
        """
        self._status_callback = callback
    
    def _on_message_received(self, msg: can.Message):
        """Handle incoming CAN messages from the motor."""
        if not msg.is_extended_id:
            return
            
        # Parse CAN ID
        comm_type = (msg.arbitration_id >> 24) & 0x1F
        data_field = (msg.arbitration_id >> 8) & 0xFFFF
        sender_id = msg.arbitration_id & 0xFF
        
        # Check if this message is from our motor
        if sender_id != self.motor_id:
            return
        
        try:
            if comm_type in [0x02, 0x18]:  # Motor feedback frames
                with self._status_lock:
                    self._status = protocol.unpack_feedback_frame(msg.arbitration_id, msg.data)
                    
                # Call status callback if set
                if self._status_callback:
                    self._status_callback(self._status)
                    
                # Check for faults
                if self._status['error_code'] != 0:
                    fault_msg = f"Motor {self.motor_id} reported fault: 0x{self._status['error_code']:02X}"
                    # Don't raise exception here as it's in callback context
                    # Store fault for later retrieval
                    with self._response_lock:
                        self._responses[0x15] = (self._status['error_code'], 0)
                        
            elif comm_type == 0x00:  # Device ID response
                device_id = protocol.unpack_device_id_response(msg.data)
                with self._response_lock:
                    self._responses[0x00] = device_id
                    
            elif comm_type == 0x11:  # Parameter read response
                index, value = protocol.unpack_read_param_response(msg.data)
                with self._response_lock:
                    self._responses[0x11] = (index, value)
                    
            elif comm_type == 0x15:  # Fault frame
                fault, warning = protocol.unpack_fault_frame(msg.data)
                with self._response_lock:
                    self._responses[0x15] = (fault, warning)
                    
        except Exception as e:
            # Log error but don't let it crash the callback
            print(f"Error processing message from motor {self.motor_id}: {e}")
    
    def _send_command(self, can_id: int, data: bytes) -> None:
        """Send a CAN command to the motor."""
        message = can.Message(
            arbitration_id=can_id,
            data=data,
            is_extended_id=True
        )
        try:
            self.bus.send(message)
        except can.CanError as e:
            raise ConnectionError(f"Failed to send command to motor {self.motor_id}: {e}") from e
    
    def _wait_for_response(self, comm_type: int, timeout: Optional[float] = None) -> Any:
        """Wait for a specific response type from the motor."""
        if timeout is None:
            timeout = self.response_timeout
            
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self._response_lock:
                if comm_type in self._responses:
                    return self._responses.pop(comm_type)
            time.sleep(0.001)  # Small sleep to prevent busy waiting
            
        raise TimeoutException(f"No response from motor {self.motor_id} for command type 0x{comm_type:02X}")
    
    # ========================== Basic Motor Control ==========================
    
    def enable(self) -> None:
        """
        Enable the motor (Communication Type 3).
        
        After enabling, the motor will be ready to accept motion commands.
        """
        can_id, data = protocol.pack_enable_motor_command(self.motor_id, self.host_id)
        self._send_command(can_id, data)
    
    def disable(self, clear_errors: bool = False) -> None:
        """
        Disable the motor (Communication Type 4).
        
        Args:
            clear_errors: If True, also clear any existing motor faults
        """
        can_id, data = protocol.pack_disable_motor_command(self.motor_id, self.host_id, clear_errors)
        self._send_command(can_id, data)
    
    def set_zero_position(self) -> None:
        """
        Set the current position as the new zero position (Communication Type 6).
        
        Note: This function is only available in CSP and Motion Control modes.
        """
        can_id, data = protocol.pack_set_zero_position_command(self.motor_id, self.host_id)
        self._send_command(can_id, data)
    
    # ========================== Motion Control ==========================
    
    def set_motion_control(self, pos: float, vel: float, kp: float, kd: float, torque: float) -> None:
        """
        Send motion control command (Communication Type 1).
        
        This is the most flexible control mode, implementing:
        torque_output = Kp * (pos_target - pos_actual) + Kd * (vel_target - vel_actual) + torque_feedforward
        
        Args:
            pos: Target position in radians (-12.57 to 12.57)
            vel: Target velocity in rad/s (-50 to 50)
            kp: Position gain (0 to 500)
            kd: Damping gain (0 to 5)
            torque: Feedforward torque in Nm (-5.5 to 5.5)
        
        Examples:
            # Position control (spring to position 1.0 rad)
            motor.set_motion_control(pos=1.0, vel=0.0, kp=50.0, kd=1.0, torque=0.0)
            
            # Velocity control (constant 2 rad/s)
            motor.set_motion_control(pos=0.0, vel=2.0, kp=0.0, kd=1.0, torque=0.0)
            
            # Damping mode (resist external motion)
            motor.set_motion_control(pos=0.0, vel=0.0, kp=0.0, kd=2.0, torque=0.0)
            
            # Torque control (constant 1 Nm)
            motor.set_motion_control(pos=0.0, vel=0.0, kp=0.0, kd=0.0, torque=1.0)
        """
        can_id, data = protocol.pack_motion_control_command(
            self.motor_id, pos, vel, kp, kd, torque, self.host_id
        )
        self._send_command(can_id, data)
    
    # ========================== Parameter Control ==========================
    
    def set_run_mode(self, mode: int) -> None:
        """
        Set the motor run mode (writes parameter 0x7005).
        
        Args:
            mode: Run mode
                0: Motion control mode (default)
                1: Position mode (PP)
                2: Velocity mode
                3: Current mode
                5: Position mode (CSP)
        
        Note: Motor must be disabled when changing modes.
        """
        can_id, data = protocol.pack_write_param_command(
            self.motor_id, protocol.PARAM_RUN_MODE, mode, self.host_id
        )
        self._send_command(can_id, data)
    
    def set_current_reference(self, current: float) -> None:
        """
        Set current mode Iq reference (writes parameter 0x7006).
        
        Args:
            current: Target current in Amperes (-11 to 11)
        """
        can_id, data = protocol.pack_write_param_command(
            self.motor_id, protocol.PARAM_IQ_REF, current, self.host_id
        )
        self._send_command(can_id, data)
    
    def set_velocity_reference(self, velocity: float) -> None:
        """
        Set velocity mode reference (writes parameter 0x700A).
        
        Args:
            velocity: Target velocity in rad/s (-50 to 50)
        """
        can_id, data = protocol.pack_write_param_command(
            self.motor_id, protocol.PARAM_SPD_REF, velocity, self.host_id
        )
        self._send_command(can_id, data)
    
    def set_position_reference(self, position: float) -> None:
        """
        Set position mode reference (writes parameter 0x7016).
        
        Args:
            position: Target position in radians
        """
        can_id, data = protocol.pack_write_param_command(
            self.motor_id, protocol.PARAM_LOC_REF, position, self.host_id
        )
        self._send_command(can_id, data)
    
    def set_velocity_limit(self, limit: float) -> None:
        """
        Set velocity limit for position modes (writes parameter 0x7017).
        
        Args:
            limit: Maximum velocity in rad/s (0 to 50)
        """
        can_id, data = protocol.pack_write_param_command(
            self.motor_id, protocol.PARAM_LIMIT_SPD, limit, self.host_id
        )
        self._send_command(can_id, data)
    
    def set_current_limit(self, limit: float) -> None:
        """
        Set current limit for velocity/position modes (writes parameter 0x7018).
        
        Args:
            limit: Maximum current in Amperes (0 to 11)
        """
        can_id, data = protocol.pack_write_param_command(
            self.motor_id, protocol.PARAM_LIMIT_CUR, limit, self.host_id
        )
        self._send_command(can_id, data)
    
    def set_position_kp(self, kp: float) -> None:
        """Set position control Kp gain (writes parameter 0x701E)."""
        can_id, data = protocol.pack_write_param_command(
            self.motor_id, protocol.PARAM_LOC_KP, kp, self.host_id
        )
        self._send_command(can_id, data)
    
    def set_velocity_kp(self, kp: float) -> None:
        """Set velocity control Kp gain (writes parameter 0x701F)."""
        can_id, data = protocol.pack_write_param_command(
            self.motor_id, protocol.PARAM_SPD_KP, kp, self.host_id
        )
        self._send_command(can_id, data)
    
    def set_velocity_ki(self, ki: float) -> None:
        """Set velocity control Ki gain (writes parameter 0x7020)."""
        can_id, data = protocol.pack_write_param_command(
            self.motor_id, protocol.PARAM_SPD_KI, ki, self.host_id
        )
        self._send_command(can_id, data)
    
    # ========================== Status and Diagnostics ==========================
    
    def get_status(self, timeout: Optional[float] = None) -> protocol.MotorStatus:
        """
        Get the latest motor status.
        
        Args:
            timeout: Maximum time to wait for fresh status (seconds)
        
        Returns:
            MotorStatus dictionary with current motor state
        
        Raises:
            TimeoutException: If no status is received within timeout
        """
        if timeout is None:
            timeout = self.response_timeout
            
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self._status_lock:
                if self._status is not None:
                    return self._status.copy()
            time.sleep(0.001)
            
        raise TimeoutException(f"No status received from motor {self.motor_id}")
    
    def get_device_id(self, timeout: Optional[float] = None) -> bytes:
        """
        Get the motor's 64-bit unique device ID.
        
        Args:
            timeout: Response timeout in seconds
        
        Returns:
            8-byte device ID
        """
        can_id, data = protocol.pack_get_device_id_command(self.motor_id, self.host_id)
        self._send_command(can_id, data)
        return self._wait_for_response(0x00, timeout)
    
    def read_parameter(self, param_index: int, timeout: Optional[float] = None) -> float:
        """
        Read a single parameter from the motor.
        
        Args:
            param_index: Parameter index (e.g., protocol.PARAM_LOC_KP)
            timeout: Response timeout in seconds
        
        Returns:
            Parameter value
        """
        can_id, data = protocol.pack_read_param_command(self.motor_id, param_index, self.host_id)
        self._send_command(can_id, data)
        index, value = self._wait_for_response(0x11, timeout)
        
        if index != param_index:
            raise ProtocolError(f"Received parameter 0x{index:04X}, expected 0x{param_index:04X}")
        
        return value
    
    def save_configuration(self) -> None:
        """
        Save current motor configuration to flash memory (Communication Type 22).
        
        This saves parameters that were written with Communication Type 18.
        """
        can_id, data = protocol.pack_save_data_command(self.motor_id, self.host_id)
        self._send_command(can_id, data)
    
    def set_active_reporting(self, enable: bool) -> None:
        """
        Enable or disable active status reporting (Communication Type 24).
        
        Args:
            enable: True to enable 10ms status reports, False to disable
        """
        can_id, data = protocol.pack_set_active_report_command(self.motor_id, enable, self.host_id)
        self._send_command(can_id, data)
    
    def set_motor_id(self, new_id: int) -> None:
        """
        Change the motor's CAN ID (Communication Type 7).
        
        Args:
            new_id: New CAN ID for the motor (1-255)
        
        Note: This takes effect immediately. Update your Motor instance accordingly.
        """
        can_id, data = protocol.pack_set_motor_id_command(self.motor_id, new_id, self.host_id)
        self._send_command(can_id, data)
        # Update our own motor_id
        self.motor_id = new_id
    
    # ========================== Cleanup ==========================
    
    def close(self) -> None:
        """
        Clean up resources and stop background threads.
        
        Call this when you're done with the motor to ensure proper cleanup.
        """
        self._stop_event.set()
        if hasattr(self, 'notifier'):
            self.notifier.stop()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# ========================== Convenience Functions ==========================

def create_motor_from_can_interface(motor_id: int, interface: str = 'socketcan', 
                                   channel: str = 'can0', bitrate: int = 1000000, 
                                   **kwargs) -> Motor:
    """
    Create a Motor instance with a new CAN bus.
    
    Args:
        motor_id: Motor CAN ID
        interface: CAN interface type ('socketcan', 'pcan', 'kvaser', etc.)
        channel: CAN channel name
        bitrate: CAN bitrate (default: 1000000 for 1Mbps)
        **kwargs: Additional arguments passed to Motor constructor
    
    Returns:
        Motor instance
    
    Example:
        >>> motor = create_motor_from_can_interface(1, 'pcan', 'PCAN_USBBUS1')
        >>> motor.enable()
        >>> # ... use motor ...
        >>> motor.close()
    """
    bus = can.interface.Bus(channel=channel, bustype=interface, bitrate=bitrate)
    return Motor(motor_id, bus, **kwargs)