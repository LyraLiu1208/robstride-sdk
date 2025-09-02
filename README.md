# RobStride Motor SDK

A Python SDK for controlling RobStride motors via CAN bus communication.

## Features

- Support for both Private and MIT communication protocols
- Comprehensive motor control modes (position, velocity, current, motion control)
- Parameter management and configuration
- Multi-motor support
- Command-line interface for testing and control
- Thread-safe CAN communication
- Extensive error handling and validation

## Installation

### Requirements

- Python 3.7+
- python-can library
- SocketCAN support (Linux)

### Install Dependencies

```bash
pip install python-can
```

### Setup CAN Interface

```bash
# Setup CAN interface (example for can1)
sudo ip link set can1 type can bitrate 1000000
sudo ip link set can1 up

# Verify interface is active
ip link show can1
```

## Quick Start

### Basic Usage

```python
from robstride import RobStrideMotor, ProtocolType

# Create motor instance
motor = RobStrideMotor(
    can_id=0x7F,                          # Motor CAN ID
    interface='can1',                  # CAN interface
    protocol=ProtocolType.PRIVATE      # Communication protocol
)

# Connect and control
with motor:
    motor.enable()
    motor.set_position_control(position=1.0, speed_limit=5.0)
    print(f"Position: {motor.position:.3f} rad")
```

### Command Line Interface

```bash
# Get motor information
python robstride_cli.py --interface can1 --motor_id 0x7F info

# Enable motor
python robstride_cli.py --interface can1 --motor_id 0x7F enable

# Position control
python robstride_cli.py --interface can1 --motor_id 0x7F position 1.5 --speed-limit 5.0

# Motion control
python robstride_cli.py --interface can1 --motor_id 0x7F motion --position 1.0 --velocity 0.0 --kp 50.0 --kd 1.0

# Monitor motor status
python robstride_cli.py --interface can1 --motor_id 0x7F monitor

# Use MIT protocol
python robstride_cli.py --interface can1 --motor_id 0x7F --mit enable
```

## Protocol Support

### Private Protocol (Default)
- Extended CAN frames (29-bit ID)
- Full parameter access
- All control modes supported
- Device identification

### MIT Protocol
- Standard CAN frames (11-bit ID)
- Motion, position, and velocity control
- Compatible with MIT Cheetah protocol

## Control Modes

### Motion Control
Direct control with position, velocity, gains, and torque:
```python
motor.set_motion_control(
    position=1.0,    # Target position (rad)
    velocity=0.0,    # Target velocity (rad/s)
    kp=50.0,         # Position gain
    kd=1.0,          # Velocity gain
    torque=0.0       # Feed-forward torque (Nm)
)
```

### Position Control
Position tracking with speed limit:
```python
motor.set_position_control(
    position=2.0,      # Target position (rad)
    speed_limit=5.0    # Maximum speed (rad/s)
)
```

### Velocity Control
Constant velocity with current limit:
```python
motor.set_velocity_control(
    velocity=3.0,        # Target velocity (rad/s)
    current_limit=10.0   # Current limit (A)
)
```

### Current Control (Private Protocol Only)
Direct current control:
```python
motor.set_current_control(current=2.0)  # Target current (A)
```

## Parameter Management

Access and modify motor parameters (Private protocol only):
```python
# Read parameters
run_mode = motor.get_parameter(ParameterAddress.RUN_MODE)
max_velocity = motor.get_parameter(ParameterAddress.MAX_VELOCITY)

# Write parameters
motor.set_parameter(ParameterAddress.LIMIT_CURRENT, 15.0)
motor.set_parameter(ParameterAddress.MAX_VELOCITY, 20.0)
```

## Examples

The `examples/` directory contains complete usage examples:

- `basic_usage.py` - Basic motor control
- `mit_protocol.py` - MIT protocol usage

## Error Handling

The SDK provides comprehensive error handling:

```python
try:
    motor.set_position_control(position=100.0)  # Invalid position
except ValueError as e:
    print(f"Parameter error: {e}")

try:
    motor.get_parameter(0x7005, timeout=0.5)
except TimeoutError:
    print("Motor did not respond")
```
