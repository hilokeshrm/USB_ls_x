# Robot Servo Control via TCP/IP

Python script to control Dynamixel servos (AX-12, MX-28, etc.) through TCP/IP using the LUCI protocol. Compatible with the Android app's communication protocol.

## Features

- ✅ Control multiple servos simultaneously via TCP/IP
- ✅ Support for AX-12, AX-18, MX-28, MX-64, MX-106 motors
- ✅ Automatic conversion from degrees to motor values
- ✅ Velocity control (RPM)
- ✅ Easy-to-use API

## Requirements

- Python 3.6 or higher
- Robot controller connected to the same Wi-Fi network
- TCP/IP connection (port 7777)

## Quick Start

1. **Find your robot's IP address** (check your router or robot's display)

2. **Edit the IP address** in `simple_servo_control.py`:
   ```python
   ROBOT_IP = "192.168.1.100"  # Change to your robot's IP
   ```

3. **Run the script**:
   ```bash
   python simple_servo_control.py
   ```

## Usage Examples

### Basic Usage

```python
from robot_servo_control import RobotServoController

# Create controller
robot = RobotServoController("192.168.1.100", 7777)

# Connect
robot.connect()

# Move all 12 servos to neutral position
robot.move_to_neutral()

# Move all servos to specific positions (in degrees)
positions = [150, 90, 150, 150, 210, 150, 150, 90, 150, 150, 210, 150]
robot.send_all_servos(positions)

# Disconnect
robot.disconnect()
```

### Control Specific Motors

```python
# Move only motors 1, 2, and 3
robot.send_servo_positions(
    motor_ids=[1, 2, 3],
    motor_types=[robot.MOTORTYPE_AX12] * 3,
    positions_degrees=[180, 120, 180],
    velocities_rpm=[30.0, 30.0, 30.0]
)
```

### Custom Motor Types

```python
# For MX motors (MX-28, MX-64, MX-106)
robot.send_servo_positions(
    motor_ids=[1, 2],
    motor_types=[robot.MOTORTYPE_MX28, robot.MOTORTYPE_MX64],
    positions_degrees=[180, 270],
    velocities_rpm=[50.0, 50.0]
)
```

### Animated Movement

```python
import time

# Smooth movement animation
for angle in range(90, 210, 5):
    positions = [angle] * 12
    robot.send_all_servos(positions)
    time.sleep(0.1)
```

## API Reference

### `RobotServoController(ip_address, port=7777)`

Create a new robot controller instance.

**Parameters:**
- `ip_address` (str): IP address of the robot controller
- `port` (int): TCP port (default: 7777)

### `connect() -> bool`

Connect to the robot controller. Returns `True` if successful.

### `disconnect()`

Disconnect from the robot controller.

### `send_servo_positions(motor_ids, motor_types, positions_degrees, velocities_rpm, baud_rate=57142) -> bool`

Send position and velocity commands to multiple servos.

**Parameters:**
- `motor_ids` (List[int]): List of motor IDs (e.g., [1, 2, 3])
- `motor_types` (List[int]): List of motor types (MOTORTYPE_AX12, etc.)
- `positions_degrees` (List[float]): Target positions in degrees
- `velocities_rpm` (List[float]): Velocities in RPM
- `baud_rate` (int): Serial baud rate (default: 57142)

**Returns:** `True` if sent successfully

### `send_all_servos(positions_degrees, velocities_rpm=None, motor_ids=None, motor_types=None, baud_rate=57142) -> bool`

Convenience method to send positions to all 12 servos.

**Parameters:**
- `positions_degrees` (List[float]): List of 12 positions in degrees
- `velocities_rpm` (List[float], optional): List of 12 velocities (default: 30 RPM)
- `motor_ids` (List[int], optional): Motor IDs (default: 1-12)
- `motor_types` (List[int], optional): Motor types (default: all AX12)
- `baud_rate` (int): Serial baud rate

### `move_to_neutral(baud_rate=57142) -> bool`

Move all servos to neutral positions:
`[150, 90, 150, 150, 210, 150, 150, 90, 150, 150, 210, 150]`

## Motor Types

- `MOTORTYPE_AX12 = 0` - AX-12A servo
- `MOTORTYPE_AX18 = 1` - AX-18 servo
- `MOTORTYPE_MX28 = 2` - MX-28 servo
- `MOTORTYPE_MX64 = 3` - MX-64 servo
- `MOTORTYPE_MX106 = 4` - MX-106 servo
- `MOTORTYPE_XL320 = 5` - XL-320 servo

## Position Ranges

- **AX-12/AX-18**: 0-300 degrees
- **MX-28/MX-64/MX-106**: 0-360 degrees

## Velocity Ranges

- **AX-12/AX-18**: 0-114 RPM
- **MX-28/MX-64/MX-106**: 0-117 RPM

## Troubleshooting

### Connection Failed
- Check that robot is powered on
- Verify robot and computer are on the same Wi-Fi network
- Check IP address is correct
- Ensure port 7777 is not blocked by firewall

### Servos Not Moving
- Check servo power supply
- Verify motor IDs are correct (1-12)
- Check motor types match your hardware
- Try lower velocity values

### Packet Errors
- Verify baud rate matches robot configuration
- Check network stability
- Try increasing delay between commands

## Protocol Details

The script uses the same protocol as the Android app:

1. **Dynamixel SYNC WRITE**: Sends position/velocity to multiple motors simultaneously
2. **LUCI UART Packet**: Wraps Dynamixel packet with baud rate info
3. **LUCI Protocol**: Final packet format sent over TCP/IP

Packet structure:
```
LUCI Header → Module Number → UART Packet → Dynamixel SYNC WRITE → Motor Data
```

## License

This code is provided as-is for controlling robot servos via TCP/IP.

