#!/usr/bin/env python3
"""
Robot Servo Control via TCP/IP
Controls Dynamixel servos (AX-12, AX-18, MX-28, MX-64, MX-106) through LUCI protocol
Compatible with the Android app's communication protocol
"""

import socket
import struct
import time
from typing import List, Tuple, Optional


class RobotServoController:
    """Controller for robot servos via TCP/IP using LUCI protocol"""
    
    # Motor type constants
    MOTORTYPE_AX12 = 0
    MOTORTYPE_AX18 = 1
    MOTORTYPE_MX28 = 2
    MOTORTYPE_MX64 = 3
    MOTORTYPE_MX106 = 4
    MOTORTYPE_XL320 = 5
    
    # Baud rates (matching Java code)
    BAUDRATES = [2000000, 1000000, 500000, 222222, 117647, 100000, 57142, 9615]
    
    # Dynamixel register addresses
    GOAL_POSITION_ADDR = 30  # Start address for goal position
    
    def __init__(self, ip_address: str, port: int = 7777):
        """
        Initialize robot controller
        
        Args:
            ip_address: IP address of the robot controller
            port: TCP port (default 7777)
        """
        self.ip_address = ip_address
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.connected = False
        
    def connect(self, debug: bool = False) -> bool:
        """Connect to robot controller via TCP/IP"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)
            if debug:
                print(f"Connecting to {self.ip_address}:{self.port}...")
            self.socket.connect((self.ip_address, self.port))
            
            # Send registration packet (matching Android app - sent as STRING in Java)
            # The Android app uses PrintWriter for registration, DataOutputStream for commands
            register_packet = bytes([0, 0, 2, 3, 0, 0, 0, 0, 0, 0])
            # Try sending as string first (matching Android app behavior)
            try:
                register_str = register_packet.decode('utf-8', errors='ignore')
                self.socket.send(register_str.encode('utf-8'))
            except:
                # Fallback to raw bytes
                self.socket.send(register_packet)
            
            time.sleep(0.5)
            
            # Read any response
            try:
                response = self.socket.recv(1024)
                if debug and response:
                    print(f"Registration response: {response.hex()}")
            except:
                pass
            
            self.connected = True
            print(f"✓ Connected to robot at {self.ip_address}:{self.port}")
            return True
            
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from robot controller"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.connected = False
        print("Disconnected from robot")
    
    def _get_little_endian_bytes(self, value: int) -> bytes:
        """Convert integer to little-endian 2-byte array"""
        return struct.pack('<H', value & 0xFFFF)
    
    def _get_baud_rate_index(self, baud_rate: int) -> int:
        """Get baud rate index from baud rate value"""
        try:
            return self.BAUDRATES.index(baud_rate)
        except ValueError:
            print(f"Warning: Baud rate {baud_rate} not in list, using default 57142")
            return self.BAUDRATES.index(57142)
    
    def _create_dynamixel_sync_write_packet(
        self, 
        motor_ids: List[int], 
        motor_data: List[bytes],
        start_address: int = GOAL_POSITION_ADDR,
        data_length: int = 4
    ) -> bytes:
        """
        Create Dynamixel SYNC WRITE packet
        
        Args:
            motor_ids: List of motor IDs
            motor_data: List of data bytes for each motor (4 bytes: 2 pos + 2 vel)
            start_address: Register start address (default 30 for goal position)
            data_length: Length of data per motor (default 4 bytes)
        
        Returns:
            Dynamixel SYNC WRITE packet bytes
        """
        num_motors = len(motor_ids)
        packet_length = (data_length + 1) * num_motors + 4
        
        # Initialize packet
        packet = bytearray()
        
        # Header: 0xFF 0xFF 0xFE (broadcast), length, instruction (0x83 = SYNC WRITE)
        packet.extend([0xFF, 0xFF, 0xFE, packet_length, 0x83, start_address, data_length])
        
        # Calculate CRC
        crc = 0xFE + packet_length + 0x83 + start_address + data_length
        
        # Add motor data
        for i, motor_id in enumerate(motor_ids):
            packet.append(motor_id)
            crc += motor_id
            packet.extend(motor_data[i])
            for byte in motor_data[i]:
                crc += byte
        
        # Add CRC checksum
        crc = (255 - (crc & 0xFF)) & 0xFF
        packet.append(crc)
        
        return bytes(packet)
    
    def _create_luci_uart_packet(self, baud_rate: int, uart_packet: bytes) -> bytes:
        """
        Wrap Dynamixel packet in LUCI UART packet
        
        Args:
            baud_rate: Serial baud rate
            uart_packet: Dynamixel packet bytes
        
        Returns:
            LUCI UART packet bytes
        """
        baud_index = self._get_baud_rate_index(baud_rate)
        packet = bytearray([0, baud_index])
        packet.extend(uart_packet)
        return bytes(packet)
    
    def _create_luci_packet(self, module_number: int, mode: int, packet0: bytes) -> bytes:
        """
        Create final LUCI protocol packet
        
        Args:
            module_number: LUCI module number (254 for robot controller)
            mode: Mode (0 for write)
            packet0: UART packet bytes
        
        Returns:
            Complete LUCI packet bytes
        """
        if mode == 4 or mode == 5:
            return bytes([0, 0, 2])
        
        # Convert lengths and module number to little-endian bytes
        packet0_len_bytes = self._get_little_endian_bytes(len(packet0))
        packet1_len_bytes = self._get_little_endian_bytes(0)
        module_bytes = self._get_little_endian_bytes(module_number)
        
        luci_length = len(packet0) + 5
        luci_length_bytes = self._get_little_endian_bytes(luci_length)
        
        # Build packet
        packet = bytearray()
        packet.extend([0, 0, 2])  # LUCI header
        packet.extend(module_bytes)  # Module number
        packet.extend([0, 0, 0])  # Padding
        packet.extend(luci_length_bytes)  # Length
        packet.append(mode)  # Mode
        packet.extend(packet0_len_bytes)  # Packet0 length
        packet.extend(packet1_len_bytes)  # Packet1 length
        packet.extend(packet0)  # UART packet data
        
        return bytes(packet)
    
    def _degrees_to_motor_value(
        self, 
        degrees: float, 
        motor_type: int, 
        is_position: bool = True
    ) -> int:
        """
        Convert degrees to motor position/velocity value
        
        Args:
            degrees: Angle in degrees
            motor_type: Motor type constant
            is_position: True for position, False for velocity
        
        Returns:
            Motor value (0-1023 for AX, 0-4095 for MX position)
        """
        if motor_type in [self.MOTORTYPE_AX12, self.MOTORTYPE_AX18]:
            if is_position:
                # AX: 0-300° maps to 0-1023
                return int((degrees / 300.0) * 1023.0)
            else:
                # AX: 0-114 RPM maps to 0-1023
                return int((degrees / 114.0) * 1023.0)
        else:  # MX motors
            if is_position:
                # MX: 0-360° maps to 0-4095
                return int((degrees / 360.0) * 4095.0)
            else:
                # MX: 0-117 RPM maps to 0-1023
                return int((degrees / 117.0) * 1023.0)
    
    def send_servo_positions(
        self,
        motor_ids: List[int],
        motor_types: List[int],
        positions_degrees: List[float],
        velocities_rpm: List[float],
        baud_rate: int = 57142
    ) -> bool:
        """
        Send position and velocity commands to multiple servos
        
        Args:
            motor_ids: List of motor IDs (e.g., [1, 2, 3, ...])
            motor_types: List of motor types (MOTORTYPE_AX12, etc.)
            positions_degrees: List of target positions in degrees
            velocities_rpm: List of velocities in RPM
            baud_rate: Serial baud rate (default 57142)
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.connected:
            print("Error: Not connected to robot")
            return False
        
        if len(motor_ids) != len(motor_types) != len(positions_degrees) != len(velocities_rpm):
            print("Error: All lists must have the same length")
            return False
        
        # Convert degrees to motor values
        motor_data = []
        for i in range(len(motor_ids)):
            goal_pos = self._degrees_to_motor_value(positions_degrees[i], motor_types[i], True)
            goal_vel = self._degrees_to_motor_value(velocities_rpm[i], motor_types[i], False)
            
            # Convert to little-endian bytes
            pos_bytes = self._get_little_endian_bytes(goal_pos)
            vel_bytes = self._get_little_endian_bytes(goal_vel)
            
            # Combine: [pos_low, pos_high, vel_low, vel_high]
            motor_data.append(pos_bytes + vel_bytes)
        
        # Create Dynamixel SYNC WRITE packet
        dynamixel_packet = self._create_dynamixel_sync_write_packet(
            motor_ids, motor_data, self.GOAL_POSITION_ADDR, 4
        )
        
        # Wrap in LUCI UART packet
        luci_uart_packet = self._create_luci_uart_packet(baud_rate, dynamixel_packet)
        
        # Create final LUCI packet (module 254, mode 0 = write)
        luci_packet = self._create_luci_packet(254, 0, luci_uart_packet)
        
        # Send packet
        try:
            bytes_sent = self.socket.send(luci_packet)
            time.sleep(0.035)  # Delay matching Android app (35ms)
            return True
        except Exception as e:
            print(f"Error sending packet: {e}")
            return False
    
    def send_servo_positions_debug(
        self,
        motor_ids: List[int],
        motor_types: List[int],
        positions_degrees: List[float],
        velocities_rpm: List[float],
        baud_rate: int = 57142
    ) -> bool:
        """
        Debug version that prints packet information
        """
        if not self.connected:
            print("Error: Not connected to robot")
            return False
        
        if len(motor_ids) != len(motor_types) != len(positions_degrees) != len(velocities_rpm):
            print("Error: All lists must have the same length")
            return False
        
        print(f"\n[DEBUG] Sending to {len(motor_ids)} motors:")
        print(f"  Motor IDs: {motor_ids}")
        print(f"  Positions (degrees): {positions_degrees}")
        print(f"  Velocities (RPM): {velocities_rpm}")
        
        # Convert degrees to motor values
        motor_data = []
        for i in range(len(motor_ids)):
            goal_pos = self._degrees_to_motor_value(positions_degrees[i], motor_types[i], True)
            goal_vel = self._degrees_to_motor_value(velocities_rpm[i], motor_types[i], False)
            
            print(f"  Motor {motor_ids[i]}: {positions_degrees[i]}° -> {goal_pos}, {velocities_rpm[i]} RPM -> {goal_vel}")
            
            # Convert to little-endian bytes
            pos_bytes = self._get_little_endian_bytes(goal_pos)
            vel_bytes = self._get_little_endian_bytes(goal_vel)
            
            # Combine: [pos_low, pos_high, vel_low, vel_high]
            motor_data.append(pos_bytes + vel_bytes)
        
        # Create Dynamixel SYNC WRITE packet
        dynamixel_packet = self._create_dynamixel_sync_write_packet(
            motor_ids, motor_data, self.GOAL_POSITION_ADDR, 4
        )
        print(f"  Dynamixel packet length: {len(dynamixel_packet)} bytes")
        print(f"  Dynamixel packet (hex): {dynamixel_packet.hex()}")
        
        # Wrap in LUCI UART packet
        luci_uart_packet = self._create_luci_uart_packet(baud_rate, dynamixel_packet)
        print(f"  LUCI UART packet length: {len(luci_uart_packet)} bytes")
        
        # Create final LUCI packet (module 254, mode 0 = write)
        luci_packet = self._create_luci_packet(254, 0, luci_uart_packet)
        print(f"  Final LUCI packet length: {len(luci_packet)} bytes")
        print(f"  Final LUCI packet (hex): {luci_packet.hex()[:100]}...")  # First 100 chars
        
        # Send packet
        try:
            bytes_sent = self.socket.send(luci_packet)
            print(f"  ✓ Sent {bytes_sent} bytes")
            time.sleep(0.035)  # Delay matching Android app
            return True
        except Exception as e:
            print(f"  ✗ Error sending packet: {e}")
            return False
    
    def send_all_servos(
        self,
        positions_degrees: List[float],
        velocities_rpm: Optional[List[float]] = None,
        motor_ids: Optional[List[int]] = None,
        motor_types: Optional[List[int]] = None,
        baud_rate: int = 57142
    ) -> bool:
        """
        Convenience method to send positions to all 12 servos
        
        Args:
            positions_degrees: List of 12 positions in degrees
            velocities_rpm: Optional list of 12 velocities (default: 30 RPM for all)
            motor_ids: Optional list of motor IDs (default: 1-12)
            motor_types: Optional list of motor types (default: all AX12)
            baud_rate: Serial baud rate
        
        Returns:
            True if sent successfully
        """
        if motor_ids is None:
            motor_ids = list(range(1, 13))  # Motors 1-12
        
        if motor_types is None:
            motor_types = [self.MOTORTYPE_AX12] * 12  # All AX12
        
        if velocities_rpm is None:
            velocities_rpm = [30.0] * 12  # Default 30 RPM
        
        return self.send_servo_positions(
            motor_ids, motor_types, positions_degrees, velocities_rpm, baud_rate
        )
    
    def move_to_neutral(self, baud_rate: int = 57142) -> bool:
        """
        Move all servos to neutral positions (matching Android app)
        
        Neutral positions: [150, 90, 150, 150, 210, 150, 150, 90, 150, 150, 210, 150]
        """
        neutral_positions = [150, 90, 150, 150, 210, 150, 150, 90, 150, 150, 210, 150]
        return self.send_all_servos(neutral_positions, baud_rate=baud_rate)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Configuration
    ROBOT_IP = "192.168.1.100"  # Change this to your robot's IP address
    ROBOT_PORT = 7777
    
    # Create controller
    controller = RobotServoController(ROBOT_IP, ROBOT_PORT)
    
    # Connect to robot
    if not controller.connect():
        print("Failed to connect. Please check:")
        print("1. Robot is powered on")
        print("2. Robot and computer are on the same network")
        print("3. IP address is correct")
        exit(1)
    
    try:
        print("\n=== Robot Servo Control Demo ===\n")
        
        # Example 1: Move to neutral position
        print("1. Moving to neutral position...")
        controller.move_to_neutral()
        time.sleep(2)
        
        # Example 2: Move all servos to specific positions
        print("2. Moving servos to custom positions...")
        positions = [150, 90, 150, 150, 210, 150, 150, 90, 150, 150, 210, 150]
        controller.send_all_servos(positions, velocities_rpm=[30.0] * 12)
        time.sleep(2)
        
        # Example 3: Control specific motors
        print("3. Moving specific motors...")
        motor_ids = [1, 2, 3]
        motor_types = [controller.MOTORTYPE_AX12] * 3
        positions = [180, 120, 180]
        velocities = [30.0, 30.0, 30.0]
        controller.send_servo_positions(motor_ids, motor_types, positions, velocities)
        time.sleep(2)
        
        # Example 4: Animated movement
        print("4. Performing animated movement...")
        for angle in range(90, 210, 10):
            positions = [angle] * 12
            controller.send_all_servos(positions)
            time.sleep(0.1)
        
        # Return to neutral
        print("5. Returning to neutral...")
        controller.move_to_neutral()
        time.sleep(1)
        
        print("\n✓ Demo completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
    finally:
        # Disconnect
        controller.disconnect()

