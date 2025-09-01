#!/usr/bin/env python3
"""
RobStride Motor CLI Tool

Command line interface for controlling RobStride motors.
"""

import argparse
import logging
import time
import sys
from robstride import RobStrideMotor, ProtocolType

def setup_logging(verbose: bool):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def create_motor(args) -> RobStrideMotor:
    """Create motor instance from command line arguments"""
    protocol = ProtocolType.MIT if args.mit else ProtocolType.PRIVATE
    
    return RobStrideMotor(
        can_id=args.motor_id,
        interface=args.interface,
        master_id=args.master_id,
        protocol=protocol,
        timeout=args.timeout
    )

def cmd_info(args):
    """Get motor information"""
    with create_motor(args) as motor:
        print(f"Motor ID: {motor.can_id}")
        print(f"Interface: {motor.can_interface.interface_name}")
        print(f"Protocol: {motor.protocol.value}")
        print(f"Master ID: 0x{motor.master_id:02X}")
        
        if motor.protocol == ProtocolType.PRIVATE:
            unique_id = motor.get_device_id()
            if unique_id:
                print(f"Unique ID: {unique_id.hex().upper()}")
            else:
                print("Unique ID: Not available")

def cmd_enable(args):
    """Enable motor"""
    with create_motor(args) as motor:
        motor.enable()
        print(f"Motor {motor.can_id} enabled")

def cmd_disable(args):
    """Disable motor"""
    with create_motor(args) as motor:
        motor.disable(clear_error=args.clear_error)
        print(f"Motor {motor.can_id} disabled")

def cmd_zero(args):
    """Set zero position"""
    with create_motor(args) as motor:
        motor.enable()
        motor.set_zero_position()
        print(f"Zero position set for motor {motor.can_id}")

def cmd_status(args):
    """Get motor status"""
    with create_motor(args) as motor:
        motor.enable()
        
        # Wait a bit for status update
        time.sleep(0.1)
        
        print(f"Motor {motor.can_id} Status:")
        print(f"  Position: {motor.position:.3f} rad ({motor.position*180/3.14159:.1f}°)")
        print(f"  Velocity: {motor.velocity:.3f} rad/s")
        print(f"  Torque: {motor.torque:.3f} Nm")
        print(f"  Temperature: {motor.temperature:.1f}°C")
        print(f"  Error Code: 0x{motor.error_code:02X}")
        print(f"  Enabled: {motor.is_enabled}")

def cmd_motion(args):
    """Motion control command"""
    with create_motor(args) as motor:
        motor.enable()
        
        motor.set_motion_control(
            position=args.position,
            velocity=args.velocity,
            kp=args.kp,
            kd=args.kd,
            torque=args.torque
        )
        
        print(f"Motion control sent to motor {motor.can_id}")
        print(f"  Position: {args.position:.3f} rad")
        print(f"  Velocity: {args.velocity:.3f} rad/s")
        print(f"  Kp: {args.kp:.1f}")
        print(f"  Kd: {args.kd:.3f}")
        print(f"  Torque: {args.torque:.3f} Nm")

def cmd_position(args):
    """Position control command"""
    with create_motor(args) as motor:
        motor.enable()
        
        motor.set_position_control(
            position=args.position,
            speed_limit=args.speed_limit
        )
        
        print(f"Position control sent to motor {motor.can_id}")
        print(f"  Target: {args.position:.3f} rad ({args.position*180/3.14159:.1f}°)")
        print(f"  Speed limit: {args.speed_limit:.3f} rad/s")

def cmd_velocity(args):
    """Velocity control command"""
    with create_motor(args) as motor:
        motor.enable()
        
        motor.set_velocity_control(
            velocity=args.velocity,
            current_limit=args.current_limit
        )
        
        print(f"Velocity control sent to motor {motor.can_id}")
        print(f"  Target: {args.velocity:.3f} rad/s")
        print(f"  Current limit: {args.current_limit:.1f} A")

def cmd_current(args):
    """Current control command"""
    with create_motor(args) as motor:
        if motor.protocol == ProtocolType.MIT:
            print("Error: Current control not supported in MIT mode")
            return
        
        motor.enable()
        
        motor.set_current_control(current=args.current)
        
        print(f"Current control sent to motor {motor.can_id}")
        print(f"  Target: {args.current:.3f} A")

