#!/usr/bin/env python3
"""
Quick test - minimal code to test servo control
"""

from robot_servo_control import RobotServoController
import time

ROBOT_IP = "192.168.0.132"

print("Connecting to robot...")
robot = RobotServoController(ROBOT_IP, 7777)

if robot.connect():
    print("✓ Connected!")
    
    # Try the simplest possible command: move motor 1 to 150 degrees
    print("\nMoving motor 1 to 150°...")
    result = robot.send_servo_positions(
        motor_ids=[1],
        motor_types=[robot.MOTORTYPE_AX12],
        positions_degrees=[150.0],
        velocities_rpm=[30.0]
    )
    
    if result:
        print("✓ Command sent!")
        print("Waiting 3 seconds - watch motor 1...")
        time.sleep(3)
        
        # Try moving it to 180
        print("\nMoving motor 1 to 180°...")
        robot.send_servo_positions(
            motor_ids=[1],
            motor_types=[robot.MOTORTYPE_AX12],
            positions_degrees=[180.0],
            velocities_rpm=[30.0]
        )
        time.sleep(2)
        
        # Back to 150
        print("Moving motor 1 back to 150°...")
        robot.send_servo_positions(
            motor_ids=[1],
            motor_types=[robot.MOTORTYPE_AX12],
            positions_degrees=[150.0],
            velocities_rpm=[30.0]
        )
        time.sleep(1)
        
        print("\n✓ Test complete!")
    else:
        print("✗ Failed to send command")
    
    robot.disconnect()
else:
    print("✗ Connection failed!")

