# ACB v2.0 Actuator Examples

This directory contains example scripts demonstrating how to use the ACB v2.0 actuator.

## Examples

### 1. Basic Example (`basic_acb_example.py`)
A minimal example showing the core functionality:
- Connect to ACB v2.0
- Recalibrate sensors
- Set velocity to 1000°/s

**Usage:**
```bash
python basic_acb_example.py
```

### 2. Comprehensive Example (`comprehensive_acb_example.py`)
A full-featured example with command-line arguments:
- Command-line argument parsing
- User confirmation for recalibration
- Real-time monitoring
- Error handling and cleanup

**Usage:**
```bash
# Use default port and baudrate
python comprehensive_acb_example.py

# Specify custom port and baudrate
python comprehensive_acb_example.py /dev/ttyUSB0 2000000

# Use different communication mode
python comprehensive_acb_example.py /dev/ttyUSB0 2000000 --mode binary
```

## Configuration

### Port Configuration
Update the port in the examples to match your system:

**Linux/Mac:**
```python
port = "/dev/ttyUSB0"  # or /dev/ttyACM0, etc.
```

**Windows:**
```python
port = "COM3"  # or COM4, etc.
```

## Safety Notes

⚠️ **IMPORTANT SAFETY WARNINGS:**

1. **Recalibration:** The recalibration process will disable the motor. Ensure the actuator is in a safe position before starting.

2. **High Velocity:** Setting velocity to 1000°/s is very fast. Make sure the actuator has enough space to move safely.

3. **Emergency Stop:** Always have a way to stop the actuator if needed.

## Example Output

### Basic Example Output:
```
ACB v2.0 Basic Example
=========================
Connecting to /dev/ttyUSB0...
✅ Connected!
Recalibrating sensors...
✅ Recalibration complete!
Setting velocity to 1000°/s...
✅ Velocity set to 1000°/s!
✅ Example completed successfully!
Disconnected.
```

## Troubleshooting

### Connection Issues
- **Port not found:** Check that the device is connected and the port name is correct
- **Permission denied:** On Linux/Mac, you may need to add your user to the dialout group
- **Device busy:** Make sure no other software is using the serial port

### Safety Issues
- **Motor not stopping:** Use the emergency stop button on the actuator if available
- **Unexpected movement:** Ensure the actuator is properly secured before running examples