def cmd_monitor(args):
    """Monitor motor status continuously"""
    with create_motor(args) as motor:
        motor.enable()
        
        print(f"Monitoring motor {motor.can_id} (Press Ctrl+C to stop)")
        print("Time\t\tPos(rad)\tVel(rad/s)\tTorque(Nm)\tTemp(°C)")
        print("-" * 70)
        
        try:
            while True:
                print(f"{time.time():.1f}\t\t{motor.position:.3f}\t\t{motor.velocity:.3f}\t\t{motor.torque:.3f}\t\t{motor.temperature:.1f}")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped")

def main():
    parser = argparse.ArgumentParser(description='RobStride Motor CLI Tool')
    
    # Global arguments
    parser.add_argument('--interface', '-i', default='can0', 
                       help='CAN interface name (default: can0)')
    parser.add_argument('--motor_id', '-m', type=int, required=True,
                       help='Motor CAN ID (1-255)')
    parser.add_argument('--master_id', type=lambda x: int(x, 0), default=0xFD,
                       help='Master CAN ID (default: 0xFD)')
    parser.add_argument('--mit', action='store_true',
                       help='Use MIT protocol (default: Private protocol)')
    parser.add_argument('--timeout', type=float, default=1.0,
                       help='Response timeout in seconds (default: 1.0)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Info command
    subparsers.add_parser('info', help='Get motor information')
    
    # Enable command
    subparsers.add_parser('enable', help='Enable motor')
    
    # Disable command
    disable_parser = subparsers.add_parser('disable', help='Disable motor')
    disable_parser.add_argument('--clear-error', action='store_true',
                               help='Clear error flags when disabling')
    
    # Zero command
    subparsers.add_parser('zero', help='Set current position as zero')
    
    # Status command
    subparsers.add_parser('status', help='Get motor status')
    
    # Motion control command
    motion_parser = subparsers.add_parser('motion', help='Motion control')
    motion_parser.add_argument('--position', type=float, default=0.0,
                              help='Target position (rad, default: 0.0)')
    motion_parser.add_argument('--velocity', type=float, default=0.0,
                              help='Target velocity (rad/s, default: 0.0)')
    motion_parser.add_argument('--kp', type=float, default=50.0,
                              help='Position gain (default: 50.0)')
    motion_parser.add_argument('--kd', type=float, default=1.0,
                              help='Velocity gain (default: 1.0)')
    motion_parser.add_argument('--torque', type=float, default=0.0,
                              help='Feed-forward torque (Nm, default: 0.0)')
    
    # Position control command
    pos_parser = subparsers.add_parser('position', help='Position control')
    pos_parser.add_argument('position', type=float, help='Target position (rad)')
    pos_parser.add_argument('--speed-limit', type=float, default=5.0,
                           help='Speed limit (rad/s, default: 5.0)')
    
    # Velocity control command
    vel_parser = subparsers.add_parser('velocity', help='Velocity control')
    vel_parser.add_argument('velocity', type=float, help='Target velocity (rad/s)')
    vel_parser.add_argument('--current-limit', type=float, default=10.0,
                           help='Current limit (A, default: 10.0)')
    
    # Current control command
    cur_parser = subparsers.add_parser('current', help='Current control')
    cur_parser.add_argument('current', type=float, help='Target current (A)')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor motor status')
    monitor_parser.add_argument('--interval', type=float, default=0.1,
                               help='Update interval in seconds (default: 0.1)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    setup_logging(args.verbose)
    
    # Command dispatch
    commands = {
        'info': cmd_info,
        'enable': cmd_enable,
        'disable': cmd_disable,
        'zero': cmd_zero,
        'status': cmd_status,
        'motion': cmd_motion,
        'position': cmd_position,
        'velocity': cmd_velocity,
        'current': cmd_current,
        'monitor': cmd_monitor,
    }
    
    try:
        commands[args.command](args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            raise
        sys.exit(1)

if __name__ == '__main__':
    main()
