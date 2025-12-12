#!/usr/bin/env python3
"""
Test script to verify TCP/IP connection to robot
Helps diagnose connection issues
"""

import socket
import sys
from robot_servo_control import RobotServoController

def test_connection(ip: str, port: int = 7777):
    """Test basic TCP/IP connection to robot"""
    print(f"Testing connection to {ip}:{port}...")
    
    try:
        # Test basic socket connection
        print("1. Testing socket connection...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.0)
        sock.connect((ip, port))
        print("   ✓ Socket connection successful")
        sock.close()
        
        # Test RobotServoController
        print("2. Testing RobotServoController...")
        robot = RobotServoController(ip, port)
        if robot.connect():
            print("   ✓ RobotServoController connected")
            
            # Test sending a neutral position command
            print("3. Testing servo command...")
            if robot.send_all_servos([150] * 12):
                print("   ✓ Servo command sent successfully")
            else:
                print("   ✗ Failed to send servo command")
            
            robot.disconnect()
            print("\n✅ All tests passed!")
            return True
        else:
            print("   ✗ RobotServoController connection failed")
            return False
            
    except socket.timeout:
        print("   ✗ Connection timeout - robot may be unreachable")
        return False
    except socket.gaierror as e:
        print(f"   ✗ DNS resolution failed: {e}")
        print("   Check that the IP address is correct")
        return False
    except ConnectionRefusedError:
        print("   ✗ Connection refused - robot may not be listening on port 7777")
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        robot_ip = sys.argv[1]
    else:
        robot_ip = input("Enter robot IP address: ").strip()
    
    if not robot_ip:
        print("Error: IP address required")
        sys.exit(1)
    
    print("=" * 50)
    print("Robot Connection Test")
    print("=" * 50)
    print()
    
    success = test_connection(robot_ip)
    
    if not success:
        print("\n" + "=" * 50)
        print("Troubleshooting Tips:")
        print("=" * 50)
        print("1. Verify robot is powered on")
        print("2. Check robot and computer are on the same Wi-Fi network")
        print("3. Verify IP address is correct")
        print("4. Check firewall settings (port 7777)")
        print("5. Try pinging the robot: ping " + robot_ip)
        sys.exit(1)

