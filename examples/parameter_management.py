#!/usr/bin/env python3
"""
Parameter management example for RobStride Motor SDK
"""

import time
from robstride import RobStrideMotor, ProtocolType
from robstride.protocol import ParameterAddress, ControlMode

def main():
    # Create motor instance (private protocol required for parameter access)
    motor = RobStrideMotor(
        can_id=1,
        interface='can0',
        protocol=ProtocolType.PRIVATE,
        timeout=2.0  # Longer timeout for parameter operations
    )
    
    try:
        print("Connecting to motor...")
        motor.connect()
        
        # Get device information
        unique_id = motor.get_device_id()
        if unique_id:
            print(f"Device ID: {unique_id.hex().upper()}")
        
        # Read current parameters
        print("\nReading current parameters...")
        try:
            run_mode = motor.get_parameter(ParameterAddress.RUN_MODE)
            print(f"Current run mode: {run_mode} ({['Motion', 'Position', 'Velocity', 'Current'][run_mode] if run_mode < 4 else 'Unknown'})")
        except Exception as e:
            print(f"Failed to read run mode: {e}")
        
        try:
            max_velocity = motor.get_parameter(ParameterAddress.MAX_VELOCITY)
            print(f"Max velocity: {max_velocity:.2f} rad/s")
        except Exception as e:
            print(f"Failed to read max velocity: {e}")
        
        try:
            limit_current = motor.get_parameter(ParameterAddress.LIMIT_CURRENT)
            print(f"Current limit: {limit_current:.2f} A")
        except Exception as e:
            print(f"Failed to read current limit: {e}")
        
        # Enable motor
        print("\nEnabling motor...")
        motor.enable()
        
        # Demonstrate different control modes
        print("\n--- Position Control Mode ---")
        motor.set_parameter(ParameterAddress.RUN_MODE, ControlMode.POSITION)
        time.sleep(0.1)
        motor.set_parameter(ParameterAddress.TARGET_POSITION, 1.0)
        motor.set_parameter(ParameterAddress.LIMIT_VELOCITY, 5.0)
        time.sleep(3.0)
        
        print("Position control status:")
        print(f"  Position: {motor.position:.3f} rad")
        print(f"  Velocity: {motor.velocity:.3f} rad/s")
        
        print("\n--- Velocity Control Mode ---")
        motor.set_parameter(ParameterAddress.RUN_MODE, ControlMode.VELOCITY)
        time.sleep(0.1)
        motor.set_parameter(ParameterAddress.TARGET_VELOCITY, 2.0)
        motor.set_parameter(ParameterAddress.LIMIT_CURRENT, 8.0)
        time.sleep(3.0)
        
        print("Velocity control status:")
        print(f"  Position: {motor.position:.3f} rad")
        print(f"  Velocity: {motor.velocity:.3f} rad/s")
        
        # Stop motor
        motor.set_parameter(ParameterAddress.TARGET_VELOCITY, 0.0)
        time.sleep(1.0)
        
        print("\n--- Current Control Mode ---")
        motor.set_parameter(ParameterAddress.RUN_MODE, ControlMode.CURRENT)
        time.sleep(0.1)
        motor.set_parameter(ParameterAddress.TARGET_CURRENT, 1.0)
        time.sleep(2.0)
        
        print("Current control status:")
        print(f"  Position: {motor.position:.3f} rad")
        print(f"  Velocity: {motor.velocity:.3f} rad/s")
        print(f"  Torque: {motor.torque:.3f} Nm")
        
        # Stop current
        motor.set_parameter(ParameterAddress.TARGET_CURRENT, 0.0)
        time.sleep(1.0)
        
        # Modify motor parameters
        print("\n--- Parameter Modification ---")
        
        # Set maximum velocity limit
        print("Setting max velocity to 10 rad/s...")
        motor.set_parameter(ParameterAddress.MAX_VELOCITY, 10.0)
        time.sleep(0.1)
        
        # Verify the change
        new_max_vel = motor.get_parameter(ParameterAddress.MAX_VELOCITY)
        print(f"New max velocity: {new_max_vel:.2f} rad/s")
        
        # Set current limit
        print("Setting current limit to 15 A...")
        motor.set_parameter(ParameterAddress.LIMIT_CURRENT, 15.0)
        time.sleep(0.1)
        
        new_current_limit = motor.get_parameter(ParameterAddress.LIMIT_CURRENT)
        print(f"New current limit: {new_current_limit:.2f} A")
        
        # Save parameters to motor's non-volatile memory
        print("\nSaving parameters to motor memory...")
        motor.set_parameter(ParameterAddress.RUN_MODE, ControlMode.MOTION_CONTROL)  # Reset to motion control
        time.sleep(0.5)
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        print("\nDisabling motor...")
        motor.disable()
        motor.disconnect()
        print("Done!")

if __name__ == '__main__':
    main()
