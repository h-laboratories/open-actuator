"""
Core actuator communication interface.

This module provides the main interface for communicating with actuators
over USB serial connection.
"""

import serial
import time
import struct
from typing import Optional, Dict, Any, Tuple
from enum import IntEnum


class CommandID(IntEnum):
    """Actuator command IDs."""
    SET_POSITION = 0x01
    SET_VELOCITY = 0x02
    SET_TORQUE = 0x03
    GET_POSITION = 0x04
    GET_VELOCITY = 0x05
    GET_TORQUE = 0x06
    ENABLE = 0x07
    DISABLE = 0x08
    HOME = 0x09
    STOP = 0x0A
    CMD_MODE = 0xAB
    BROADCAST = 0xAC


class CommandMode(IntEnum):
    """Command communication modes."""
    HUMAN_READABLE = 1
    HIGH_SPEED_BINARY = 2
    SIMPLEFOC = 3


class ActuatorInterface:
    """
    Interface for communicating with actuators over USB serial.
    
    Supports both human-readable and binary command formats.
    """
    
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 1.0):
        """
        Initialize the actuator interface.
        
        Args:
            port: Serial port name (e.g., '/dev/ttyUSB0' or 'COM3')
            baudrate: Serial communication baud rate
            timeout: Serial communication timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn: Optional[serial.Serial] = None
        self.command_mode = CommandMode.HUMAN_READABLE
        self.connected = False
        
    def connect(self) -> bool:
        """
        Establish connection to the actuator.
        
        Returns:
            True if connection successful, False otherwise

        """
        print(f"Connecting to {self.port} at {self.baudrate} baud")
        
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            time.sleep(0.1)  # Allow connection to stabilize
            self.connected = True
            return True
        except (serial.SerialException, OSError) as e:
            import traceback
            traceback.print_exc()
            print(f"Failed to connect to {self.port}: {e}")
            
            self.connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the actuator."""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self.connected = False
    
    def _float_to_q88(self, value: float) -> int:
        """
        Convert float to q8.8 fixed point format.
        
        Args:
            value: Float value to convert
            
        Returns:
            16-bit integer in q8.8 format
        """
        # Clamp value to valid range
        value = max(-128.0, min(127.996, value))
        return int(value * 256) & 0xFFFF
    
    def _q88_to_float(self, value: int) -> float:
        """
        Convert q8.8 fixed point format to float.
        
        Args:
            value: 16-bit integer in q8.8 format
            
        Returns:
            Float value
        """
        # Handle signed 16-bit integer
        if value & 0x8000:
            value = value - 0x10000
        return value / 256.0
    
    def _send_human_command(self, command: str) -> Optional[str]:
        """
        Send human-readable command and get response.
        
        Args:
            command: Human-readable command string
            
        Returns:
            Response string or None if failed
        """
        if not self.connected or not self.serial_conn:
            print(f"[DEBUG] Not connected, cannot send command: {command}")
            return None
            
        try:
            print(f"[DEBUG] Sending command: '{command}'")
            self.serial_conn.write(f"{command}\n".encode())
            self.serial_conn.flush()  # Ensure data is sent
            
            # Wait a bit for response
            time.sleep(0.1)
            
            # Read response with timeout
            response = self.serial_conn.readline().decode().strip()
            print(f"[DEBUG] Received response: '{response}'")
            return response
        except (serial.SerialException, UnicodeDecodeError) as e:
            print(f"[DEBUG] Communication error: {e}")
            return None
    
    def _send_binary_command(self, command_id: int, data: bytes = b'') -> Optional[bytes]:
        """
        Send binary command and get response.
        
        Args:
            command_id: Command ID
            data: Optional data payload
            
        Returns:
            Response bytes or None if failed
        """
        if not self.connected or not self.serial_conn:
            return None
            
        try:
            # Send command with data
            packet = struct.pack('B', command_id) + data
            self.serial_conn.write(packet)
            
            # Read response (assuming single byte response for now)
            response = self.serial_conn.read(1)
            return response
        except (serial.SerialException, struct.error) as e:
            print(f"Binary communication error: {e}")
            return None
    
    def set_position(self, position: float) -> bool:
        """
        Move actuator to specified position.
        
        Args:
            position: Target position in degrees
            
        Returns:
            True if command sent successfully
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command(f"set_position {position}")
            print(f"[DEBUG] Set position response: '{response}'")
            # The firmware responds with "set_position <value>"
            if response and response.startswith("set_position "):
                try:
                    # Extract the value to verify it was set correctly
                    value_str = response.split(" ", 1)[1]
                    set_value = float(value_str)
                    print(f"[DEBUG] Position set to: {set_value}")
                    return True
                except (ValueError, IndexError) as e:
                    print(f"[DEBUG] Failed to parse set position response: {e}")
                    return False
            return response is not None
        else:
            data = struct.pack('>h', self._float_to_q88(position))
            response = self._send_binary_command(CommandID.SET_POSITION, data)
            return response is not None
    
    def set_velocity(self, velocity: float) -> bool:
        """
        Set actuator velocity.
        
        Args:
            velocity: Target velocity in degrees/second
            
        Returns:
            True if command sent successfully
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command(f"set_velocity {velocity}")
            print(f"[DEBUG] Set velocity response: '{response}'")
            # The firmware responds with "set_velocity <value>"
            if response and response.startswith("set_velocity "):
                try:
                    # Extract the value to verify it was set correctly
                    value_str = response.split(" ", 1)[1]
                    set_value = float(value_str)
                    print(f"[DEBUG] Velocity set to: {set_value}")
                    return True
                except (ValueError, IndexError) as e:
                    print(f"[DEBUG] Failed to parse set velocity response: {e}")
                    return False
            return response is not None
        else:
            data = struct.pack('>h', self._float_to_q88(velocity))
            response = self._send_binary_command(CommandID.SET_VELOCITY, data)
            return response is not None
    
    def set_torque(self, torque: float) -> bool:
        """
        Set actuator torque limit.
        
        Args:
            torque: Torque limit in Nm
            
        Returns:
            True if command sent successfully
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command(f"set_torque {torque}")
            print(f"[DEBUG] Set torque response: '{response}'")
            # The firmware responds with "set_torque <value>"
            if response and response.startswith("set_torque "):
                try:
                    # Extract the value to verify it was set correctly
                    value_str = response.split(" ", 1)[1]
                    set_value = float(value_str)
                    print(f"[DEBUG] Torque set to: {set_value}")
                    return True
                except (ValueError, IndexError) as e:
                    print(f"[DEBUG] Failed to parse set torque response: {e}")
                    return False
            return response is not None
        else:
            data = struct.pack('>h', self._float_to_q88(torque))
            response = self._send_binary_command(CommandID.SET_TORQUE, data)
            return response is not None
    
    def get_position(self) -> Optional[float]:
        """
        Get current actuator position.
        
        Returns:
            Current position in degrees or None if failed
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command("get_position")
            print(f"[DEBUG] Get position response: '{response}'")
            if response:
                try:
                    # The firmware responds with "get_position <value>"
                    if response.startswith("get_position "):
                        value_str = response.split(" ", 1)[1]
                        return float(value_str)
                    else:
                        return float(response)
                except (ValueError, IndexError) as e:
                    print(f"[DEBUG] Failed to parse position response: {e}")
                    return None
        else:
            response = self._send_binary_command(CommandID.GET_POSITION)
            if response and len(response) >= 2:
                value = struct.unpack('>h', response[:2])[0]
                return self._q88_to_float(value)
        return None
    
    def get_velocity(self) -> Optional[float]:
        """
        Get current actuator velocity.
        
        Returns:
            Current velocity in degrees/second or None if failed
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command("get_velocity")
            print(f"[DEBUG] Get velocity response: '{response}'")
            if response:
                try:
                    # The firmware responds with "get_velocity <value>"
                    if response.startswith("get_velocity "):
                        value_str = response.split(" ", 1)[1]
                        return float(value_str)
                    else:
                        return float(response)
                except (ValueError, IndexError) as e:
                    print(f"[DEBUG] Failed to parse velocity response: {e}")
                    return None
        else:
            response = self._send_binary_command(CommandID.GET_VELOCITY)
            if response and len(response) >= 2:
                value = struct.unpack('>h', response[:2])[0]
                return self._q88_to_float(value)
        return None
    
    def get_torque(self) -> Optional[float]:
        """
        Get current actuator torque.
        
        Returns:
            Current torque in Nm or None if failed
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command("get_torque")
            print(f"[DEBUG] Get torque response: '{response}'")
            if response:
                try:
                    # The firmware responds with "get_torque <value>"
                    if response.startswith("get_torque "):
                        value_str = response.split(" ", 1)[1]
                        return float(value_str)
                    else:
                        return float(response)
                except (ValueError, IndexError) as e:
                    print(f"[DEBUG] Failed to parse torque response: {e}")
                    return None
        else:
            response = self._send_binary_command(CommandID.GET_TORQUE)
            if response and len(response) >= 2:
                value = struct.unpack('>h', response[:2])[0]
                return self._q88_to_float(value)
        return None
    
    def enable(self) -> bool:
        """
        Enable actuator motor.
        
        Returns:
            True if command sent successfully
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command("enable")
            print(f"[DEBUG] Enable response: '{response}'")
            # The firmware responds with "enable" on success
            return response == "enable"
        else:
            response = self._send_binary_command(CommandID.ENABLE)
            print(f"[DEBUG] Enable binary response: {response}")
            return response is not None
    
    def disable(self) -> bool:
        """
        Disable actuator motor.
        
        Returns:
            True if command sent successfully
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command("disable")
            print(f"[DEBUG] Disable response: '{response}'")
            # The firmware responds with "disable" on success
            return response == "disable"
        else:
            response = self._send_binary_command(CommandID.DISABLE)
            print(f"[DEBUG] Disable binary response: {response}")
            return response is not None
    
    def home(self) -> bool:
        """
        Move actuator to home position.
        
        Returns:
            True if command sent successfully
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command("home")
            return response is not None
        else:
            response = self._send_binary_command(CommandID.HOME)
            return response is not None
    
    def stop(self) -> bool:
        """
        Stop actuator movement immediately.
        
        Returns:
            True if command sent successfully
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command("stop")
            return response is not None
        else:
            response = self._send_binary_command(CommandID.STOP)
            return response is not None
    
    def set_command_mode(self, mode: CommandMode) -> bool:
        """
        Set the command communication mode.
        
        Args:
            mode: Command mode to use
            
        Returns:
            True if command sent successfully
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command(f"cmd_mode {mode.value}")
            if response is not None:
                self.command_mode = mode
            return response is not None
        else:
            data = struct.pack('>h', mode.value)
            response = self._send_binary_command(CommandID.CMD_MODE, data)
            if response is not None:
                self.command_mode = mode
            return response is not None
    
    def set_broadcast_frequency(self, frequency: float) -> bool:
        """
        Set the broadcast frequency for position, velocity, and torque data.
        
        Args:
            frequency: Broadcast frequency in Hz (0 to disable broadcast)
            
        Returns:
            True if command sent successfully
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command(f"broadcast {frequency}")
            print(f"[DEBUG] Set broadcast response: '{response}'")
            # The firmware should respond with "broadcast <frequency>"
            if response and response.startswith("broadcast "):
                try:
                    # Extract the value to verify it was set correctly
                    value_str = response.split(" ", 1)[1]
                    set_value = float(value_str)
                    print(f"[DEBUG] Broadcast frequency set to: {set_value} Hz")
                    return True
                except (ValueError, IndexError) as e:
                    print(f"[DEBUG] Failed to parse broadcast response: {e}")
                    return False
            return response is not None
        else:
            data = struct.pack('>h', self._float_to_q88(frequency))
            response = self._send_binary_command(CommandID.BROADCAST, data)
            print(f"[DEBUG] Broadcast binary response: {response}")
            return response is not None
    
    def get_velocity_pid(self) -> Optional[Tuple[float, float, float]]:
        """
        Get current velocity PID parameters.
        
        Returns:
            Tuple of (P, I, D) values or None if failed
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command("get_velocity_pid")
            print(f"[DEBUG] Get velocity PID response: '{response}'")
            if response and response.startswith("get_velocity_pid "):
                try:
                    # Parse "get_velocity_pid P I D"
                    parts = response.split()
                    if len(parts) >= 4:
                        p = float(parts[1])
                        i = float(parts[2])
                        d = float(parts[3])
                        return (p, i, d)
                except (ValueError, IndexError) as e:
                    print(f"[DEBUG] Failed to parse velocity PID response: {e}")
            return None
        else:
            # Binary mode not implemented for PID commands yet
            return None
    
    def set_velocity_pid(self, p: float, i: float, d: float) -> bool:
        """
        Set velocity PID parameters.
        
        Args:
            p: Proportional gain
            i: Integral gain
            d: Derivative gain
            
        Returns:
            True if command sent successfully
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command(f"set_velocity_pid {p} {i} {d}")
            print(f"[DEBUG] Set velocity PID response: '{response}'")
            if response and response.startswith("set_velocity_pid "):
                try:
                    # Parse response to verify values were set
                    parts = response.split()
                    if len(parts) >= 4:
                        set_p = float(parts[1])
                        set_i = float(parts[2])
                        set_d = float(parts[3])
                        print(f"[DEBUG] Velocity PID set to: P={set_p}, I={set_i}, D={set_d}")
                        return True
                except (ValueError, IndexError) as e:
                    print(f"[DEBUG] Failed to parse set velocity PID response: {e}")
                    return False
            return response is not None
        else:
            # Binary mode not implemented for PID commands yet
            return False
    
    def get_angle_pid(self) -> Optional[Tuple[float, float, float]]:
        """
        Get current angle PID parameters.
        
        Returns:
            Tuple of (P, I, D) values or None if failed
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command("get_angle_pid")
            print(f"[DEBUG] Get angle PID response: '{response}'")
            if response and response.startswith("get_angle_pid "):
                try:
                    # Parse "get_angle_pid P I D"
                    parts = response.split()
                    if len(parts) >= 4:
                        p = float(parts[1])
                        i = float(parts[2])
                        d = float(parts[3])
                        return (p, i, d)
                except (ValueError, IndexError) as e:
                    print(f"[DEBUG] Failed to parse angle PID response: {e}")
            return None
        else:
            # Binary mode not implemented for PID commands yet
            return None
    
    def set_angle_pid(self, p: float, i: float, d: float) -> bool:
        """
        Set angle PID parameters.
        
        Args:
            p: Proportional gain
            i: Integral gain
            d: Derivative gain
            
        Returns:
            True if command sent successfully
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command(f"set_angle_pid {p} {i} {d}")
            print(f"[DEBUG] Set angle PID response: '{response}'")
            if response and response.startswith("set_angle_pid "):
                try:
                    # Parse response to verify values were set
                    parts = response.split()
                    if len(parts) >= 4:
                        set_p = float(parts[1])
                        set_i = float(parts[2])
                        set_d = float(parts[3])
                        print(f"[DEBUG] Angle PID set to: P={set_p}, I={set_i}, D={set_d}")
                        return True
                except (ValueError, IndexError) as e:
                    print(f"[DEBUG] Failed to parse set angle PID response: {e}")
                    return False
            return response is not None
        else:
            # Binary mode not implemented for PID commands yet
            return False
    
    def get_current_pid(self) -> Optional[Tuple[float, float, float]]:
        """
        Get current current PID parameters.
        
        Returns:
            Tuple of (P, I, D) values or None if failed
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command("get_current_pid")
            print(f"[DEBUG] Get current PID response: '{response}'")
            if response and response.startswith("get_current_pid "):
                try:
                    # Parse "get_current_pid P I D"
                    parts = response.split()
                    if len(parts) >= 4:
                        p = float(parts[1])
                        i = float(parts[2])
                        d = float(parts[3])
                        return (p, i, d)
                except (ValueError, IndexError) as e:
                    print(f"[DEBUG] Failed to parse current PID response: {e}")
            return None
        else:
            # Binary mode not implemented for PID commands yet
            return None
    
    def set_current_pid(self, p: float, i: float, d: float) -> bool:
        """
        Set current PID parameters.
        
        Args:
            p: Proportional gain
            i: Integral gain
            d: Derivative gain
            
        Returns:
            True if command sent successfully
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command(f"set_current_pid {p} {i} {d}")
            print(f"[DEBUG] Set current PID response: '{response}'")
            if response and response.startswith("set_current_pid "):
                try:
                    # Parse response to verify values were set
                    parts = response.split()
                    if len(parts) >= 4:
                        set_p = float(parts[1])
                        set_i = float(parts[2])
                        set_d = float(parts[3])
                        print(f"[DEBUG] Current PID set to: P={set_p}, I={set_i}, D={set_d}")
                        return True
                except (ValueError, IndexError) as e:
                    print(f"[DEBUG] Failed to parse set current PID response: {e}")
                    return False
            return response is not None
        else:
            # Binary mode not implemented for PID commands yet
            return False
    
    def save_config(self) -> bool:
        """
        Save current configuration to EEPROM.
        
        Returns:
            True if command sent successfully
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command("save_config")
            print(f"[DEBUG] Save config response: '{response}'")
            return response == "save_config"
        else:
            # Binary mode not implemented for save_config yet
            return False
    
    def get_downsample(self) -> Optional[int]:
        """
        Get current motion downsampling value.
        
        Returns:
            Current downsampling value or None if failed
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command("get_downsample")
            print(f"[DEBUG] Get downsample response: '{response}'")
            if response and response.startswith("get_downsample "):
                try:
                    value_str = response.split(" ", 1)[1]
                    return int(value_str)
                except (ValueError, IndexError) as e:
                    print(f"[DEBUG] Failed to parse downsample response: {e}")
                    return None
            return None
        else:
            # Binary mode not implemented for downsample commands yet
            return None
    
    def set_downsample(self, downsample: int) -> bool:
        """
        Set motion downsampling value.
        
        Args:
            downsample: Downsampling factor (1 = every loop, 2 = every other loop, etc.)
            
        Returns:
            True if command sent successfully
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command(f"set_downsample {downsample}")
            print(f"[DEBUG] Set downsample response: '{response}'")
            if response and response.startswith("set_downsample "):
                try:
                    value_str = response.split(" ", 1)[1]
                    set_value = int(value_str)
                    print(f"[DEBUG] Downsample set to: {set_value}")
                    return True
                except (ValueError, IndexError) as e:
                    print(f"[DEBUG] Failed to parse set downsample response: {e}")
                    return False
            return response is not None
        else:
            # Binary mode not implemented for downsample commands yet
            return False
    
    def get_temperature(self) -> Optional[float]:
        """
        Get current board temperature.
        
        Returns:
            Current temperature in Celsius or None if failed
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command("get_temperature")
            print(f"[DEBUG] Get temperature response: '{response}'")
            if response and response.startswith("get_temperature "):
                try:
                    value_str = response.split(" ", 1)[1]
                    return float(value_str)
                except (ValueError, IndexError) as e:
                    print(f"[DEBUG] Failed to parse temperature response: {e}")
                    return None
            return None
        else:
            # Binary mode not implemented for temperature commands yet
            return None
    
    def get_bus_voltage(self) -> Optional[float]:
        """
        Get current bus voltage.
        
        Returns:
            Current bus voltage in Volts or None if failed
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command("get_bus_voltage")
            print(f"[DEBUG] Get bus voltage response: '{response}'")
            if response and response.startswith("get_bus_voltage "):
                try:
                    value_str = response.split(" ", 1)[1]
                    return float(value_str)
                except (ValueError, IndexError) as e:
                    print(f"[DEBUG] Failed to parse bus voltage response: {e}")
                    return None
            return None
        else:
            # Binary mode not implemented for bus voltage commands yet
            return None
    
    def get_internal_temperature(self) -> Optional[float]:
        """
        Get current internal STM32 temperature.
        
        Returns:
            Current internal temperature in Celsius or None if failed
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command("get_internal_temperature")
            print(f"[DEBUG] Get internal temperature response: '{response}'")
            if response and response.startswith("get_internal_temperature "):
                try:
                    value_str = response.split(" ", 1)[1]
                    return float(value_str)
                except (ValueError, IndexError) as e:
                    print(f"[DEBUG] Failed to parse internal temperature response: {e}")
                    return None
            return None
        else:
            # Binary mode not implemented for internal temperature commands yet
            return None
    
    def recalibrate_sensors(self) -> bool:
        """
        Recalibrate the actuator sensors.
        
        Returns:
            True if command sent successfully
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command("recalibrate_sensors")
            print(f"[DEBUG] Recalibrate sensors response: '{response}'")
            # The firmware responds with multiple lines during calibration
            # We consider it successful if we get any response
            return response is not None
        else:
            # Binary mode not implemented for recalibrate_sensors yet
            return False

