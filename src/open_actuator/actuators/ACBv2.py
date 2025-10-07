from typing import Optional, Tuple, Dict
from open_actuator.actuators.Actuator import Actuator
from open_actuator.interface import USBInterface


class ACBv2(Actuator):
    """
    ACB v2.0 actuator implementation.
    
    This class provides a complete interface for controlling ACB v2.0 actuators
    with state management and all required control methods.
    """
    
    def __init__(self, interface: USBInterface):
        """
        Initialize ACB v2.0 actuator.
        
        Args:
            interface: USB interface for communication
        """
        super().__init__(interface)
        
        # Current actuator state
        self._position: Optional[float] = None
        self._velocity: Optional[float] = None
        self._torque: Optional[float] = None
        self._temperature: Optional[float] = None
        self._bus_voltage: Optional[float] = None
        self._internal_temperature: Optional[float] = None
        self._enabled: bool = False
        
        # PID parameters
        self._velocity_pid: Optional[Tuple[float, float, float]] = None
        self._angle_pid: Optional[Tuple[float, float, float]] = None
        self._current_pid: Optional[Tuple[float, float, float]] = None
        
        # Configuration
        self._downsample: Optional[int] = None

    def get_position(self) -> Optional[float]:
        """
        Get current actuator position.
        
        Returns:
            Current position in degrees or None if failed
        """
        position = self.interface.get_position()
        if position is not None:
            self._position = position
        return position

    def get_velocity(self) -> Optional[float]:
        """
        Get current actuator velocity.
        
        Returns:
            Current velocity in degrees/second or None if failed
        """
        velocity = self.interface.get_velocity()
        if velocity is not None:
            self._velocity = velocity
        return velocity

    def get_torque(self) -> Optional[float]:
        """
        Get current actuator torque.
        
        Returns:
            Current torque in Nm or None if failed
        """
        torque = self.interface.get_torque()
        if torque is not None:
            self._torque = torque
        return torque

    def set_position(self, position: float) -> bool:
        """
        Set actuator position.
        
        Args:
            position: Target position in degrees
            
        Returns:
            True if command sent successfully
        """
        return self.interface.set_position(position)

    def set_velocity(self, velocity: float) -> bool:
        """
        Set actuator velocity.
        
        Args:
            velocity: Target velocity in degrees/second
            
        Returns:
            True if command sent successfully
        """
        return self.interface.set_velocity(velocity)

    def set_torque(self, torque: float) -> bool:
        """
        Set actuator torque.
        
        Args:
            torque: Target torque in Nm
            
        Returns:
            True if command sent successfully
        """
        return self.interface.set_torque(torque)

    def enable(self) -> bool:
        """
        Enable the actuator.
        
        Returns:
            True if command sent successfully
        """
        success = self.interface.enable()
        if success:
            self._enabled = True
        return success

    def disable(self) -> bool:
        """
        Disable the actuator.
        
        Returns:
            True if command sent successfully
        """
        success = self.interface.disable()
        if success:
            self._enabled = False
        return success

    def home(self) -> bool:
        """
        Home the actuator.
        
        Returns:
            True if command sent successfully
        """
        return self.interface.home()

    def stop(self) -> bool:
        """
        Stop the actuator.
        
        Returns:
            True if command sent successfully
        """
        return self.interface.stop()

    def reset_position(self) -> bool:
        """
        Reset the actuator position to zero without changing the target.
        This sets the current position as the new zero reference.
        
        Returns:
            True if command sent successfully
        """
        return self.interface.reset_position()

    def get_temperature(self) -> Optional[float]:
        """
        Get current board temperature.
        
        Returns:
            Current temperature in Celsius or None if failed
        """
        temperature = self.interface.get_temperature()
        if temperature is not None:
            self._temperature = temperature
        return temperature

    def get_bus_voltage(self) -> Optional[float]:
        """
        Get current bus voltage.
        
        Returns:
            Current bus voltage in Volts or None if failed
        """
        bus_voltage = self.interface.get_bus_voltage()
        if bus_voltage is not None:
            self._bus_voltage = bus_voltage
        return bus_voltage

    def get_internal_temperature(self) -> Optional[float]:
        """
        Get current internal STM32 temperature.
        
        Returns:
            Current internal temperature in Celsius or None if failed
        """
        internal_temperature = self.interface.get_internal_temperature()
        if internal_temperature is not None:
            self._internal_temperature = internal_temperature
        return internal_temperature

    def get_current_a(self) -> Optional[float]:
        """
        Get current phase A current.
        
        Returns:
            Current phase A current in Amperes or None if failed
        """
        return self.interface.get_current_a()

    def get_current_b(self) -> Optional[float]:
        """
        Get current phase B current.
        
        Returns:
            Current phase B current in Amperes or None if failed
        """
        return self.interface.get_current_b()

    def get_current_c(self) -> Optional[float]:
        """
        Get current phase C current.
        
        Returns:
            Current phase C current in Amperes or None if failed
        """
        return self.interface.get_current_c()

    def get_velocity_pid(self) -> Optional[Tuple[float, float, float]]:
        """
        Get current velocity PID parameters.
        
        Returns:
            Tuple of (P, I, D) values or None if failed
        """
        pid_values = self.interface.get_velocity_pid()
        if pid_values is not None:
            self._velocity_pid = pid_values
        return pid_values

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
        success = self.interface.set_velocity_pid(p, i, d)
        if success:
            self._velocity_pid = (p, i, d)
        return success

    def get_angle_pid(self) -> Optional[Tuple[float, float, float]]:
        """
        Get current angle PID parameters.
        
        Returns:
            Tuple of (P, I, D) values or None if failed
        """
        pid_values = self.interface.get_angle_pid()
        if pid_values is not None:
            self._angle_pid = pid_values
        return pid_values

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
        success = self.interface.set_angle_pid(p, i, d)
        if success:
            self._angle_pid = (p, i, d)
        return success

    def get_current_pid(self) -> Optional[Tuple[float, float, float]]:
        """
        Get current current PID parameters.
        
        Returns:
            Tuple of (P, I, D) values or None if failed
        """
        pid_values = self.interface.get_current_pid()
        if pid_values is not None:
            self._current_pid = pid_values
        return pid_values

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
        success = self.interface.set_current_pid(p, i, d)
        if success:
            self._current_pid = (p, i, d)
        return success

    def save_config(self) -> bool:
        """
        Save current configuration to EEPROM.
        
        Returns:
            True if command sent successfully
        """
        return self.interface.save_config()

    def get_downsample(self) -> Optional[int]:
        """
        Get current motion downsampling value.
        
        Returns:
            Current downsampling value or None if failed
        """
        downsample = self.interface.get_downsample()
        if downsample is not None:
            self._downsample = downsample
        return downsample

    def set_downsample(self, downsample: int) -> bool:
        """
        Set motion downsampling value.
        
        Args:
            downsample: Downsampling factor (1 = every loop, 2 = every other loop, etc.)
            
        Returns:
            True if command sent successfully
        """
        success = self.interface.set_downsample(downsample)
        if success:
            self._downsample = downsample
        return success


    def recalibrate_sensors(self) -> bool:
        """
        Recalibrate the actuator sensors.
        
        Returns:
            True if command sent successfully
        """
        return self.interface.recalibrate_sensors()

    def get_pole_pairs(self) -> Optional[int]:
        """
        Get current number of pole pairs.
        
        Returns:
            Current number of pole pairs or None if failed
        """
        pole_pairs = self.interface.get_pole_pairs()
        return pole_pairs

    def set_pole_pairs(self, pole_pairs: int) -> bool:
        """
        Set number of pole pairs.
        
        Args:
            pole_pairs: Number of pole pairs (1-50)
            
        Returns:
            True if command sent successfully
        """
        return self.interface.set_pole_pairs(pole_pairs)

    def get_full_state(self) -> Optional[Dict[str, float]]:
        """
        Get full actuator state including position, velocity, torque, and status.
        
        Returns:
            Dictionary with state data or None if failed
        """
        return self.interface.get_full_state()

    # State access methods
    @property
    def position(self) -> Optional[float]:
        """Get cached position value."""
        return self._position

    @property
    def velocity(self) -> Optional[float]:
        """Get cached velocity value."""
        return self._velocity

    @property
    def torque(self) -> Optional[float]:
        """Get cached torque value."""
        return self._torque

    @property
    def temperature(self) -> Optional[float]:
        """Get cached temperature value."""
        return self._temperature

    @property
    def bus_voltage(self) -> Optional[float]:
        """Get cached bus voltage value."""
        return self._bus_voltage

    @property
    def internal_temperature(self) -> Optional[float]:
        """Get cached internal temperature value."""
        return self._internal_temperature

    @property
    def enabled(self) -> bool:
        """Get cached enabled state."""
        return self._enabled

    @property
    def velocity_pid(self) -> Optional[Tuple[float, float, float]]:
        """Get cached velocity PID values."""
        return self._velocity_pid

    @property
    def angle_pid(self) -> Optional[Tuple[float, float, float]]:
        """Get cached angle PID values."""
        return self._angle_pid

    @property
    def current_pid(self) -> Optional[Tuple[float, float, float]]:
        """Get cached current PID values."""
        return self._current_pid

    @property
    def downsample(self) -> Optional[int]:
        """Get cached downsample value."""
        return self._downsample