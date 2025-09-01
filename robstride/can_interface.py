"""
CAN bus interface for RobStride motor communication.
"""

import can
import threading
import time
import logging
from typing import Optional, Callable, Any

logger = logging.getLogger(__name__)

class CANInterface:
    """CAN bus interface wrapper"""
    
    def __init__(self, interface_name: str, bitrate: int = 1000000):
        """
        Initialize CAN interface.
        
        Args:
            interface_name: CAN interface name (e.g., 'can0', 'can1')
            bitrate: CAN bus bitrate in bps (default: 1000000)
        """
        self.interface_name = interface_name
        self.bitrate = bitrate
        self.bus: Optional[can.Bus] = None
        self.notifier: Optional[can.Notifier] = None
        self.listener_thread: Optional[threading.Thread] = None
        self.running = False
        self.message_callbacks = []
        
    def connect(self):
        """Connect to CAN bus"""
        try:
            self.bus = can.Bus(
                interface='socketcan',
                channel=self.interface_name,
                bitrate=self.bitrate
            )
            logger.info(f"Connected to CAN interface {self.interface_name} at {self.bitrate} bps")
            
            # Start message listener
            self.running = True
            self.listener_thread = threading.Thread(target=self._listen_messages, daemon=True)
            self.listener_thread.start()
            
        except Exception as e:
            logger.error(f"Failed to connect to CAN interface {self.interface_name}: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from CAN bus"""
        self.running = False
        
        if self.listener_thread:
            self.listener_thread.join(timeout=1.0)
            
        if self.notifier:
            self.notifier.stop()
            
        if self.bus:
            self.bus.shutdown()
            logger.info(f"Disconnected from CAN interface {self.interface_name}")
    
    def send_message(self, can_id: int, data: list, is_extended: bool = True):
        """
        Send CAN message.
        
        Args:
            can_id: CAN message ID
            data: Message data (list of bytes)
            is_extended: True for extended frame, False for standard frame
        """
        if not self.bus:
            raise RuntimeError("CAN bus not connected")
        
        message = can.Message(
            arbitration_id=can_id,
            data=data,
            is_extended_id=is_extended
        )
        
        try:
            self.bus.send(message)
            logger.debug(f"Sent CAN message: ID=0x{can_id:08X}, Data={data}")
        except Exception as e:
            logger.error(f"Failed to send CAN message: {e}")
            raise
    
    def add_message_callback(self, callback: Callable[[int, list, bool], None]):
        """
        Add callback for received CAN messages.
        
        Args:
            callback: Function to call with (can_id, data, is_extended) parameters
        """
        self.message_callbacks.append(callback)
    
    def remove_message_callback(self, callback: Callable[[int, list, bool], None]):
        """
        Remove message callback.
        
        Args:
            callback: Callback function to remove
        """
        if callback in self.message_callbacks:
            self.message_callbacks.remove(callback)
    
    def _listen_messages(self):
        """Listen for incoming CAN messages (runs in separate thread)"""
        while self.running and self.bus:
            try:
                message = self.bus.recv(timeout=0.1)
                if message:
                    logger.debug(f"Received CAN message: ID=0x{message.arbitration_id:08X}, Data={list(message.data)}")
                    
                    # Call all registered callbacks
                    for callback in self.message_callbacks:
                        try:
                            callback(message.arbitration_id, list(message.data), message.is_extended_id)
                        except Exception as e:
                            logger.error(f"Error in message callback: {e}")
                            
            except Exception as e:
                if self.running:  # Only log if we're still supposed to be running
                    logger.error(f"Error receiving CAN message: {e}")
                    time.sleep(0.1)  # Brief pause before retrying
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
