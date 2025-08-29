"""
Example 1: Basic Motor Enable and Disable
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This example demonstrates the most basic operations with a Robstride motor:
- Connecting to the motor
- Enabling the motor
- Getting motor status
- Disabling the motor
- Proper cleanup

This is the starting point for all motor operations.
"""

import time
import robstride

# Configuration - adjust these for your setup
MOTOR_ID = 1
CAN_INTERFACE = 'socketcan'  # Options: 'socketcan', 'pcan', 'kvaser', etc.
CAN_CHANNEL = 'can0'         # Linux: 'can0', Windows PCAN: 'PCAN_USBBUS1', etc.


def main():
    """Main function demonstrating basic motor operations."""
    
    print("=== Robstride Motor Enable/Disable Example ===")
    print(f"Connecting to motor ID {MOTOR_ID} on {CAN_INTERFACE}:{CAN_CHANNEL}")
    
    try:
        # Create motor instance - this also creates the CAN bus
        motor = robstride.create_motor_from_can_interface(
            motor_id=MOTOR_ID,
            interface=CAN_INTERFACE,
            channel=CAN_CHANNEL
        )
        
        print("✓ Connected to motor successfully")
        
        # Enable the motor
        print("\nEnabling motor...")
        motor.enable()
        print("✓ Motor enabled")
        
        # Wait a moment for the motor to be ready
        time.sleep(0.5)
        
        # Get and display motor status
        print("\nReading motor status...")
        try:
            status = motor.get_status(timeout=2.0)
            print("✓ Motor status received:")
            print(f"  Position: {status['position']:.3f} rad")
            print(f"  Velocity: {status['velocity']:.3f} rad/s")
            print(f"  Torque: {status['torque']:.3f} Nm")
            print(f"  Temperature: {status['temperature']:.1f} °C")
            print(f"  Mode: {status['mode']} (0=Reset, 1=Cali, 2=Motor)")
            print(f"  Error code: 0x{status['error_code']:02X}")
            
            if status['error_code'] != 0:
                print("⚠️  Motor has error flags set!")
        
        except robstride.TimeoutException:
            print("⚠️  No status received from motor - it may not be connected properly")
        
        # Keep motor enabled for a few seconds
        print(f"\nMotor will stay enabled for 3 seconds...")
        print("(You can try gently moving the motor by hand)")
        time.sleep(3)
        
        # Disable the motor
        print("\nDisabling motor...")
        motor.disable()
        print("✓ Motor disabled")
        
        print("\n=== Example completed successfully! ===")
        
    except robstride.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        print("\nTroubleshooting tips:")
        print("- Check CAN interface is available")
        print("- Verify motor is powered on")
        print("- Check CAN bus connections")
        print("- Ensure correct CAN channel name")
        
    except robstride.RobstrideException as e:
        print(f"❌ Motor error: {e}")
        
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        
    finally:
        # Always clean up, even if there was an error
        try:
            if 'motor' in locals():
                print("\nCleaning up...")
                motor.close()
                print("✓ Resources cleaned up")
        except:
            pass


if __name__ == "__main__":
    main()
