#!/usr/bin/env python3
"""
MIT protocol example for RobStride Motor SDK
"""

import time
from robstride import RobStrideMotor, ProtocolType

def main():
    # Create motor instance with MIT protocol
    motor = RobStrideMotor(
        can_id=1,                      # Motor CAN ID
        interface='can0',              # CAN interface
        protocol=ProtocolType.MIT,     # Use MIT protocol
        timeout=1.0
    )
    
    try:
        # Connect to motor
        print("Connecting to motor (MIT protocol)...")
        motor.connect()
        
        # Enable motor
        print("Enabling motor...")
        motor.enable()
        
        # Set zero position
        print("Setting zero position...")
        motor.set_zero_position()
        time.sleep(0.5)
        
        # MIT motion control
        print("MIT motion control example...")
        motor.set_motion_control(
            position=1.0,    # 1 radian
            velocity=0.0,    # Hold position
            kp=50.0,         # Position gain
            kd=2.0,          # Velocity gain  
            torque=0.0       # No feed-forward torque
        )
        
        # Monitor status
        print("Monitoring...")
        for i in range(50):  # 5 seconds
            print(f"Pos: {motor.position:.3f} rad, "
                  f"Vel: {motor.velocity:.3f} rad/s, "
                  f"Torque: {motor.torque:.3f} Nm, "
                  f"Temp: {motor.temperature:.1f}°C")
            time.sleep(0.1)
        
        # Position control with MIT protocol
        print("MIT position control...")
        motor.set_position_control(position=2.0, speed_limit=5.0)
        time.sleep(3.0)
        
        # Velocity control with MIT protocol
        print("MIT velocity control...")
        motor.set_velocity_control(velocity=2.0, current_limit=8.0)
        time.sleep(2.0)
        
        # Stop
        motor.set_velocity_control(velocity=0.0, current_limit=8.0)
        time.sleep(1.0)
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        print("Disabling motor...")
        motor.disable()
        motor.disconnect()
        print("Done!")

if __name__ == '__main__':
    main()
