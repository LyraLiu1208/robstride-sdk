"""
Example 2: Motion Control Demonstrations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This example demonstrates the powerful motion control capabilities of Robstride motors.
The motion control mode implements: 
    torque_output = Kp*(pos_target - pos_actual) + Kd*(vel_target - vel_actual) + torque_feedforward

This allows for:
- Position control (spring behavior)
- Velocity control 
- Damping control
- Direct torque control
- Any combination of the above
"""

import time
import robstride

# Configuration
MOTOR_ID = 1
CAN_INTERFACE = 'socketcan'
CAN_CHANNEL = 'can0'


def demo_position_control(motor):
    """Demonstrate position control - motor acts like a spring."""
    print("\n=== Position Control Demo ===")
    print("Motor will act like a spring, returning to position 0")
    print("Try gently moving the motor by hand - it should resist and return to center")
    
    # Position control: high Kp, some damping
    motor.set_motion_control(
        pos=0.0,     # Target position: 0 radians
        vel=0.0,     # Target velocity: 0 (we want to stay at position)
        kp=50.0,     # High position gain - strong spring
        kd=1.0,      # Some damping to prevent oscillation
        torque=0.0   # No feedforward torque
    )
    
    print("Position control active for 5 seconds...")
    for i in range(5):
        time.sleep(1)
        try:
            status = motor.get_status(timeout=0.5)
            print(f"  Position: {status['position']:.3f} rad, Torque: {status['torque']:.2f} Nm")
        except robstride.TimeoutException:
            print("  (No status received)")


def demo_velocity_control(motor):
    """Demonstrate velocity control - motor rotates at constant speed."""
    print("\n=== Velocity Control Demo ===")
    print("Motor will rotate at 1 rad/s")
    print("You can try to slow it down by hand - it will push back")
    
    # Velocity control: zero Kp, high Kd
    motor.set_motion_control(
        pos=0.0,     # Position target doesn't matter
        vel=1.0,     # Target velocity: 1 rad/s
        kp=0.0,      # No position control
        kd=2.0,      # High velocity gain
        torque=0.0   # No feedforward torque
    )
    
    print("Velocity control active for 5 seconds...")
    for i in range(5):
        time.sleep(1)
        try:
            status = motor.get_status(timeout=0.5)
            print(f"  Velocity: {status['velocity']:.3f} rad/s, Torque: {status['torque']:.2f} Nm")
        except robstride.TimeoutException:
            print("  (No status received)")


def demo_damping_control(motor):
    """Demonstrate damping control - motor resists motion."""
    print("\n=== Damping Control Demo ===")
    print("Motor will resist any movement")
    print("Try moving the motor by hand - it should feel heavy/viscous")
    
    # Damping control: zero Kp and target velocity, high Kd
    motor.set_motion_control(
        pos=0.0,     # Position target doesn't matter
        vel=0.0,     # Target velocity: 0 (resist any motion)
        kp=0.0,      # No position control
        kd=3.0,      # High damping gain
        torque=0.0   # No feedforward torque
    )
    
    print("Damping control active for 5 seconds...")
    print("Note: Motor will generate power when moved - ensure your power supply can handle regeneration")
    for i in range(5):
        time.sleep(1)
        try:
            status = motor.get_status(timeout=0.5)
            print(f"  Velocity: {status['velocity']:.3f} rad/s, Torque: {status['torque']:.2f} Nm")
        except robstride.TimeoutException:
            print("  (No status received)")


def demo_torque_control(motor):
    """Demonstrate direct torque control."""
    print("\n=== Torque Control Demo ===")
    print("Motor will output a constant 0.5 Nm torque")
    print("The motor will accelerate unless you hold it")
    
    # Pure torque control
    motor.set_motion_control(
        pos=0.0,     # Position doesn't matter
        vel=0.0,     # Velocity doesn't matter  
        kp=0.0,      # No position control
        kd=0.0,      # No velocity control
        torque=0.5   # Constant 0.5 Nm output
    )
    
    print("Torque control active for 3 seconds...")
    for i in range(3):
        time.sleep(1)
        try:
            status = motor.get_status(timeout=0.5)
            print(f"  Velocity: {status['velocity']:.3f} rad/s, Torque: {status['torque']:.2f} Nm")
        except robstride.TimeoutException:
            print("  (No status received)")


def demo_trajectory_following(motor):
    """Demonstrate smooth trajectory following."""
    print("\n=== Trajectory Following Demo ===")
    print("Motor will smoothly move between different positions")
    
    # Trajectory: move to different positions with smooth motion
    positions = [0.0, 1.0, -1.0, 0.5, -0.5, 0.0]
    
    for target_pos in positions:
        print(f"Moving to position {target_pos:.1f} rad...")
        
        # Use moderate gains for smooth motion
        motor.set_motion_control(
            pos=target_pos,
            vel=0.0,     # Let the controller determine velocity
            kp=20.0,     # Moderate position gain
            kd=2.0,      # Good damping
            torque=0.0   # No feedforward
        )
        
        # Wait and monitor progress
        for _ in range(20):  # 2 seconds at 0.1s intervals
            time.sleep(0.1)
            try:
                status = motor.get_status(timeout=0.1)
                current_pos = status['position']
                error = abs(current_pos - target_pos)
                
                # Print progress occasionally
                if _ % 5 == 0:
                    print(f"  Position: {current_pos:.3f} rad (error: {error:.3f})")
                
                # Move to next target if we're close enough
                if error < 0.05:  # Within 0.05 radians
                    break
                    
            except robstride.TimeoutException:
                pass


def main():
    """Main function running all motion control demos."""
    
    print("=== Robstride Motion Control Examples ===")
    
    try:
        # Connect to motor
        motor = robstride.create_motor_from_can_interface(
            motor_id=MOTOR_ID,
            interface=CAN_INTERFACE,
            channel=CAN_CHANNEL
        )
        
        print(f"✓ Connected to motor {MOTOR_ID}")
        
        # Enable motor
        print("Enabling motor...")
        motor.enable()
        time.sleep(0.5)
        print("✓ Motor enabled")
        
        # Run demos
        demo_position_control(motor)
        demo_velocity_control(motor)
        demo_damping_control(motor)
        demo_torque_control(motor)
        demo_trajectory_following(motor)
        
        # Stop motion
        print("\nStopping all motion...")
        motor.set_motion_control(0.0, 0.0, 0.0, 1.0, 0.0)  # Light damping only
        time.sleep(1)
        
        print("\n=== All demos completed! ===")
        
    except robstride.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        
    except robstride.RobstrideException as e:
        print(f"❌ Motor error: {e}")
        
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
        
    finally:
        try:
            if 'motor' in locals():
                print("\nDisabling motor and cleaning up...")
                motor.disable()
                motor.close()
                print("✓ Cleanup complete")
        except Exception:
            pass


if __name__ == "__main__":
    main()
