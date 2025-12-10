import serial

# Change this to your actual port:
#   Windows → "COM3" / "COM4"
#   Linux   → "/dev/ttyACM0" or "/dev/ttyUSB0"
#   Mac     → "/dev/tty.usbserial-XXXX"
PORT = "COM17"     
BAUD = 57600

ser = serial.Serial(PORT, BAUD, timeout=0.5)

print(f"Listening on {PORT} at {BAUD} baud...\n")

while True:
    try:
        line = ser.readline()
        if line:
            print(line.hex(), "   |   ", line.decode(errors="ignore"))
    except KeyboardInterrupt:
        print("Stopped.")
        break
