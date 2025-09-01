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
# Setup CAN interface (example for can0)
sudo ip link set can0 type can bitrate 1000000
sudo ip link set can0 up

# Verify interface is active
ip link show can0
```

## Quick Start

### Basic Usage

```python
from robstride import RobStrideMotor, ProtocolType

# Create motor instance
motor = RobStrideMotor(
    can_id=1,                          # Motor CAN ID
    interface='can0',                  # CAN interface
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
python robstride_cli.py --interface can0 --motor_id 1 info

# Enable motor
python robstride_cli.py --interface can0 --motor_id 1 enable

# Position control
python robstride_cli.py --interface can0 --motor_id 1 position 1.5 --speed-limit 5.0

# Motion control
python robstride_cli.py --interface can0 --motor_id 1 motion --position 1.0 --velocity 0.0 --kp 50.0 --kd 1.0

# Monitor motor status
python robstride_cli.py --interface can0 --motor_id 1 monitor

# Use MIT protocol
python robstride_cli.py --interface can0 --motor_id 1 --mit enable
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

## Multi-Motor Control

Control multiple motors simultaneously:
```python
motors = [
    RobStrideMotor(can_id=1, interface='can0'),
    RobStrideMotor(can_id=2, interface='can0'),
    RobStrideMotor(can_id=3, interface='can0')
]

for motor in motors:
    motor.connect()
    motor.enable()
    motor.set_position_control(position=1.0, speed_limit=5.0)
```

## Examples

The `examples/` directory contains complete usage examples:

- `basic_usage.py` - Basic motor control
- `mit_protocol.py` - MIT protocol usage
- `multi_motor.py` - Multi-motor coordination
- `parameter_management.py` - Parameter access and modification

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

## Testing

Run the test suite:
```bash
python -m pytest tests/
```

## CAN Interface Configuration

### Supported Bitrates
- 1000000 bps (default)
- 500000 bps
- 250000 bps

### Interface Setup
```bash
# Set bitrate and bring up interface
sudo ip link set can0 type can bitrate 1000000
sudo ip link set can0 up

# Monitor CAN traffic
candump can0

# Send raw CAN messages for testing
cansend can0 03FD0100#0000000000000000  # Enable motor ID 1
```

## Troubleshooting

### Common Issues

1. **No response from motor**
   - Check CAN interface is up and configured
   - Verify motor ID and protocol mode
   - Check physical connections

2. **Permission denied on CAN interface**
   - Run with sudo or add user to appropriate groups
   - Check udev rules for CAN interfaces

3. **Protocol mismatch**
   - Verify motor is in correct protocol mode
   - Try both Private and MIT protocols

4. **Parameter access fails**
   - Parameter access only available in Private protocol
   - Check timeout values for slow responses

### Debug Logging

Enable debug logging for detailed information:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## License

This SDK is provided for use with RobStride motors. Please refer to the motor documentation for warranty and support information.

## Support

For technical support and questions:
- Check motor documentation
- Review example code
- Enable debug logging for troubleshooting
