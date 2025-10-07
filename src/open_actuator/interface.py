import serial
import time
import struct
from typing import Optional, Tuple, Dict
from abc import ABC, abstractmethod
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
    RESET_POSITION = 0x0B
    GET_CURRENT_A = 0x0C
    GET_CURRENT_B = 0x0D
    GET_CURRENT_C = 0x0E
    CMD_MODE = 0xAB
    BROADCAST = 0xAC


class CommandMode(IntEnum):
    """Command communication modes."""
    HUMAN_READABLE = 1
    HIGH_SPEED_BINARY = 2
    SIMPLEFOC = 3


class Interface(ABC):
    """Abstract base class for actuator interfaces."""
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to the actuator interface."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the actuator interface."""
        pass

    @abstractmethod
    def send_command(self, command: str) -> Optional[str]:
        """Send a command to the actuator."""
        pass
    
    @abstractmethod
    def get_position(self) -> Optional[float]:
        """Get current actuator position."""
        pass

    @abstractmethod
    def get_velocity(self) -> Optional[float]:
        """Get current actuator velocity."""
        pass

    @abstractmethod
    def get_torque(self) -> Optional[float]:
        """Get current actuator torque."""
        pass

    @abstractmethod
    def set_position(self, position: float) -> bool:
        """Set actuator position."""
        pass

    @abstractmethod
    def set_velocity(self, velocity: float) -> bool:
        """Set actuator velocity."""
        pass

    @abstractmethod
    def set_torque(self, torque: float) -> bool:
        """Set actuator torque."""
        pass

    @abstractmethod
    def enable(self) -> bool:
        """Enable the actuator."""
        pass

    @abstractmethod
    def disable(self) -> bool:
        """Disable the actuator."""
        pass
        
    @abstractmethod
    def home(self) -> bool:
        """Home the actuator."""
        pass

    @abstractmethod
    def stop(self) -> bool:
        """Stop the actuator."""
        pass


