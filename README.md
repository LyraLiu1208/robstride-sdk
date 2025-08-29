# Robstride Python SDK

A comprehensive Python SDK for controlling Robstride motors via CAN bus communication.

## Overview

The Robstride SDK provides a simple, powerful interface for controlling Robstride motors. It implements the complete CAN protocol specification and offers both low-level protocol access and high-level motor control functions.

## Features

- **Complete Protocol Implementation**: Full support for all Robstride CAN communication types
- **Multiple Control Modes**: Motion control, position, velocity, current, and torque control
- **Asynchronous Communication**: Background message handling with thread-safe status updates
- **Parameter Management**: Read/write motor parameters with automatic type handling
- **Error Handling**: Comprehensive exception system for robust applications
- **Cross-Platform**: Works with any python-can compatible CAN interface

## Quick Start

### Installation

```bash
pip install python-can
```

### Basic Usage

```python
import robstride
import time

# Connect to motor
motor = robstride.create_motor_from_can_interface(
    motor_id=1, 
    interface='socketcan', 
    channel='can0'
)

# Enable motor
motor.enable()

# Position control - motor acts like a spring
motor.set_motion_control(
    pos=1.0,      # Target 1 radian
    vel=0.0,      # No velocity target
    kp=50.0,      # Position gain
    kd=1.0,       # Damping
    torque=0.0    # No feedforward torque
)

# Monitor status
time.sleep(2)
status = motor.get_status()
print(f"Position: {status['position']:.3f} rad")

# Clean up
motor.disable()
motor.close()
```

## Control Modes

### Motion Control (Default)
The most flexible mode implementing:
```
torque_output = Kp*(pos_target - pos_actual) + Kd*(vel_target - vel_actual) + torque_feedforward
```

Examples:
```python
# Position control (spring to 1.0 rad)
motor.set_motion_control(pos=1.0, vel=0.0, kp=50.0, kd=1.0, torque=0.0)

# Velocity control (constant 2 rad/s)  
motor.set_motion_control(pos=0.0, vel=2.0, kp=0.0, kd=1.0, torque=0.0)

# Damping mode (resist motion)
motor.set_motion_control(pos=0.0, vel=0.0, kp=0.0, kd=2.0, torque=0.0)

# Torque control (constant 1 Nm)
motor.set_motion_control(pos=0.0, vel=0.0, kp=0.0, kd=0.0, torque=1.0)
```

### Other Control Modes

```python
# Current control mode
motor.set_run_mode(robstride.RUN_MODE_CURRENT)
motor.enable()
motor.set_current_reference(2.0)  # 2 Amps

# Velocity control mode
motor.set_run_mode(robstride.RUN_MODE_VELOCITY)
motor.set_current_limit(5.0)      # Max 5A
motor.enable()
motor.set_velocity_reference(3.0)  # 3 rad/s

# Position control mode (CSP)
motor.set_run_mode(robstride.RUN_MODE_POSITION_CSP)
motor.set_velocity_limit(10.0)     # Max 10 rad/s
motor.set_current_limit(3.0)       # Max 3A
motor.enable()
motor.set_position_reference(1.5)  # 1.5 rad
```

## CAN Interface Setup

The SDK works with any python-can compatible interface:

### SocketCAN (Linux)
```bash
sudo ip link set can0 type can bitrate 1000000
sudo ip link set up can0
```

```python
motor = robstride.create_motor_from_can_interface(1, 'socketcan', 'can0')
```

### PCAN (Windows/Linux)
```python
motor = robstride.create_motor_from_can_interface(1, 'pcan', 'PCAN_USBBUS1')
```

### Kvaser (Windows/Linux)
```python
motor = robstride.create_motor_from_can_interface(1, 'kvaser', 'kvaser://0')
```

## Examples

The `examples/` directory contains complete working examples:

- `01_enable_and_disable.py` - Basic motor connection and status reading
- `02_motion_control.py` - All motion control modes with detailed demos
- `03_read_write_params.py` - Parameter management and control mode switching

Run an example:
```bash
cd examples
python 01_enable_and_disable.py
```

## API Reference

### Motor Class

#### Basic Control
- `enable()` - Enable motor
- `disable(clear_errors=False)` - Disable motor
- `set_zero_position()` - Set current position as zero

#### Motion Control
- `set_motion_control(pos, vel, kp, kd, torque)` - Unified motion control
- `set_run_mode(mode)` - Change control mode
- `set_current_reference(current)` - Set current target
- `set_velocity_reference(velocity)` - Set velocity target  
- `set_position_reference(position)` - Set position target

#### Status and Diagnostics
- `get_status(timeout=None)` - Get current motor status
- `get_device_id(timeout=None)` - Get 64-bit device ID
- `read_parameter(param_index, timeout=None)` - Read parameter value

#### Configuration
- `save_configuration()` - Save parameters to flash
- `set_active_reporting(enable)` - Enable/disable status reports
- `set_motor_id(new_id)` - Change motor CAN ID

### Exception Handling

```python
try:
    motor.enable()
    motor.set_motion_control(1.0, 0.0, 50.0, 1.0, 0.0)
    status = motor.get_status()
except robstride.ConnectionError:
    print("CAN communication failed")
except robstride.TimeoutException:
    print("Motor did not respond")
except robstride.MotorFaultException as e:
    print(f"Motor fault: 0x{e.fault_code:08X}")
```

## Protocol Details

The SDK implements the complete Robstride CAN protocol:

- **Extended CAN frames** (29-bit ID) at 1Mbps
- **ID Structure**: `[28-24: comm_type] [23-8: host_id] [7-0: motor_id]`
- **All communication types** (0-25) from the official specification
- **Automatic data conversion** between physical units and protocol integers
- **Thread-safe message handling** with asynchronous status updates

## Advanced Usage

### Custom CAN Bus Management
```python
import can
import robstride

bus = can.interface.Bus(channel='can0', bustype='socketcan', bitrate=1000000)
motor1 = robstride.Motor(motor_id=1, can_bus=bus)
motor2 = robstride.Motor(motor_id=2, can_bus=bus)

# Use motors...

motor1.close()
motor2.close()
bus.shutdown()
```

### Status Callbacks
```python
def status_callback(status):
    print(f"Motor {status['motor_id']}: pos={status['position']:.3f}")

motor.set_status_callback(status_callback)
motor.set_active_reporting(True)  # Enable 10ms status reports
```

### Parameter Access
```python
# Read parameter
kp_value = motor.read_parameter(robstride.PARAM_LOC_KP)

# Write parameter  
motor.set_position_kp(30.0)

# Save to flash (persists after power cycle)
motor.save_configuration()
```

## Requirements

- Python 3.7+
- python-can >= 4.0.0
- Compatible CAN interface hardware

## License

MIT License - see LICENSE file for details.

## Support

For technical support and documentation, visit [robstride.com](https://robstride.com)

## Installation
To install the RobStride SDK, clone the repository and install the required dependencies:

```bash
git clone https://github.com/yourusername/robstride-sdk.git
cd robstride-sdk
pip install -r requirements.txt
```

## Usage
To use the RobStride SDK, import the necessary modules in your Python script:

```python
from robstride.motor import Motor
from robstride.protocol import Protocol
```

### Example
Here is a simple example of how to move the motor:

```python
from robstride.motor import Motor

motor = Motor()
motor.move_forward(speed=100)
```

## Examples
The `examples` directory contains scripts demonstrating how to use the SDK:
- `move_motor.py`: A script to control the motor's movement.
- `read_status.py`: A script to read the motor's status.

## Testing
To run the tests, navigate to the `tests` directory and execute:

```bash
python -m unittest discover
```

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.