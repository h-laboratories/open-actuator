# Open Actuator
A control software for actuators.

## Commands

Commands are 

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
| `cmd_mode` | 0xaB | int mode | Set the command mode (see command modes)|

## Command modes 
IT's possible to communicate with the open actuator control boards in one of three ways, dependant on the interface used:
1. Human readable format (USB) - String commands (e.g. `set_position 10.0`)
2. High speed non human readable (USB/CAN) - Pure bit format (e.g. 0x010A00 = `set_position 10.0` where decimals are * 256 for this command see (Variable Types)[#variable-types]).
3. SimpleFOC motor control mode (USB).


## Variable types

The following table describes the variable types used in the commands:

| Type | Description | Format | Range |
|------|-------------|---------|--------|
| q8.8 | Fixed point number with 8 bits integer and 8 bits decimal | 16-bit integer where decimal part is multiplied by 256 | -128.0 to +127.996 (divide the standard binary number by 256) |
| q4.12 | Fixed point number with 4 bits integer and 12 bits decimal | 16-bit integer where decimal part is multiplied by 4096 | -8.0 to +7.99975 (divide the standard binary number by 4096) |
| int | Signed integer | 16-bit integer | -32,768 to +32,767 |
| uint | Unsigned integer | 16-bit integer | 0 to 65,535 |