class USBInterface(Interface):
    """
    USB serial interface implementation.
    
    Provides complete USB serial communication with actuators,
    including all control methods and extended functionality.
    """
    
    def __init__(self, port: str, baudrate: int = 2000000, timeout: float = 1.0):
        """
        Initialize USB interface.
        
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
            return None
            
        try:
            self.serial_conn.write(f"{command}\n".encode())
            self.serial_conn.flush()  # Ensure data is sent
            
            # Wait a bit for response
            time.sleep(0.1)
            
            # Read response with timeout
            response = self.serial_conn.readline().decode().strip()
            return response
        except (serial.SerialException, UnicodeDecodeError) as e:
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

    def send_command(self, command: str) -> Optional[str]:
        """Send a command to the actuator."""
        return self._send_human_command(command)
    
    def get_position(self) -> Optional[float]:
        """
        Get current actuator position.
        
        Returns:
            Current position in degrees or None if failed
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command("get_position")
            if response:
                try:
                    # The firmware responds with "get_position <value>"
                    if response.startswith("get_position "):
                        value_str = response.split(" ", 1)[1]
                        return float(value_str)
                    else:
                        return float(response)
                except (ValueError, IndexError) as e:
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
            if response:
                try:
                    # The firmware responds with "get_velocity <value>"
                    if response.startswith("get_velocity "):
                        value_str = response.split(" ", 1)[1]
                        return float(value_str)
                    else:
                        return float(response)
                except (ValueError, IndexError) as e:
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
            if response:
                try:
                    # The firmware responds with "get_torque <value>"
                    if response.startswith("get_torque "):
                        value_str = response.split(" ", 1)[1]
                        return float(value_str)
                    else:
                        return float(response)
                except (ValueError, IndexError) as e:
                    return None
        else:
            response = self._send_binary_command(CommandID.GET_TORQUE)
            if response and len(response) >= 2:
                value = struct.unpack('>h', response[:2])[0]
                return self._q88_to_float(value)
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
            # The firmware responds with "set_position <value>"
            if response and response.startswith("set_position "):
                try:
                    # Extract the value to verify it was set correctly
                    value_str = response.split(" ", 1)[1]
                    set_value = float(value_str)
                    return True
                except (ValueError, IndexError) as e:
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
            # The firmware responds with "set_velocity <value>"
            if response and response.startswith("set_velocity "):
                try:
                    # Extract the value to verify it was set correctly
                    value_str = response.split(" ", 1)[1]
                    set_value = float(value_str)
                    return True
                except (ValueError, IndexError) as e:
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
            # The firmware responds with "set_torque <value>"
            if response and response.startswith("set_torque "):
                try:
                    # Extract the value to verify it was set correctly
                    value_str = response.split(" ", 1)[1]
                    set_value = float(value_str)
                    return True
                except (ValueError, IndexError) as e:
                    return False
            return response is not None
        else:
            data = struct.pack('>h', self._float_to_q88(torque))
            response = self._send_binary_command(CommandID.SET_TORQUE, data)
            return response is not None

    def enable(self) -> bool:
        """
        Enable actuator motor.
        
        Returns:
            True if command sent successfully
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command("enable")
            # The firmware responds with "enable" on success
            return response == "enable"
        else:
            response = self._send_binary_command(CommandID.ENABLE)
            return response is not None

    def disable(self) -> bool:
        """
        Disable actuator motor.
        
        Returns:
            True if command sent successfully
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command("disable")
            # The firmware responds with "disable" on success
            return response == "disable"
        else:
            response = self._send_binary_command(CommandID.DISABLE)
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

    def reset_position(self) -> bool:
        """
        Reset the actuator position to zero without changing the target.
        This sets the current position as the new zero reference.
        
        Returns:
            True if command sent successfully
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command("reset_position")
            return response == "reset_position"
        else:
            response = self._send_binary_command(CommandID.RESET_POSITION)
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


    def get_velocity_pid(self) -> Optional[Tuple[float, float, float]]:
        """
        Get current velocity PID parameters.
        
        Returns:
            Tuple of (P, I, D) values or None if failed
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command("get_velocity_pid")
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
                    ...
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
            if response and response.startswith("set_velocity_pid "):
                try:
                    # Parse response to verify values were set
                    parts = response.split()
                    if len(parts) >= 4:
                        set_p = float(parts[1])
                        set_i = float(parts[2])
                        set_d = float(parts[3])
                        return True
                except (ValueError, IndexError) as e:
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
                    ...
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
            if response and response.startswith("set_angle_pid "):
                try:
                    # Parse response to verify values were set
                    parts = response.split()
                    if len(parts) >= 4:
                        set_p = float(parts[1])
                        set_i = float(parts[2])
                        set_d = float(parts[3])
                        return True
                except (ValueError, IndexError) as e:
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
                    ...
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
            if response and response.startswith("set_current_pid "):
                try:
                    # Parse response to verify values were set
                    parts = response.split()
                    if len(parts) >= 4:
                        set_p = float(parts[1])
                        set_i = float(parts[2])
                        set_d = float(parts[3])
                        return True
                except (ValueError, IndexError) as e:
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
            if response and response.startswith("get_downsample "):
                try:
                    value_str = response.split(" ", 1)[1]
                    return int(value_str)
                except (ValueError, IndexError) as e:
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
            if response and response.startswith("set_downsample "):
                try:
                    value_str = response.split(" ", 1)[1]
                    set_value = int(value_str)
                    return True
                except (ValueError, IndexError) as e:
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
            if response and response.startswith("get_temperature "):
                try:
                    value_str = response.split(" ", 1)[1]
                    return float(value_str)
                except (ValueError, IndexError) as e:
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
            if response and response.startswith("get_bus_voltage "):
                try:
                    value_str = response.split(" ", 1)[1]
                    return float(value_str)
                except (ValueError, IndexError) as e:
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
            if response and response.startswith("get_internal_temperature "):
                try:
                    value_str = response.split(" ", 1)[1]
                    return float(value_str)
                except (ValueError, IndexError) as e:
                    return None
            return None
        else:
            # Binary mode not implemented for internal temperature commands yet
            return None

    def get_current_a(self) -> Optional[float]:
        """
        Get current phase A current.
        
        Returns:
            Current phase A current in Amperes or None if failed
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command("get_current_a")
            if response and response.startswith("get_current_a "):
                try:
                    value_str = response.split(" ", 1)[1]
                    return float(value_str)
                except (ValueError, IndexError) as e:
                    return None
            return None
        else:
            response = self._send_binary_command(CommandID.GET_CURRENT_A)
            if response and len(response) >= 4:
                value = struct.unpack('>f', response[:4])[0]
                return value
            return None

    def get_current_b(self) -> Optional[float]:
        """
        Get current phase B current.
        
        Returns:
            Current phase B current in Amperes or None if failed
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command("get_current_b")
            if response and response.startswith("get_current_b "):
                try:
                    value_str = response.split(" ", 1)[1]
                    return float(value_str)
                except (ValueError, IndexError) as e:
                    return None
            return None
        else:
            response = self._send_binary_command(CommandID.GET_CURRENT_B)
            if response and len(response) >= 4:
                value = struct.unpack('>f', response[:4])[0]
                return value
            return None

    def get_current_c(self) -> Optional[float]:
        """
        Get current phase C current.
        
        Returns:
            Current phase C current in Amperes or None if failed
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command("get_current_c")
            if response and response.startswith("get_current_c "):
                try:
                    value_str = response.split(" ", 1)[1]
                    return float(value_str)
                except (ValueError, IndexError) as e:
                    return None
            return None
        else:
            response = self._send_binary_command(CommandID.GET_CURRENT_C)
            if response and len(response) >= 4:
                value = struct.unpack('>f', response[:4])[0]
                return value
            return None

    def recalibrate_sensors(self) -> bool:
        """
        Recalibrate the actuator sensors.
        
        Returns:
            True if command sent successfully
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command("recalibrate_sensors")
            # The firmware responds with multiple lines during calibration
            # We consider it successful if we get any response
            return response is not None
        else:
            # Binary mode not implemented for recalibrate_sensors yet
            return False

    def get_pole_pairs(self) -> Optional[int]:
        """
        Get current number of pole pairs.
        
        Returns:
            Current number of pole pairs or None if failed
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command("get_pole_pairs")
            if response and response.startswith("get_pole_pairs "):
                try:
                    value_str = response.split(" ", 1)[1]
                    return int(value_str)
                except (ValueError, IndexError) as e:
                    return None
            return None
        else:
            # Binary mode not implemented for pole pairs commands yet
            return None

    def set_pole_pairs(self, pole_pairs: int) -> bool:
        """
        Set number of pole pairs.
        
        Args:
            pole_pairs: Number of pole pairs (1-50)
            
        Returns:
            True if command sent successfully
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command(f"set_pole_pairs {pole_pairs}")
            if response and response.startswith("set_pole_pairs "):
                try:
                    # Parse response to verify value was set
                    value_str = response.split(" ", 1)[1]
                    set_value = int(value_str)
                    return True
                except (ValueError, IndexError) as e:
                    return False
            return response is not None
        else:
            # Binary mode not implemented for pole pairs commands yet
            return False

    def get_full_state(self) -> Optional[Dict[str, float]]:
        """
        Get full actuator state including position, velocity, torque, and status.
        
        Returns:
            Dictionary with state data or None if failed
        """
        if self.command_mode == CommandMode.HUMAN_READABLE:
            response = self._send_human_command("get_full_state")
            if response and response.startswith("full_state "):
                try:
                    # Parse "full_state pos vel torque temp voltage int_temp current_a current_b current_c"
                    parts = response.split()
                    if len(parts) >= 10:
                        return {
                            'position': float(parts[1]),
                            'velocity': float(parts[2]),
                            'torque': float(parts[3]),
                            'temperature': float(parts[4]),
                            'bus_voltage': float(parts[5]),
                            'internal_temperature': float(parts[6]),
                            'current_a': float(parts[7]),
                            'current_b': float(parts[8]),
                            'current_c': float(parts[9])
                        }
                except (ValueError, IndexError) as e:
                    ...
            return None
        else:
            # Binary mode not implemented for get_full_state yet
            return None


class SerialInterface(Interface):
    """Serial interface implementation."""
    pass


class CANInterface(Interface):
    """CAN interface implementation."""
    pass