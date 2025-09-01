#!/usr/bin/env python3
"""
Multi-motor control example for RobStride Motor SDK
"""

import time
import threading
from robstride import RobStrideMotor, ProtocolType

def control_motor(motor_id: int, interface: str, positions: list):
    """Control a single motor through a sequence of positions"""
    motor = RobStrideMotor(
        can_id=motor_id,
        interface=interface,
        protocol=ProtocolType.PRIVATE
    )
    
    try:
        print(f"Motor {motor_id}: Connecting...")
        motor.connect()
        motor.enable()
        
        for i, pos in enumerate(positions):
            print(f"Motor {motor_id}: Moving to position {pos:.2f} rad (step {i+1}/{len(positions)})")
            motor.set_position_control(position=pos, speed_limit=3.0)
            time.sleep(2.0)  # Wait for movement
            
            # Print current status
            print(f"Motor {motor_id}: Current pos={motor.position:.3f}, vel={motor.velocity:.3f}")
        
        print(f"Motor {motor_id}: Sequence complete")
        
    except Exception as e:
        print(f"Motor {motor_id}: Error - {e}")
        
    finally:
        motor.disable()
        motor.disconnect()
        print(f"Motor {motor_id}: Disconnected")

def main():
    # Define motor configurations
    motors = [
        {'id': 1, 'interface': 'can0', 'positions': [0.0, 1.0, -1.0, 0.0]},
        {'id': 2, 'interface': 'can0', 'positions': [0.0, -1.0, 1.0, 0.0]},
        {'id': 3, 'interface': 'can0', 'positions': [0.0, 0.5, -0.5, 0.0]},
    ]
    
    print("Starting multi-motor control example...")
    print(f"Controlling {len(motors)} motors simultaneously")
    
    # Create and start threads for each motor
    threads = []
    for motor_config in motors:
        thread = threading.Thread(
            target=control_motor,
            args=(motor_config['id'], motor_config['interface'], motor_config['positions'])
        )
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    print("All motors completed their sequences!")

if __name__ == '__main__':
    main()
