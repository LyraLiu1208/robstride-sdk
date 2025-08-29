"""
Custom exceptions for Robstride SDK
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module defines custom exception classes for different error scenarios
that can occur when communicating with Robstride motors.
"""


class RobstrideException(Exception):
    """Base exception class for all Robstride-related errors."""
    pass


class ConnectionError(RobstrideException):
    """Raised when communication with the motor cannot be established."""
    pass


class TimeoutException(RobstrideException):
    """Raised when a motor operation times out."""
    pass


class MotorFaultException(RobstrideException):
    """Raised when the motor reports a fault condition."""
    
    def __init__(self, message: str, fault_code: int = 0, warning_code: int = 0):
        super().__init__(message)
        self.fault_code = fault_code
        self.warning_code = warning_code
        
    def __str__(self):
        base_msg = super().__str__()
        if self.fault_code or self.warning_code:
            return f"{base_msg} (Fault: 0x{self.fault_code:08X}, Warning: 0x{self.warning_code:08X})"
        return base_msg


class ParameterError(RobstrideException):
    """Raised when invalid parameters are provided to motor commands."""
    pass


class ProtocolError(RobstrideException):
    """Raised when there's an error in the CAN protocol communication."""
    pass
