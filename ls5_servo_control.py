#!/usr/bin/env python3
"""
ls5_servo_set_baud_and_angle.py

1) Set AX-series servo (ID 1) baudrate ~222222 bps by writing Control Table address 4.
   Computed baud value = 8 because Baudrate(BPS) = 2,000,000 / (Value + 1).
2) Set goal position (address 30, 2 bytes) from an angle in degrees (0..300 deg -> 0..1023).

Wraps Dynamixel Protocol 1.0 packets in the LUCI general packet header used in your Java code,
then sends them over TCP to the LS5 (port 7777).
"""
import socket
import time
from typing import List

LS5_IP = "192.168.0.110"   # <--- change to your LS5 IP
LS5_PORT = 7777

def get_lh_bytes(x: int) -> bytes:
    return bytes([x & 0xFF, (x >> 8) & 0xFF])

def build_write_packet(servo_id: int, address: int, data: bytes) -> bytes:
    """
    Build a Dynamixel Protocol 1.0 WRITE instruction packet (no LUCI wrap).
    Packet format:
      0xFF 0xFF ID LENGTH INSTRUCTION PARAM1 PARAM2 ... CHECKSUM
    where LENGTH = number_of_parameters + 2  (params + instruction + checksum fields accounted)
    INSTRUCTION for WRITE = 0x03
    CHECKSUM = 255 - ((ID + LENGTH + INSTRUCTION + sum(params)) & 0xFF)
    """
    INSTR_WRITE = 0x03
    params = bytes([address]) + data
    length = len(params) + 2  # instruction + params + checksum => length field as Dynamixel doc
    header = bytearray([0xFF, 0xFF, servo_id & 0xFF, length & 0xFF, INSTR_WRITE])
    body = bytearray(params)
    checksum_val = (servo_id + length + INSTR_WRITE + sum(body)) & 0xFF
    checksum = (255 - checksum_val) & 0xFF
    packet = bytes(header + body + bytearray([checksum]))
    return packet

def create_luci_general_packet(mbnum: int, payload: bytes) -> bytes:
    """
    LUCI header used in your Java code:
      [0,0,2, mbnum_low, mbnum_high, 0,0,0, luci_len_low, luci_len_high] + payload
    """
    mb_bytes = get_lh_bytes(mbnum)
    luci_len_bytes = get_lh_bytes(len(payload))
    header = bytearray([
        0, 0, 2,
        mb_bytes[0], mb_bytes[1],
        0, 0, 0,
        luci_len_bytes[0], luci_len_bytes[1]
    ])
    return bytes(header) + payload

def send_luci_packet(ip: str, port: int, luci_packet: bytes, timeout=1.0) -> bytes:
    with socket.create_connection((ip, port), timeout=5) as sock:
        sock.settimeout(timeout)
        sock.sendall(luci_packet)
        try:
            resp = sock.recv(2048)
            return resp
        except socket.timeout:
            return b''

def angle_deg_to_ax_position(angle_deg: float) -> int:
    """
    Convert degrees to AX 0..1023 position.
    AX typical range is 0..300 degrees -> 0..1023 ticks.
    Clamp to 0..1023.
    """
    pos = round((angle_deg / 300.0) * 1023.0)
    return max(0, min(1023, pos))

if __name__ == "__main__":
    servo_id = 1
    # 1) Set baudrate to ~222,222 bps: compute register value
    target_bps = 222222
    baud_value = round((2000000.0 / target_bps) - 1.0)  # -> 8 for 222222
    if baud_value < 0 or baud_value > 254:
        raise ValueError("Computed baud register out of range: %d" % baud_value)
    print(f"Setting servo ID {servo_id} baud register (addr=4) -> value {baud_value} (target ~{target_bps} bps)")

    # Build WRITE packet to address 4 with a single byte (baud_value)
    write_baud_pkt = build_write_packet(servo_id=servo_id, address=4, data=bytes([baud_value]))
    luci_pkt_baud = create_luci_general_packet(mbnum=254, payload=write_baud_pkt)
    print("LUCI packet (set baud) hex:", luci_pkt_baud.hex())

    resp = send_luci_packet(LS5_IP, LS5_PORT, luci_pkt_baud, timeout=0.8)
    print("Response (set baud) (hex):", resp.hex() if resp else "<no response>")

    # IMPORTANT: after changing servo baudrate, the servo will expect frames at new baud.
    # If the LS5/bridge does not switch its UART speed automatically, further commands may not reach the servo.
    # Wait a short moment (and ensure your LS5 supports switching its UART speed to match).
    time.sleep(0.2)

    # 2) Set angle (goal position) at address 30 (two bytes little-endian)
    desired_angle = 90.0   # degrees; change this to whatever angle you want (0..300)
    pos = angle_deg_to_ax_position(desired_angle)
    pos_lo = pos & 0xFF
    pos_hi = (pos >> 8) & 0xFF
    print(f"Setting servo ID {servo_id} goal position -> angle {desired_angle} deg -> position {pos}")

    write_goal_pkt = build_write_packet(servo_id=servo_id, address=30, data=bytes([pos_lo, pos_hi]))
    luci_pkt_goal = create_luci_general_packet(mbnum=254, payload=write_goal_pkt)
    print("LUCI packet (set goal) hex:", luci_pkt_goal.hex())

    resp2 = send_luci_packet(LS5_IP, LS5_PORT, luci_pkt_goal, timeout=0.8)
    print("Response (set goal) (hex):", resp2.hex() if resp2 else "<no response>")

    print("Done.")
