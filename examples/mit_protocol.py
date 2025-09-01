#!/usr/bin/env python3
"""
MIT Protocol Example for RobStride Motor SDK

This example demonstrates how to use the RobStride motor with MIT protocol.
When initializing with MIT protocol, the motor will automatically be set to MIT mode.
"""

import time
import logging
from robstride import RobStrideMotor, ProtocolType

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """MIT protocol usage example"""
    
    # Initialize motor with MIT protocol (default)
    motor = RobStrideMotor(
        can_id=1,
        interface='can0',
        protocol=ProtocolType.MIT  # This will automatically set the motor to MIT mode
    )
    
    try:
        # Connect to motor (this will automatically set MIT protocol)
        logger.info("Connecting to motor with MIT protocol...")
        motor.connect()
        
        # Enable motor
        logger.info("Enabling motor...")
        motor.enable()
        time.sleep(0.1)
        
        # Set zero position
        logger.info("Setting zero position...")
        motor.set_zero_position()
        time.sleep(0.1)
        
        # MIT protocol motion control examples
        logger.info("MIT Motion Control Examples:")
        
        # Example 1: Position control with MIT protocol
        logger.info("1. Position control (target: 1.0 rad)")
        motor.set_position_control(position=1.0, speed_limit=5.0)
        time.sleep(2.0)
        
        # Example 2: Velocity control with MIT protocol  
        logger.info("2. Velocity control (target: 2.0 rad/s)")
        motor.set_velocity_control(velocity=2.0, current_limit=10.0)
        time.sleep(2.0)
        
        # Example 3: Advanced motion control with all parameters
        logger.info("3. Advanced motion control")
        motor.set_motion_control(
            position=0.5,    # Target position (rad)
            velocity=1.0,    # Target velocity (rad/s)
            kp=100.0,        # Position gain
            kd=2.0,          # Velocity gain
            torque=0.0       # Feed-forward torque (Nm)
        )
        time.sleep(2.0)
        
        # Return to zero
        logger.info("4. Returning to zero position")
        motor.set_motion_control(position=0.0, velocity=0.0, kp=50.0, kd=1.0, torque=0.0)
        time.sleep(2.0)
        
        # Print motor status
        logger.info(f"Motor Status:")
        logger.info(f"  Position: {motor.position:.3f} rad")
        logger.info(f"  Velocity: {motor.velocity:.3f} rad/s")
        logger.info(f"  Torque: {motor.torque:.3f} Nm")
        logger.info(f"  Temperature: {motor.temperature:.1f} °C")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        
    finally:
        # Always disable and disconnect
        logger.info("Disabling motor...")
        motor.disable()
        motor.disconnect()
        logger.info("Example completed.")

if __name__ == "__main__":
    main()
