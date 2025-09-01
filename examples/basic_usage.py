#!/usr/bin/env python3
"""
Basic usage example for RobStride Motor SDK
"""

import time
from robstride import RobStrideMotor, ProtocolType

def main():
    # Create motor instance
    motor = RobStrideMotor(
        can_id=1,                          # Motor CAN ID
        interface='can0',                  # CAN interface  
        master_id=0xFD,                   # Master controller ID
        protocol=ProtocolType.PRIVATE,    # Use private protocol
        timeout=1.0                       # Response timeout
    )
    
    try:
        # Connect to motor
        print("Connecting to motor...")
        motor.connect()
        
        # Get device information
        unique_id = motor.get_device_id()
        if unique_id:
            print(f"Device ID: {unique_id.hex().upper()}")
        
        # Enable motor
        print("Enabling motor...")
        motor.enable()
        
        # Set zero position
        print("Setting zero position...")
        motor.set_zero_position()
        time.sleep(0.5)
        
        # Motion control example
        print("Motion control example...")
        motor.set_motion_control(
            position=1.0,    # 1 radian
            velocity=0.0,    # Hold position
            kp=50.0,         # Position gain
            kd=1.0,          # Velocity gain
            torque=0.0       # No feed-forward torque
        )
        
        # Monitor for a few seconds
        print("Monitoring motor status...")
        for i in range(30):  # 3 seconds at 10Hz
            print(f"Pos: {motor.position:.3f} rad, "
                  f"Vel: {motor.velocity:.3f} rad/s, "
                  f"Torque: {motor.torque:.3f} Nm, "
                  f"Temp: {motor.temperature:.1f}°C")
            time.sleep(0.1)
        
        # Position control example
        print("Position control example...")
        motor.set_position_control(position=2.0, speed_limit=5.0)
        time.sleep(2.0)
        
        # Velocity control example  
        print("Velocity control example...")
        motor.set_velocity_control(velocity=3.0, current_limit=10.0)
        time.sleep(2.0)
        
        # Stop motor
        motor.set_velocity_control(velocity=0.0, current_limit=10.0)
        time.sleep(1.0)
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        # Always disable and disconnect
        print("Disabling motor...")
        motor.disable()
        motor.disconnect()
        print("Done!")

if __name__ == '__main__':
    main()
