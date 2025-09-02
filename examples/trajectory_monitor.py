#!/usr/bin/env python3
"""
Trajectory Tracking Example for RobStride Motors
Generates and executes sinusoidal trajectories using Private protocol control.
"""


import time
import csv
import numpy as np
import matplotlib.pyplot as plt
import argparse
import logging
from pathlib import Path
import sys


# Add parent directory to path to import robstride modules
sys.path.append(str(Path(__file__).parent.parent))


from robstride import RobStrideMotor


# Setup basic logging
logging.basicConfig(
   level=logging.INFO,
   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)




class TrajectoryTracker:
    """Trajectory tracking controller for RobStride motors using Private protocol."""
    
    def __init__(self, motor_id: int = 0x7F, can_interface: str = "can1"):
       """Initialize trajectory tracker.
      
       Args:
           motor_id: Motor CAN ID
           can_interface: CAN interface name
       """
       self.motor_id = motor_id
       self.can_interface = can_interface
       self.motor = None
      
    def connect(self) -> bool:
       """Connect to motor and initialize.
      
       Returns:
           True if connection successful, False otherwise
       """
       try:
           # Initialize motor with Private protocol
           self.motor = RobStrideMotor(
               can_id=self.motor_id,
               interface=self.can_interface,
               timeout=2.0
           )
          
           # Connect to motor
           self.motor.connect()
          
           # Enable motor
           self.motor.enable()
           time.sleep(0.1)
              
           logger.info(f"Successfully connected to motor {self.motor_id:#04x}")
           return True
          
       except Exception as e:
           logger.error(f"Connection failed: {e}")
           return False
  
    def disconnect(self):
       """Disconnect from motor and CAN interface."""
       try:
           if self.motor:
               self.motor.disable()
               self.motor.disconnect()
           logger.info("Disconnected from motor")
       except Exception as e:
           logger.error(f"Error during disconnect: {e}")
  
    def generate_sine_trajectory(self, amplitude: float, frequency: float,
                              num_periods: int, control_freq: int,
                              start_pos: float) -> tuple:
       """Generate sinusoidal trajectory.
      
       Args:
           amplitude: Sine wave amplitude in radians
           frequency: Sine wave frequency in Hz
           num_periods: Number of periods to generate
           control_freq: Control frequency in Hz
           start_pos: Starting position in radians
          
       Returns:
           Tuple of (time_array, position_array, velocity_array)
       """
       duration = num_periods / frequency
       t = np.linspace(0, duration, int(duration * control_freq))
       pos = start_pos + amplitude * np.sin(2 * np.pi * frequency * t)
       vel = 2 * np.pi * frequency * amplitude * np.cos(2 * np.pi * frequency * t)
      
       logger.info(f"Generated trajectory: {len(t)} points, {duration:.2f}s duration")
       return t, pos, vel
  
    def execute_trajectory(self, t: np.ndarray, pos: np.ndarray, vel: np.ndarray,
                         control_freq: int, kp: float, kd: float) -> list:
       """Execute trajectory using Private protocol control.
      
       Args:
           t: Time array
           pos: Position array
           vel: Velocity array
           control_freq: Control frequency in Hz
           kp: Position gain
           kd: Velocity gain
          
       Returns:
           List of recorded data points
       """
       data = []
       dt = 1.0 / control_freq
       error_count = 0
       max_errors = 5
      
       logger.info(f"Executing trajectory: {len(t)} steps at {control_freq}Hz")
      
       for i in range(len(t)):
           target_pos = pos[i]
           target_vel = 0
           target_torque = 0.0
          
           try:
               # Send Private protocol motion control command using set_motion_control
               self.motor.set_motion_control(
                   position=target_pos,
                   velocity=target_vel,
                   torque=target_torque,
                   kp=kp,
                   kd=kd
               )
              
               # Small delay to allow command processing
               time.sleep(0.001)
              
               # Record current motor status
               data.append([
                   t[i],
                   self.motor.position,
                   self.motor.velocity,
                   0.0,  # Current not directly available in Private protocol
                   self.motor.torque,
                   target_pos,
                   target_vel
               ])
              
               error_count = 0  # Reset error count on success
              
               # Progress logging
               if i % 100 == 0:
                   progress = (i / len(t)) * 100
                   logger.info(f"Progress: {progress:.1f}% ({i}/{len(t)})")
                   logger.debug(f"  Pos: {self.motor.position:.3f}, Vel: {self.motor.velocity:.3f}")
              
           except Exception as e:
               logger.error(f"Error at step {i}: {e}")
               error_count += 1
               if error_count >= max_errors:
                   logger.error("Too many errors, stopping execution")
                   break
          
           # Wait for next control step (account for processing time)
           elapsed = time.time() % dt
           sleep_time = max(0, dt - elapsed - 0.001)
           if sleep_time > 0:
               time.sleep(sleep_time)
      
       logger.info(f"Trajectory execution completed: {len(data)} data points")
       return data
  
    def save_data_to_csv(self, data: list, filename: str) -> bool:
       """Save trajectory data to CSV file.
      
       Args:
           data: List of data points
           filename: Output CSV filename
          
       Returns:
           True if save successful, False otherwise
       """
       try:
           with open(filename, 'w', newline='') as file:
               writer = csv.writer(file)
               writer.writerow([
                   'Time (s)', 'Position (rad)', 'Velocity (rad/s)',
                   'Current (A)', 'Torque (Nm)', 'Target Position (rad)',
                   'Target Velocity (rad/s)'
               ])
               writer.writerows(data)
          
           logger.info(f"Data saved to: {filename}")
           return True
          
       except Exception as e:
           logger.error(f"Failed to save CSV: {e}")
           return False
  
    def plot_trajectory(self, data: list, filename: str) -> bool:
       """Plot trajectory tracking results.
      
       Args:
           data: List of data points
           filename: Output plot filename
          
       Returns:
           True if plot successful, False otherwise
       """
       if not data:
           logger.error("No data to plot")
           return False
      
       try:
           data_array = np.array(data)
           t = data_array[:, 0]
           pos = data_array[:, 1]
           vel = data_array[:, 2]
           current = data_array[:, 3]
           torque = data_array[:, 4]
           target_pos = data_array[:, 5]
           target_vel = data_array[:, 6]
          
           # Unwrap position to handle discontinuities
           pos = np.unwrap(pos)
           target_pos = np.unwrap(target_pos)
          
           # Calculate tracking error
           pos_error = pos - target_pos
           vel_error = vel - target_vel
          
           # Create plots
           fig, axes = plt.subplots(5, 1, figsize=(12, 14))
          
           # Position tracking
           axes[0].plot(t, target_pos, 'b-', linewidth=2, label='Target')
           axes[0].plot(t, pos, 'r-', linewidth=1, alpha=0.8, label='Actual')
           axes[0].set_ylabel('Position (rad)')
           axes[0].set_title('Position Tracking')
           axes[0].legend()
           axes[0].grid(True, alpha=0.3)
          
           # Position error
           axes[1].plot(t, pos_error, 'purple', linewidth=1, label='Position Error')
           axes[1].set_ylabel('Position Error (rad)')
           axes[1].set_title('Position Tracking Error')
           axes[1].legend()
           axes[1].grid(True, alpha=0.3)
          
           # Velocity
           axes[2].plot(t, target_vel, 'b--', linewidth=2, label='Target Vel')
           axes[2].plot(t, vel, 'orange', linewidth=1, label='Actual Vel')
           axes[2].set_ylabel('Velocity (rad/s)')
           axes[2].set_title('Velocity Profile')
           axes[2].legend()
           axes[2].grid(True, alpha=0.3)
          
           # Velocity error
           axes[3].plot(t, vel_error, 'green', linewidth=1, label='Velocity Error')
           axes[3].set_ylabel('Velocity Error (rad/s)')
           axes[3].set_title('Velocity Tracking Error')
           axes[3].legend()
           axes[3].grid(True, alpha=0.3)
          
           # Torque
           axes[4].plot(t, torque, 'red', linewidth=1, label='Torque')
           axes[4].set_ylabel('Torque (Nm)')
           axes[4].set_xlabel('Time (s)')
           axes[4].set_title('Motor Torque')
           axes[4].legend()
           axes[4].grid(True, alpha=0.3)
          
           plt.tight_layout()
           plt.savefig(filename, dpi=300, bbox_inches='tight')
           plt.close()
          
           # Calculate and log statistics
           if len(pos_error) > 0:
               logger.info("Position Tracking Statistics:")
               logger.info(f"  - Mean absolute error: {np.mean(np.abs(pos_error)):.4f} rad")
               logger.info(f"  - Max absolute error: {np.max(np.abs(pos_error)):.4f} rad")
               logger.info(f"  - RMS error: {np.sqrt(np.mean(pos_error**2)):.4f} rad")
          
           logger.info(f"Plot saved to: {filename}")
           return True
          
       except Exception as e:
           logger.error(f"Failed to create plot: {e}")
           return False




