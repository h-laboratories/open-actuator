from open_actuator.interface import Interface


class Actuator:
    interface: Interface

    def __init__(self, interface: Interface):
        self.interface = interface
        ...

    def connect(self) -> bool:
        return self.interface.connect()

    def disconnect(self) -> bool:
        return self.interface.disconnect()

    def send_command(self, command: str):
        self.interface.send_command(command)

    def get_position(self):
        raise NotImplementedError("Subclass must implement get_position")

    def get_velocity(self):
        raise NotImplementedError("Subclass must implement get_velocity")

    def get_torque(self):
        raise NotImplementedError("Subclass must implement get_torque")

    def set_position(self, position: float):
        raise NotImplementedError("Subclass must implement set_position")

    def set_velocity(self, velocity: float):
        raise NotImplementedError("Subclass must implement set_velocity")
        
    def set_torque(self, torque: float):
        raise NotImplementedError("Subclass must implement set_torque")

    def enable(self):
        raise NotImplementedError("Subclass must implement enable")
        
    def disable(self):
        raise NotImplementedError("Subclass must implement disable")

    def home(self):
        raise NotImplementedError("Subclass must implement home")
        
    def stop(self):
        raise NotImplementedError("Subclass must implement stop")

    
        
        
        