"""
Example 3: Parameter Reading and Writing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This example demonstrates how to read and write motor parameters using the SDK.
Parameters control various aspects of motor behavior like control gains,
limits, and operational modes.

Important: Some parameters require saving to flash memory to persist after power cycling.
"""

import time
import robstride

# Configuration
MOTOR_ID = 1
CAN_INTERFACE = 'socketcan'
CAN_CHANNEL = 'can0'


def read_motor_info(motor):
    """Read and display basic motor information."""
    print("\n=== Motor Information ===")
    
    try:
        # Get device ID
        device_id = motor.get_device_id(timeout=2.0)
        device_id_hex = ' '.join(f'{b:02X}' for b in device_id)
        print(f"Device ID: {device_id_hex}")
        
    except robstride.TimeoutException:
        print("❌ Could not read device ID")
    
    # Read some key parameters
    params_to_read = [
        (robstride.PARAM_RUN_MODE, "Run Mode"),
        (robstride.PARAM_LOC_KP, "Position Kp"),
        (robstride.PARAM_SPD_KP, "Velocity Kp"), 
        (robstride.PARAM_SPD_KI, "Velocity Ki"),
        (robstride.PARAM_LIMIT_CUR, "Current Limit"),
        (robstride.PARAM_LIMIT_SPD, "Speed Limit"),
        (robstride.PARAM_VBUS, "Bus Voltage"),
        (robstride.PARAM_MECH_POS, "Mechanical Position"),
        (robstride.PARAM_MECH_VEL, "Mechanical Velocity"),
    ]
    
    print("\nCurrent Parameter Values:")
    for param_index, param_name in params_to_read:
        try:
            value = motor.read_parameter(param_index, timeout=1.0)
            if param_index == robstride.PARAM_RUN_MODE:
                mode_names = {0: "Motion Control", 1: "Position PP", 2: "Velocity", 3: "Current", 5: "Position CSP"}
                mode_name = mode_names.get(int(value), "Unknown")
                print(f"  {param_name}: {int(value)} ({mode_name})")
            else:
                print(f"  {param_name}: {value:.3f}")
        except robstride.TimeoutException:
            print(f"  {param_name}: (timeout)")
        except Exception as e:
            print(f"  {param_name}: (error: {e})")


def demo_mode_switching(motor):
    """Demonstrate switching between different control modes."""
    print("\n=== Control Mode Switching Demo ===")
    
    # Note: Motor must be disabled to change modes
    print("Disabling motor to change modes...")
    motor.disable()
    time.sleep(0.5)
    
    # Demo different modes
    modes_to_test = [
        (robstride.RUN_MODE_CURRENT, "Current Mode"),
        (robstride.RUN_MODE_VELOCITY, "Velocity Mode"),
        (robstride.RUN_MODE_POSITION_CSP, "Position CSP Mode"),
        (robstride.RUN_MODE_MOTION_CONTROL, "Motion Control Mode"),
    ]
    
    for mode_code, mode_name in modes_to_test:
        print(f"\nSetting motor to {mode_name}...")
        
        try:
            # Set the run mode
            motor.set_run_mode(mode_code)
            time.sleep(0.2)
            
            # Verify the mode was set
            current_mode = motor.read_parameter(robstride.PARAM_RUN_MODE, timeout=1.0)
            if int(current_mode) == mode_code:
                print(f"✓ Successfully set to {mode_name}")
            else:
                print(f"⚠️  Mode readback mismatch: expected {mode_code}, got {int(current_mode)}")
                
        except Exception as e:
            print(f"❌ Failed to set {mode_name}: {e}")
    
    # Re-enable motor in motion control mode
    print("\nRe-enabling motor in Motion Control mode...")
    motor.enable()
    time.sleep(0.5)


def demo_current_mode(motor):
    """Demonstrate current control mode."""
    print("\n=== Current Control Mode Demo ===")
    
    # Switch to current mode
    motor.disable()
    time.sleep(0.2)
    motor.set_run_mode(robstride.RUN_MODE_CURRENT)
    time.sleep(0.2)
    motor.enable()
    time.sleep(0.2)
    
    print("Motor is now in current control mode")
    print("Setting current reference to 1.0 A for 3 seconds...")
    
    # Set current reference
    motor.set_current_reference(1.0)  # 1 Amp
    
    # Monitor for a few seconds
    for i in range(3):
        time.sleep(1)
        try:
            status = motor.get_status(timeout=0.5)
            print(f"  Velocity: {status['velocity']:.2f} rad/s, Torque: {status['torque']:.2f} Nm")
        except robstride.TimeoutException:
            print("  (no status)")
    
    # Stop current
    motor.set_current_reference(0.0)
    print("Current reference set to 0")


