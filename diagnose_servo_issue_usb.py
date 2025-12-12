#!/usr/bin/env python3
"""
Diagnostic script to troubleshoot servo control issues via USB/Serial
"""

from robot_servo_control_usb import RobotServoControllerUSB
import time
import sys

SERIAL_PORT = "COM20"  # Change this to your serial port
SERIAL_BAUD = 57600    # Serial communication baud rate

def main():
    print("=" * 60)
    print("ROBOT SERVO CONTROL DIAGNOSTIC (USB/Serial)")
    print("=" * 60)
    print()
    
    # Step 1: Test connection
    print("Step 1: Testing USB/Serial connection...")
    robot = RobotServoControllerUSB(SERIAL_PORT, SERIAL_BAUD)
    
    if not robot.connect(debug=True):
        print("\n❌ FAILED: Cannot connect to robot")
        print("\nTroubleshooting:")
        print("  1. Check robot is powered on")
        print("  2. Verify serial port: " + SERIAL_PORT)
        print("  3. Check port is not in use by another application")
        print("  4. Try different baud rates if connection fails")
        print("  5. On Windows: Check Device Manager for COM port")
        print("  6. On Linux: Check /dev/ttyUSB* or /dev/ttyACM*")
        return False
    
    print("✓ Connection successful\n")
    
    # Step 2: Test with debug output
    print("Step 2: Testing servo command with debug output...")
    print("-" * 60)
    
    # Try moving just one motor first
    print("\nTrying to move motor 1 to 150°...")
    success = robot.send_servo_positions_debug(
        motor_ids=[1],
        motor_types=[robot.MOTORTYPE_AX12],
        positions_degrees=[150.0],
        velocities_rpm=[30.0]
    )
    
    if success:
        print("\n✓ Command sent successfully")
        print("Waiting 2 seconds to see if motor moves...")
        time.sleep(2)
    else:
        print("\n✗ Failed to send command")
        return False
    
    # Step 3: Try all motors to neutral
    print("\n" + "-" * 60)
    print("Step 3: Moving all motors to neutral position...")
    print("Neutral positions: [150, 90, 150, 150, 210, 150, 150, 90, 150, 150, 210, 150]")
    
    success = robot.send_servo_positions_debug(
        motor_ids=list(range(1, 13)),
        motor_types=[robot.MOTORTYPE_AX12] * 12,
        positions_degrees=[150, 90, 150, 150, 210, 150, 150, 90, 150, 150, 210, 150],
        velocities_rpm=[30.0] * 12
    )
    
    if success:
        print("\n✓ Neutral command sent")
        print("Waiting 3 seconds...")
        time.sleep(3)
    else:
        print("\n✗ Failed to send neutral command")
    
    # Step 4: Try different positions
    print("\n" + "-" * 60)
    print("Step 4: Testing movement to different positions...")
    
    test_positions = [
        [180, 90, 150, 150, 210, 150, 150, 90, 150, 150, 210, 150],
        [120, 90, 150, 150, 210, 150, 150, 90, 150, 150, 210, 150],
    ]
    
    for i, pos in enumerate(test_positions):
        print(f"\nTest {i+1}: Moving motor 1 to {pos[0]}°...")
        success = robot.send_servo_positions(
            motor_ids=[1],
            motor_types=[robot.MOTORTYPE_AX12],
            positions_degrees=[pos[0]],
            velocities_rpm=[30.0]
        )
        if success:
            time.sleep(2)
    
    # Step 5: Check motor IDs
    print("\n" + "-" * 60)
    print("Step 5: Testing different motor IDs...")
    print("Note: Valid motor IDs are typically 1-12 for your robot")
    
    # Try motor 1, 2, 3 (valid)
    print("\nTrying motors 1, 2, 3...")
    robot.send_servo_positions_debug(
        motor_ids=[1, 2, 3],
        motor_types=[robot.MOTORTYPE_AX12] * 3,
        positions_degrees=[180, 120, 180],
        velocities_rpm=[30.0, 30.0, 30.0]
    )
    time.sleep(2)
    
    # Return to neutral
    print("\nReturning to neutral...")
    robot.move_to_neutral()
    time.sleep(1)
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)
    print("\nIf motors still don't move, check:")
    print("  1. Servos are powered (LEDs should be on)")
    print("  2. Motor IDs are correct (1-12)")
    print("  3. Motor types match your hardware (AX12, MX28, etc.)")
    print("  4. Baud rate matches robot configuration")
    print("  5. Serial port is correct and not in use")
    print("  6. Try using the Android app to verify robot works")
    
    robot.disconnect()
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()

