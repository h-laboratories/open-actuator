class Command:
    arguments: dict
    def __init__(self, command: str, **arguments: dict):
        self.command = command
        self.arguments = arguments

class SetPositionCommand(Command):
    def __init__(self, position: float):
        super().__init__("set_position", position=position)

class SetVelocityCommand(Command):
    def __init__(self, velocity: float):
        super().__init__("set_velocity", velocity=velocity)

class SetTorqueCommand(Command):
    def __init__(self, torque: float):
        super().__init__("set_torque", torque=torque)

class GetPositionCommand(Command):
    def __init__(self):
        super().__init__("get_position")

class GetVelocityCommand(Command):
    def __init__(self):
        super().__init__("get_velocity")

class GetTorqueCommand(Command):
    def __init__(self):
        super().__init__("get_torque")

class EnableCommand(Command):
    def __init__(self):
        super().__init__("enable")

class DisableCommand(Command):
    def __init__(self):
        super().__init__("disable")

class HomeCommand(Command):
    def __init__(self):
        super().__init__("home")

class StopCommand(Command):
    def __init__(self):
        super().__init__("stop")

        