def demo_velocity_mode(motor):
    """Demonstrate velocity control mode."""
    print("\n=== Velocity Control Mode Demo ===")
    
    # Switch to velocity mode  
    motor.disable()
    time.sleep(0.2)
    motor.set_run_mode(robstride.RUN_MODE_VELOCITY)
    time.sleep(0.2)
    
    # Set limits before enabling
    motor.set_current_limit(5.0)  # Max 5A
    motor.set_velocity_reference(2.0)  # 2 rad/s target
    
    motor.enable()
    time.sleep(0.2)
    
    print("Motor is now in velocity control mode")
    print("Target velocity: 2.0 rad/s for 4 seconds...")
    
    # Monitor velocity
    for i in range(4):
        time.sleep(1)
        try:
            status = motor.get_status(timeout=0.5)
            print(f"  Target: 2.0, Actual: {status['velocity']:.2f} rad/s")
        except robstride.TimeoutException:
            print("  (no status)")
    
    # Change velocity
    print("Changing target velocity to -1.0 rad/s...")
    motor.set_velocity_reference(-1.0)
    
    for i in range(3):
        time.sleep(1)
        try:
            status = motor.get_status(timeout=0.5)
            print(f"  Target: -1.0, Actual: {status['velocity']:.2f} rad/s")
        except robstride.TimeoutException:
            print("  (no status)")
    
    # Stop
    motor.set_velocity_reference(0.0)
    print("Velocity reference set to 0")


def demo_position_mode(motor):
    """Demonstrate position control mode (CSP)."""
    print("\n=== Position Control Mode (CSP) Demo ===")
    
    # Switch to position CSP mode
    motor.disable()
    time.sleep(0.2)
    motor.set_run_mode(robstride.RUN_MODE_POSITION_CSP)
    time.sleep(0.2)
    
    # Set limits
    motor.set_velocity_limit(5.0)  # Max 5 rad/s
    motor.set_current_limit(3.0)   # Max 3A
    
    motor.enable()
    time.sleep(0.2)
    
    print("Motor is now in position control mode (CSP)")
    
    # Move to different positions
    positions = [1.0, -1.0, 0.5, 0.0]
    
    for target_pos in positions:
        print(f"Moving to position {target_pos:.1f} rad...")
        motor.set_position_reference(target_pos)
        
        # Wait and monitor
        for _ in range(20):  # 2 seconds
            time.sleep(0.1)
            try:
                status = motor.get_status(timeout=0.1)
                error = abs(status['position'] - target_pos)
                if _ % 10 == 0:  # Print every second
                    print(f"  Position: {status['position']:.3f} rad (error: {error:.3f})")
                if error < 0.05:  # Close enough
                    break
            except robstride.TimeoutException:
                pass


def demo_parameter_tuning(motor):
    """Demonstrate reading and modifying control parameters."""
    print("\n=== Parameter Tuning Demo ===")
    
    # Read current position gains
    try:
        current_kp = motor.read_parameter(robstride.PARAM_LOC_KP)
        current_kd = motor.read_parameter(robstride.PARAM_SPD_KI)  # Ki for velocity loop
        
        print(f"Current Position Kp: {current_kp:.1f}")
        print(f"Current Velocity Ki: {current_kd:.3f}")
        
        # Modify parameters
        print("\nModifying parameters...")
        new_kp = 30.0
        new_ki = 0.015
        
        # Write new parameters (they take effect immediately but are not saved to flash)
        motor.set_position_kp(new_kp)
        motor.set_velocity_ki(new_ki)
        
        time.sleep(0.1)
        
        # Read back to verify
        readback_kp = motor.read_parameter(robstride.PARAM_LOC_KP)
        readback_ki = motor.read_parameter(robstride.PARAM_SPD_KI)
        
        print(f"New Position Kp: {readback_kp:.1f}")
        print(f"New Velocity Ki: {readback_ki:.3f}")
        
        # Note: To save these parameters permanently, you would call:
        # motor.save_configuration()
        # But we won't do that in this example
        
        print("\nNote: Parameters modified but not saved to flash memory")
        print("They will revert to defaults on power cycle")
        
        # Restore original parameters
        print("\nRestoring original parameters...")
        motor.set_position_kp(current_kp)
        motor.set_velocity_ki(current_kd)
        
    except Exception as e:
        print(f"❌ Parameter tuning demo failed: {e}")


def main():
    """Main function running all parameter demos."""
    
    print("=== Robstride Parameter Control Examples ===")
    
    try:
        # Connect to motor
        motor = robstride.create_motor_from_can_interface(
            motor_id=MOTOR_ID,
            interface=CAN_INTERFACE,
            channel=CAN_CHANNEL
        )
        
        print(f"✓ Connected to motor {MOTOR_ID}")
        
        # Enable motor initially
        motor.enable()
        time.sleep(0.5)
        
        # Run all demos
        read_motor_info(motor)
        demo_mode_switching(motor)
        demo_current_mode(motor)
        demo_velocity_mode(motor)
        demo_position_mode(motor)
        demo_parameter_tuning(motor)
        
        print("\n=== All parameter demos completed! ===")
        
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
