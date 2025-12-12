#!/usr/bin/env python3
"""
Test script for AX-18A servo with ID 1, baud rate 222222
"""

from robot_servo_control import RobotServoController
import time

ROBOT_IP = "192.168.0.132"
ROBOT_PORT = 7777
MOTOR_ID = 1
BAUD_RATE = 222222

print("=" * 60)
print("AX-18A Servo Control Test")
print("=" * 60)
print(f"IP: {ROBOT_IP}")
print(f"Motor ID: {MOTOR_ID}")
print(f"Motor Type: AX-18A")
print(f"Baud Rate: {BAUD_RATE}")
print("=" * 60)
print()

# Create and connect
robot = RobotServoController(ROBOT_IP, ROBOT_PORT)

if not robot.connect():
    print("\n❌ Connection failed!")
    print("Please check:")
    print("  • Robot is powered on")
    print("  • Robot and computer are on the same Wi-Fi network")
    print("  • IP address is correct")
    exit(1)

try:
    print("✅ Connected! Testing AX-18A servo...\n")
    
    # Test 1: Move to 150 degrees (neutral)
    print("Test 1: Moving to 150° (neutral position)...")
    robot.send_servo_positions_debug(
        motor_ids=[MOTOR_ID],
        motor_types=[robot.MOTORTYPE_AX18],
        positions_degrees=[150.0],
        velocities_rpm=[30.0],
        baud_rate=BAUD_RATE
    )
    time.sleep(3)
    
    # Test 2: Move to 180 degrees
    print("\nTest 2: Moving to 180°...")
    robot.send_servo_positions_debug(
        motor_ids=[MOTOR_ID],
        motor_types=[robot.MOTORTYPE_AX18],
        positions_degrees=[180.0],
        velocities_rpm=[30.0],
        baud_rate=BAUD_RATE
    )
    time.sleep(3)
    
    # Test 3: Move to 120 degrees
    print("\nTest 3: Moving to 120°...")
    robot.send_servo_positions_debug(
        motor_ids=[MOTOR_ID],
        motor_types=[robot.MOTORTYPE_AX18],
        positions_degrees=[120.0],
        velocities_rpm=[30.0],
        baud_rate=BAUD_RATE
    )
    time.sleep(3)
    
    # Test 4: Smooth movement animation
    print("\nTest 4: Smooth movement from 90° to 210°...")
    for angle in range(90, 211, 10):
        print(f"  Moving to {angle}°...", end="\r")
        robot.send_servo_positions(
            motor_ids=[MOTOR_ID],
            motor_types=[robot.MOTORTYPE_AX18],
            positions_degrees=[float(angle)],
            velocities_rpm=[30.0],
            baud_rate=BAUD_RATE
        )
        time.sleep(0.2)
    print()
    
    # Return to neutral
    print("\nReturning to neutral (150°)...")
    robot.send_servo_positions(
        motor_ids=[MOTOR_ID],
        motor_types=[robot.MOTORTYPE_AX18],
        positions_degrees=[150.0],
        velocities_rpm=[30.0],
        baud_rate=BAUD_RATE
    )
    time.sleep(1)
    
    print("\n✅ Test complete!")
    print("\nIf the servo didn't move, check:")
    print("  1. Servo is powered (LED should be on)")
    print("  2. Motor ID is correct (should be 1)")
    print("  3. Baud rate matches servo configuration (222222)")
    print("  4. Servo is not in wheel mode")
    
except KeyboardInterrupt:
    print("\n\n⚠️ Stopped by user")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    robot.disconnect()