def parse_arguments():
   """Parse command line arguments."""
   parser = argparse.ArgumentParser(description='RobStride Motor Trajectory Tracking (Private Protocol)')
  
   parser.add_argument('--motor-id', type=lambda x: int(x, 0), default=0x7F,
                      help='Motor CAN ID (hex or decimal)')
   parser.add_argument('--can-interface', type=str, default='can1',
                      help='CAN interface name')
   parser.add_argument('--amplitude', type=float, default=3.14,
                      help='Sine wave amplitude (rad)')
   parser.add_argument('--frequency', type=float, default=0.5,
                      help='Sine wave frequency (Hz)')
   parser.add_argument('--periods', type=int, default=2,
                      help='Number of periods')
   parser.add_argument('--control-freq', type=int, default=100,
                      help='Control frequency (Hz)')
   parser.add_argument('--kp', type=float, default=50.0,
                      help='Position gain')
   parser.add_argument('--kd', type=float, default=0.4,
                      help='Velocity gain')
   parser.add_argument('--output-prefix', type=str, default='trajectory',
                      help='Output file prefix')
  
   return parser.parse_args()




def main():
   """Main function."""
   args = parse_arguments()
  
   logger.info("Starting RobStride trajectory tracking test (Private Protocol)")
   logger.info("Parameters:")
   logger.info(f"  - Motor ID: {args.motor_id:#04x}")
   logger.info(f"  - CAN Interface: {args.can_interface}")
   logger.info(f"  - Amplitude: {args.amplitude} rad")
   logger.info(f"  - Frequency: {args.frequency} Hz")
   logger.info(f"  - Periods: {args.periods}")
   logger.info(f"  - Control Frequency: {args.control_freq} Hz")
   logger.info(f"  - Gains: Kp={args.kp}, Kd={args.kd}")
  
   # Initialize tracker
   tracker = TrajectoryTracker(
       motor_id=args.motor_id,
       can_interface=args.can_interface
   )
  
   try:
       # Connect to motor
       if not tracker.connect():
           logger.error("Failed to connect to motor")
           return False
      
       # Set zero position
       logger.info("Setting zero position...")
       tracker.motor.set_zero_position()
       time.sleep(0.5)
      
       # Get initial position
       start_pos = tracker.motor.position
       logger.info(f"Starting position: {start_pos:.3f} rad")
      
       # Generate trajectory
       t, pos, vel = tracker.generate_sine_trajectory(
           amplitude=args.amplitude,
           frequency=args.frequency,
           num_periods=args.periods,
           control_freq=args.control_freq,
           start_pos=start_pos
       )
      
       # Execute trajectory
       data = tracker.execute_trajectory(
           t=t, pos=pos, vel=vel,
           control_freq=args.control_freq,
           kp=args.kp, kd=args.kd
       )
      
       if not data:
           logger.error("No data collected during trajectory execution")
           return False
      
       # Save results
       csv_filename = f"{args.output_prefix}_data.csv"
       plot_filename = f"{args.output_prefix}_plot.png"
      
       csv_success = tracker.save_data_to_csv(data, csv_filename)
       plot_success = tracker.plot_trajectory(data, plot_filename)
      
       if csv_success and plot_success:
           logger.info("Trajectory tracking completed successfully!")
           logger.info(f"  - Data file: {csv_filename}")
           logger.info(f"  - Plot file: {plot_filename}")
           logger.info(f"  - Data points: {len(data)}/{len(t)}")
           return True
       else:
           logger.error("Failed to save results")
           return False
          
   except Exception as e:
       logger.error(f"Unexpected error: {e}")
       import traceback
       traceback.print_exc()
       return False
      
   finally:
       tracker.disconnect()




if __name__ == "__main__":
   success = main()
   if success:
       logger.info("Program completed successfully")
   else:
       logger.error("Program failed")
       sys.exit(1)













