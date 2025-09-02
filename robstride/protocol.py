"""
Protocol constants and configurations for RobStride motor communication.
"""

from enum import IntEnum

class ControlMode(IntEnum):
    """Motor control modes - matching C++ header exactly"""
    MOTION_CONTROL = 0   # move_control_mode
    POSITION = 1         # Pos_control_mode (PP position mode)
    VELOCITY = 2         # Speed_control_mode
    CURRENT = 3          # Elect_control_mode
    SET_ZERO = 4         # Set_Zero_mode (NOTE: C++ shows 4, not 6!)
    CSP = 5              # CSP_control_mode (CSP position mode)

class CommunicationType(IntEnum):
    """Private protocol communication types - matching C++ header exactly"""
    GET_ID = 0x00                      # Communication_Type_Get_ID
    MOTION_CONTROL = 0x01              # Communication_Type_MotionControl  
    MOTOR_REQUEST = 0x02               # Communication_Type_MotorRequest
    MOTOR_ENABLE = 0x03                # Communication_Type_MotorEnable
    MOTOR_STOP = 0x04                  # Communication_Type_MotorStop
    SET_POS_ZERO = 0x06                # Communication_Type_SetPosZero
    GET_SINGLE_PARAMETER = 0x11        # Communication_Type_GetSingleParameter
    SET_SINGLE_PARAMETER = 0x12        # Communication_Type_SetSingleParameter

class ParameterAddress(IntEnum):
    """Parameter addresses for private protocol"""
    RUN_MODE = 0x7005      # uint8_t: 0-motion, 1-position, 2-velocity, 3-current
    TARGET_CURRENT = 0x7006  # float: -23~23A
    TARGET_VELOCITY = 0x700A # float: -30~30rad/s
    TARGET_POSITION = 0x7016 # float: -4π~4π
    LIMIT_VELOCITY = 0x7017  # float: 0~44rad/s
    LIMIT_CURRENT = 0x7018   # float: 0~23A
    ACCELERATION = 0x7022    # float: acceleration parameter
    MAX_VELOCITY = 0x7024    # float: PP mode max velocity
    ACCELERATION_SET = 0x7025 # float: PP mode acceleration

# Physical parameter limits
P_MIN = -12.5   # Position range (radians)
P_MAX = 12.5
V_MIN = -44.0   # Velocity range (rad/s)
V_MAX = 44.0
KP_MIN = 0.0    # Kp range
KP_MAX = 500.0
KD_MIN = 0.0    # Kd range  
KD_MAX = 5.0
T_MIN = -17.0   # Torque range (Nm)
T_MAX = 17.0
