# Open Actuator

A comprehensive control software for actuators with a modern GUI interface. This software provides real-time control and monitoring of actuators over USB serial communication.

## Features

- **Modern GUI Interface**: Clean, intuitive graphical interface for actuator control
- **Real-time Monitoring**: Live data visualization of position, velocity, and torque
- **Multiple Communication Modes**: Support for human-readable, binary, and SimpleFOC protocols
- **Cross-platform**: Works on Windows, macOS, and Linux
- **USB Serial Communication**: Direct communication with actuator control boards
- **Data Logging**: Built-in communication log and data export capabilities

## Installation

### Prerequisites

- Python 3.8 or higher
- USB serial device drivers (if needed for your operating system)

### Install from Source

1. Clone the repository:
```bash
git clone [<repository-url>](https://github.com/h-laboratories/open-actuator.git)
cd open-actuator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install the package:
```bash
pip install -e .
```

### Quick Start

1. Connect your actuator to a USB port
2. Run the GUI application:
```bash
python -m open_actuator.main
```

3. Select your USB port and click "Connect"
4. Use the controls to operate your actuator

## Usage

### GUI Interface

The main GUI provides the following features:

- **Connection Panel**: Select USB port, baud rate, and communication mode
- **Position Control**: Set target position with slider and numeric input
- **Velocity Control**: Set target velocity with slider and numeric input  
- **Torque Control**: Set torque limits with slider and numeric input
- **Actuator Commands**: Enable/disable, home, and stop controls
- **Real-time Monitoring**: Live display of current position, velocity, and torque
- **Communication Log**: Detailed log of all commands and responses

### Command Line Interface

You can also run the application with command-line arguments:

```bash
python -m open_actuator.main --port /dev/ttyUSB0 --baudrate 115200 --mode human
```

### Communication Modes

The software supports three communication modes:

1. **Human Readable** (default): String-based commands like `set_position 10.0`
2. **High Speed Binary**: Binary protocol for faster communication
3. **SimpleFOC**: SimpleFOC motor control protocol

## Actuator Commands

The software supports the following actuator commands:

| Command | ID | ARGS | Description |
|---------|-----|------|-------------|
| `set_position` | 0x01 | q8.8 position | Move actuator to specified position (in degrees) |
| `set_velocity` | 0x02 | q8.8 velocity | Set actuator velocity (in degrees/second) |
| `set_torque` | 0x03 | q8.8 torque | Set actuator torque limit (in Nm) |
| `get_position` | 0x04 | - | Get current actuator position |
| `get_velocity` | 0x05 | - | Get current actuator velocity |
| `get_torque` | 0x06 | - | Get current actuator torque |
| `enable` | 0x07 | - | Enable actuator motor |
| `disable` | 0x08 | - | Disable actuator motor |
| `home` | 0x09 | - | Move actuator to home position |
| `stop` | 0x0A | - | Stop actuator movement immediately |
| `cmd_mode` | 0xaB | int mode | Set the command mode |

## Variable Types

The following table describes the variable types used in the commands:

| Type | Description | Format | Range |
|------|-------------|---------|--------|
| q8.8 | Fixed point number with 8 bits integer and 8 bits decimal | 16-bit integer where decimal part is multiplied by 256 | -128.0 to +127.996 (divide the standard binary number by 256) |
| q4.12 | Fixed point number with 4 bits integer and 12 bits decimal | 16-bit integer where decimal part is multiplied by 4096 | -8.0 to +7.99975 (divide the standard binary number by 4096) |
| int | Signed integer | 16-bit integer | -32,768 to +32,767 |
| uint | Unsigned integer | 16-bit integer | 0 to 65,535 |

## Development

## Troubleshooting

### Connection Issues

- Ensure the actuator is properly connected via USB
- Check that the correct port is selected
- Verify the baud rate matches your actuator's configuration
- Try different USB ports or cables
- Flip USB C around (sometimes oneside in certain cables doesn't attach to USB 2)

### GUI Issues

- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check that your Python version is 3.8 or higher
- On Linux, you may need to install tkinter: `sudo apt-get install python3-tk`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions, please create an issue in the repository or contact the maintainers.
