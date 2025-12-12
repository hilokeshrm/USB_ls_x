#!/usr/bin/env python3
"""
Simple example: Control robot servos via TCP/IP
Quick start script for basic servo control
"""

from robot_servo_control import RobotServoController
import time

# ============================================================================
# CONFIGURATION - CHANGE THESE VALUES
# ============================================================================
ROBOT_IP = "192.168.0.132"  # ⚠️ CHANGE THIS to your robot's IP address
ROBOT_PORT = 7777

# ============================================================================
# MAIN
# ============================================================================

def main():
    # Create and connect to robot
    robot = RobotServoController(ROBOT_IP, ROBOT_PORT)
    
    if not robot.connect():
        print("\n❌ Connection failed!")
        print("Please check:")
        print("  • Robot is powered on")
        print("  • Robot and computer are on the same Wi-Fi network")
        print("  • IP address is correct in the script")
        return
    
    try:
        print("\n✅ Connected! Controlling servos...\n")
        
        # Move motor 1 to neutral position (150 degrees for AX-18A)
        print("Moving motor 1 to neutral position (150°)...")
        robot.send_servo_positions(
            motor_ids=[1],
            motor_types=[robot.MOTORTYPE_AX18],
            positions_degrees=[150.0],
            velocities_rpm=[30.0],
            baud_rate=222222
        )
        time.sleep(2)
        
        # Example: Move motor 1 (AX-18A) to 150 degrees with correct baud rate
        print("Moving motor 1 (AX-18A) to 150°...")
        robot.send_servo_positions(
            motor_ids=[1],
            motor_types=[robot.MOTORTYPE_AX18],  # AX-18A
            positions_degrees=[150.0],
            velocities_rpm=[30.0],
            baud_rate=222222  # Your baud rate
        )
        time.sleep(2)
        
        # Example: Move individual servo (AX-18A, ID 1, baud rate 222222)
        print("Moving motor 1 (AX-18A) to different positions...")
        robot.send_servo_positions(
            motor_ids=[1],
            motor_types=[robot.MOTORTYPE_AX18],  # AX-18A servo
            positions_degrees=[180],
            velocities_rpm=[30.0],
            baud_rate=222222  # Your baud rate
        )
        time.sleep(2)
        
        # Try another position
        print("Moving motor 1 to 120°...")
        robot.send_servo_positions(
            motor_ids=[1],
            motor_types=[robot.MOTORTYPE_AX18],
            positions_degrees=[120],
            velocities_rpm=[30.0],
            baud_rate=222222
        )
        time.sleep(2)
        
        # Return to neutral
        print("Returning motor 1 to neutral (150°)...")
        robot.send_servo_positions(
            motor_ids=[1],
            motor_types=[robot.MOTORTYPE_AX18],
            positions_degrees=[150.0],
            velocities_rpm=[30.0],
            baud_rate=222222
        )
        time.sleep(1)
        
        print("\n✅ Done!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        robot.disconnect()

if __name__ == "__main__":
    main()

