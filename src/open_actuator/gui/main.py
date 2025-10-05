"""
Main GUI application for Open Actuator control.

This module provides the main GUI interface for controlling actuators
over USB serial connection.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from typing import Optional, Dict, Any
import serial.tools.list_ports

from ..interface import USBInterface, CommandMode
from ..actuators.ACBv2 import ACBv2
from .plotter import ActuatorPlotter


class ActuatorGUI:
    """
    Main GUI application for actuator control.
    
    Provides a comprehensive interface for controlling actuators with
    real-time monitoring and data visualization.
    """
    
    def __init__(self):
        """Initialize the GUI application."""
        self.root = tk.Tk()
        self.root.title("Open Actuator Control")
        self.root.geometry("1600x1000")
        self.root.configure(bg='#f0f0f0')
        
        # Actuator interface
        self.actuator: Optional[ACBv2] = None
        self.connected = False
        
        # Data monitoring
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Status monitoring
        self.status_monitoring = False
        self.status_thread: Optional[threading.Thread] = None
        
        # Broadcast monitoring
        self.broadcast_listening = False
        self.broadcast_thread: Optional[threading.Thread] = None
        
        # Data storage for plotting
        self.data_history = {
            'position': [],
            'velocity': [],
            'torque': [],
            'time': []
        }
        
        # Track unsaved changes
        self.unsaved_changes = {
            'velocity_pid': False,
            'angle_pid': False,
            'current_pid': False
        }
        
        # Plotter instance
        self.plotter: Optional[ActuatorPlotter] = None
        
        self.setup_ui()
        self.setup_styles()
        
    def setup_styles(self) -> None:
        """Configure GUI styles and themes."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure custom styles
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Heading.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Status.TLabel', font=('Arial', 10))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        style.configure('Unsaved.TEntry', fieldbackground='#ffffcc')  # Light yellow background
        
    def setup_ui(self) -> None:
        """Set up the main user interface."""
        # Main container with two columns
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for two columns
        self.root.columnconfigure(0, weight=1)  # Left column (controls)
        self.root.columnconfigure(1, weight=2)  # Right column (plot) - wider
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title spanning both columns
        title_label = ttk.Label(main_frame, text="Open Actuator Control", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Left column - Controls
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        left_frame.columnconfigure(0, weight=1)
        
        # Connection frame
        self.setup_connection_frame(left_frame, 0)
        
        # Control frame
        self.setup_control_frame(left_frame, 1)
        
        # PID Control frame
        self.setup_pid_frame(left_frame, 2)
        
        # Status frame
        self.setup_status_frame(left_frame, 3)
        
        # Log frame
        self.setup_log_frame(left_frame, 4)
        
        # Right column - Plot
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        
        # Plot frame
        self.setup_plot_frame(right_frame, 0)
        
    def setup_connection_frame(self, parent: ttk.Frame, row: int) -> None:
        """Set up the connection configuration frame."""
        conn_frame = ttk.LabelFrame(parent, text="Connection", padding="10")
        conn_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        conn_frame.columnconfigure(1, weight=1)
        
        # Port selection
        ttk.Label(conn_frame, text="Port:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(conn_frame, textvariable=self.port_var, width=20)
        self.port_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        # Refresh ports button
        ttk.Button(conn_frame, text="Refresh", command=self.refresh_ports).grid(row=0, column=2, padx=(5, 0))
        
        # Baud rate
        ttk.Label(conn_frame, text="Baud Rate:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.baudrate_var = tk.StringVar(value="2000000")
        baudrate_combo = ttk.Combobox(conn_frame, textvariable=self.baudrate_var, width=10)
        baudrate_combo['values'] = ('9600', '19200', '38400', '57600', '115200', '230400', '2000000')
        baudrate_combo.grid(row=1, column=1, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        
        # Command mode
        ttk.Label(conn_frame, text="Mode:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.mode_var = tk.StringVar(value="Human Readable")
        mode_combo = ttk.Combobox(conn_frame, textvariable=self.mode_var, width=15)
        mode_combo['values'] = ('Human Readable', 'High Speed Binary', 'SimpleFOC')
        mode_combo.grid(row=2, column=1, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        
        # Connect/Disconnect button
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=3, rowspan=3, padx=(10, 0), sticky=(tk.N, tk.S))
        
        # Test connection button
        ttk.Button(conn_frame, text="Test Connection", command=self.test_connection).grid(row=3, column=0, columnspan=3, pady=(5, 0))
        
        # Initial port refresh
        self.refresh_ports()
        
    def setup_control_frame(self, parent: ttk.Frame, row: int) -> None:
        """Set up the actuator control frame."""
        control_frame = ttk.LabelFrame(parent, text="Actuator Control", padding="10")
        control_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        control_frame.columnconfigure(1, weight=1)
        
        # Position control
        ttk.Label(control_frame, text="Position (deg):", style='Heading.TLabel').grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        pos_frame = ttk.Frame(control_frame)
        pos_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        pos_frame.columnconfigure(0, weight=1)
        
        self.position_var = tk.DoubleVar()
        position_scale = ttk.Scale(pos_frame, from_=-180, to=180, variable=self.position_var, orient=tk.HORIZONTAL)
        position_scale.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        position_entry = ttk.Entry(pos_frame, textvariable=self.position_var, width=10)
        position_entry.grid(row=0, column=1, padx=(5, 0))
        
        ttk.Button(pos_frame, text="Set Position", command=self.set_position).grid(row=0, column=2, padx=(10, 0))
        
        # Velocity control
        ttk.Label(control_frame, text="Velocity (deg/s):", style='Heading.TLabel').grid(row=2, column=0, sticky=tk.W, pady=(10, 5))
        vel_frame = ttk.Frame(control_frame)
        vel_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        vel_frame.columnconfigure(0, weight=1)
        
        self.velocity_var = tk.DoubleVar()
        velocity_scale = ttk.Scale(vel_frame, from_=-100, to=100, variable=self.velocity_var, orient=tk.HORIZONTAL)
        velocity_scale.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        velocity_entry = ttk.Entry(vel_frame, textvariable=self.velocity_var, width=10)
        velocity_entry.grid(row=0, column=1, padx=(5, 0))
        
        ttk.Button(vel_frame, text="Set Velocity", command=self.set_velocity).grid(row=0, column=2, padx=(10, 0))
        
        # Torque control
        ttk.Label(control_frame, text="Torque (Nm):", style='Heading.TLabel').grid(row=4, column=0, sticky=tk.W, pady=(10, 5))
        torque_frame = ttk.Frame(control_frame)
        torque_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        torque_frame.columnconfigure(0, weight=1)
        
        self.torque_var = tk.DoubleVar()
        torque_scale = ttk.Scale(torque_frame, from_=-10, to=10, variable=self.torque_var, orient=tk.HORIZONTAL)
        torque_scale.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        torque_entry = ttk.Entry(torque_frame, textvariable=self.torque_var, width=10)
        torque_entry.grid(row=0, column=1, padx=(5, 0))
        
        ttk.Button(torque_frame, text="Set Torque", command=self.set_torque).grid(row=0, column=2, padx=(10, 0))
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Button(button_frame, text="Enable", command=self.enable_actuator).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="Disable", command=self.disable_actuator).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(button_frame, text="Home", command=self.home_actuator).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(button_frame, text="Stop", command=self.stop_actuator).grid(row=0, column=3, padx=(0, 5))
        
        # Calibration button
        ttk.Button(button_frame, text="Recalibrate Sensors", command=self.recalibrate_sensors).grid(row=1, column=0, columnspan=2, pady=(5, 0), padx=(0, 5))
        
        # Monitoring controls
        monitor_frame = ttk.Frame(control_frame)
        monitor_frame.grid(row=7, column=0, columnspan=3, pady=(10, 0))
        
        self.monitor_btn = ttk.Button(monitor_frame, text="Start Monitoring", command=self.toggle_monitoring)
        self.monitor_btn.grid(row=0, column=0, padx=(0, 5))
        
        ttk.Button(monitor_frame, text="Get Position", command=self.get_position).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(monitor_frame, text="Get Velocity", command=self.get_velocity).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(monitor_frame, text="Get Torque", command=self.get_torque).grid(row=0, column=3, padx=(0, 5))
        
        # Second row for additional monitoring buttons
        ttk.Button(monitor_frame, text="Get Temperature", command=self.get_temperature).grid(row=1, column=0, padx=(0, 5), pady=(5, 0))
        ttk.Button(monitor_frame, text="Get Bus Voltage", command=self.get_bus_voltage).grid(row=1, column=1, padx=(0, 5), pady=(5, 0))
        ttk.Button(monitor_frame, text="Get Internal Temp", command=self.get_internal_temperature).grid(row=1, column=2, padx=(0, 5), pady=(5, 0))
        
        # Broadcast controls
        broadcast_frame = ttk.Frame(control_frame)
        broadcast_frame.grid(row=8, column=0, columnspan=3, pady=(10, 0))
        broadcast_frame.columnconfigure(1, weight=1)
        
        ttk.Label(broadcast_frame, text="Broadcast (Hz):", style='Heading.TLabel').grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.broadcast_freq_var = tk.DoubleVar(value=0.0)
        broadcast_scale = ttk.Scale(broadcast_frame, from_=0, to=50, variable=self.broadcast_freq_var, orient=tk.HORIZONTAL)
        broadcast_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        broadcast_entry = ttk.Entry(broadcast_frame, textvariable=self.broadcast_freq_var, width=8)
        broadcast_entry.grid(row=0, column=2, padx=(0, 5))
        
        ttk.Button(broadcast_frame, text="Set Broadcast", command=self.set_broadcast).grid(row=0, column=3, padx=(0, 5))
        ttk.Button(broadcast_frame, text="Stop Broadcast", command=self.stop_broadcast).grid(row=0, column=4, padx=(0, 5))
        
    def setup_pid_frame(self, parent: ttk.Frame, row: int) -> None:
        """Set up the PID control frame."""
        pid_frame = ttk.LabelFrame(parent, text="PID Control", padding="10")
        pid_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        pid_frame.columnconfigure(1, weight=1)
        
        # Velocity PID
        ttk.Label(pid_frame, text="Velocity PID:", style='Heading.TLabel').grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        vel_pid_frame = ttk.Frame(pid_frame)
        vel_pid_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        vel_pid_frame.columnconfigure(1, weight=1)
        vel_pid_frame.columnconfigure(3, weight=1)
        vel_pid_frame.columnconfigure(5, weight=1)
        
        # Velocity P
        ttk.Label(vel_pid_frame, text="P:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.vel_p_var = tk.DoubleVar(value=1.0)
        vel_p_entry = ttk.Entry(vel_pid_frame, textvariable=self.vel_p_var, width=8)
        vel_p_entry.grid(row=0, column=1, padx=(0, 10))
        
        # Velocity I
        ttk.Label(vel_pid_frame, text="I:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.vel_i_var = tk.DoubleVar(value=0.0)
        vel_i_entry = ttk.Entry(vel_pid_frame, textvariable=self.vel_i_var, width=8)
        vel_i_entry.grid(row=0, column=3, padx=(0, 10))
        
        # Velocity D
        ttk.Label(vel_pid_frame, text="D:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        self.vel_d_var = tk.DoubleVar(value=0.0)
        vel_d_entry = ttk.Entry(vel_pid_frame, textvariable=self.vel_d_var, width=8)
        vel_d_entry.grid(row=0, column=5, padx=(0, 10))
        
        ttk.Button(vel_pid_frame, text="Get", command=self.get_velocity_pid).grid(row=0, column=6, padx=(5, 5))
        ttk.Button(vel_pid_frame, text="Set", command=self.set_velocity_pid).grid(row=0, column=7, padx=(0, 5))
        
        # Angle PID
        ttk.Label(pid_frame, text="Angle PID:", style='Heading.TLabel').grid(row=2, column=0, sticky=tk.W, pady=(10, 5))
        angle_pid_frame = ttk.Frame(pid_frame)
        angle_pid_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        angle_pid_frame.columnconfigure(1, weight=1)
        angle_pid_frame.columnconfigure(3, weight=1)
        angle_pid_frame.columnconfigure(5, weight=1)
        
        # Angle P
        ttk.Label(angle_pid_frame, text="P:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.angle_p_var = tk.DoubleVar(value=20.0)
        angle_p_entry = ttk.Entry(angle_pid_frame, textvariable=self.angle_p_var, width=8)
        angle_p_entry.grid(row=0, column=1, padx=(0, 10))
        
        # Angle I
        ttk.Label(angle_pid_frame, text="I:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.angle_i_var = tk.DoubleVar(value=0.0)
        angle_i_entry = ttk.Entry(angle_pid_frame, textvariable=self.angle_i_var, width=8)
        angle_i_entry.grid(row=0, column=3, padx=(0, 10))
        
        # Angle D
        ttk.Label(angle_pid_frame, text="D:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        self.angle_d_var = tk.DoubleVar(value=0.0)
        angle_d_entry = ttk.Entry(angle_pid_frame, textvariable=self.angle_d_var, width=8)
        angle_d_entry.grid(row=0, column=5, padx=(0, 10))
        
        ttk.Button(angle_pid_frame, text="Get", command=self.get_angle_pid).grid(row=0, column=6, padx=(5, 5))
        ttk.Button(angle_pid_frame, text="Set", command=self.set_angle_pid).grid(row=0, column=7, padx=(0, 5))
        
        # Current PID
        ttk.Label(pid_frame, text="Current PID:", style='Heading.TLabel').grid(row=4, column=0, sticky=tk.W, pady=(10, 5))
        current_pid_frame = ttk.Frame(pid_frame)
        current_pid_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        current_pid_frame.columnconfigure(1, weight=1)
        current_pid_frame.columnconfigure(3, weight=1)
        current_pid_frame.columnconfigure(5, weight=1)
        
        # Current P
        ttk.Label(current_pid_frame, text="P:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.current_p_var = tk.DoubleVar(value=0.5)
        current_p_entry = ttk.Entry(current_pid_frame, textvariable=self.current_p_var, width=8)
        current_p_entry.grid(row=0, column=1, padx=(0, 10))
        
        # Current I
        ttk.Label(current_pid_frame, text="I:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.current_i_var = tk.DoubleVar(value=10.0)
        current_i_entry = ttk.Entry(current_pid_frame, textvariable=self.current_i_var, width=8)
        current_i_entry.grid(row=0, column=3, padx=(0, 10))
        
        # Current D
        ttk.Label(current_pid_frame, text="D:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        self.current_d_var = tk.DoubleVar(value=0.0)
        current_d_entry = ttk.Entry(current_pid_frame, textvariable=self.current_d_var, width=8)
        current_d_entry.grid(row=0, column=5, padx=(0, 10))
        
        ttk.Button(current_pid_frame, text="Get", command=self.get_current_pid).grid(row=0, column=6, padx=(5, 5))
        ttk.Button(current_pid_frame, text="Set", command=self.set_current_pid).grid(row=0, column=7, padx=(0, 5))
        
        # Motion downsampling
        ttk.Label(pid_frame, text="Motion Downsampling:", style='Heading.TLabel').grid(row=6, column=0, sticky=tk.W, pady=(10, 5))
        downsample_frame = ttk.Frame(pid_frame)
        downsample_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        downsample_frame.columnconfigure(1, weight=1)
        
        ttk.Label(downsample_frame, text="Factor:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.downsample_var = tk.IntVar(value=1)
        downsample_entry = ttk.Entry(downsample_frame, textvariable=self.downsample_var, width=8)
        downsample_entry.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Button(downsample_frame, text="Get", command=self.get_downsample).grid(row=0, column=2, padx=(5, 5))
        ttk.Button(downsample_frame, text="Set", command=self.set_downsample).grid(row=0, column=3, padx=(0, 5))
        
        # Help text
        help_label = ttk.Label(downsample_frame, text="(1=every loop, 2=every other loop, etc.)", style='Status.TLabel')
        help_label.grid(row=1, column=0, columnspan=4, pady=(2, 0))
        
        # Save config button
        save_frame = ttk.Frame(pid_frame)
        save_frame.grid(row=8, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Button(save_frame, text="Save Configuration", command=self.save_config).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(save_frame, text="Load Configuration", command=self.load_config).grid(row=0, column=1, padx=(0, 5))
        
        # Store entry widgets for change tracking
        self.pid_entries = {
            'velocity': [vel_p_entry, vel_i_entry, vel_d_entry],
            'angle': [angle_p_entry, angle_i_entry, angle_d_entry],
            'current': [current_p_entry, current_i_entry, current_d_entry]
        }
        
        # Bind change events to all PID entry fields
        for pid_type, entries in self.pid_entries.items():
            for entry in entries:
                entry.bind('<KeyRelease>', lambda e, pid_type=pid_type: self._on_pid_change(pid_type))
                entry.bind('<FocusOut>', lambda e, pid_type=pid_type: self._on_pid_change(pid_type))
        
    def setup_status_frame(self, parent: ttk.Frame, row: int) -> None:
        """Set up the status display frame."""
        status_frame = ttk.LabelFrame(parent, text="Status", padding="10")
        status_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        # Connection status
        ttk.Label(status_frame, text="Connection:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.connection_status = ttk.Label(status_frame, text="Disconnected", style='Error.TLabel')
        self.connection_status.grid(row=0, column=1, sticky=tk.W)
        
        # Current values
        ttk.Label(status_frame, text="Position:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.position_status = ttk.Label(status_frame, text="N/A", style='Status.TLabel')
        self.position_status.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        ttk.Label(status_frame, text="Velocity:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5))
        self.velocity_status = ttk.Label(status_frame, text="N/A", style='Status.TLabel')
        self.velocity_status.grid(row=2, column=1, sticky=tk.W)
        
        ttk.Label(status_frame, text="Torque:").grid(row=3, column=0, sticky=tk.W, padx=(0, 5))
        self.torque_status = ttk.Label(status_frame, text="N/A", style='Status.TLabel')
        self.torque_status.grid(row=3, column=1, sticky=tk.W)
        
        ttk.Label(status_frame, text="Temperature:").grid(row=4, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.temperature_status = ttk.Label(status_frame, text="N/A", style='Status.TLabel')
        self.temperature_status.grid(row=4, column=1, sticky=tk.W, pady=(5, 0))
        
        ttk.Label(status_frame, text="Internal Temp:").grid(row=5, column=0, sticky=tk.W, padx=(0, 5))
        self.internal_temperature_status = ttk.Label(status_frame, text="N/A", style='Status.TLabel')
        self.internal_temperature_status.grid(row=5, column=1, sticky=tk.W)
        
        ttk.Label(status_frame, text="Bus Voltage:").grid(row=6, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.bus_voltage_status = ttk.Label(status_frame, text="N/A", style='Status.TLabel')
        self.bus_voltage_status.grid(row=6, column=1, sticky=tk.W, pady=(5, 0))
        
    def setup_plot_frame(self, parent: ttk.Frame, row: int) -> None:
        """Set up the real-time plotting frame."""
        plot_frame = ttk.LabelFrame(parent, text="Real-time Data Plot", padding="10")
        plot_frame.grid(row=row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        plot_frame.columnconfigure(0, weight=1)
        plot_frame.rowconfigure(1, weight=1)
        parent.rowconfigure(row, weight=1)
        
        # Plot control frame
        control_frame = ttk.Frame(plot_frame)
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Plot control buttons
        self.plot_start_btn = ttk.Button(control_frame, text="Start Plotting", command=self.start_plotting, state='disabled')
        self.plot_start_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.plot_stop_btn = ttk.Button(control_frame, text="Stop Plotting", command=self.stop_plotting, state='disabled')
        self.plot_stop_btn.grid(row=0, column=1, padx=(0, 5))
        
        self.plot_clear_btn = ttk.Button(control_frame, text="Clear Data", command=self.clear_plot_data)
        self.plot_clear_btn.grid(row=0, column=2, padx=(0, 5))
        
        self.plot_save_btn = ttk.Button(control_frame, text="Save Plot", command=self.save_plot)
        self.plot_save_btn.grid(row=0, column=3, padx=(0, 5))
        
        # Plot status
        self.plot_status = ttk.Label(control_frame, text="Ready", style='Status.TLabel')
        self.plot_status.grid(row=0, column=4, padx=(20, 0))
        
        # Create plotter with increased spacing and more data points for smooth plotting
        self.plotter = ActuatorPlotter(plot_frame, max_points=500)
        self.plotter.get_canvas().get_tk_widget().grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
    def setup_log_frame(self, parent: ttk.Frame, row: int) -> None:
        """Set up the log display frame."""
        log_frame = ttk.LabelFrame(parent, text="Communication Log", padding="10")
        log_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        parent.rowconfigure(row, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Clear log button
        ttk.Button(log_frame, text="Clear Log", command=self.clear_log).grid(row=1, column=0, pady=(5, 0))
        
    def refresh_ports(self) -> None:
        """Refresh the list of available serial ports."""
        all_ports = [port.device for port in serial.tools.list_ports.comports()]
        # Filter out /dev/ttyS* devices (system serial ports)
        ports = [port for port in all_ports if not port.startswith('/dev/ttyS')]
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.set(ports[0])
        self.log_message(f"Refreshed available ports (filtered {len(all_ports) - len(ports)} system ports)")
        
    def toggle_connection(self) -> None:
        """Toggle connection to the actuator."""
        if not self.connected:
            self.connect()
        else:
            self.disconnect()
            
    def connect(self) -> None:
        """Connect to the actuator."""
        port = self.port_var.get()
        if not port:
            messagebox.showerror("Error", "Please select a port")
            return
            
        try:
            baudrate = int(self.baudrate_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid baud rate")
            return
            
        # Create USB interface and ACBv2 actuator
        usb_interface = USBInterface(port, baudrate)
        self.actuator = ACBv2(usb_interface)
        
        # Set command mode on the interface
        mode_map = {
            'Human Readable': CommandMode.HUMAN_READABLE,
            'High Speed Binary': CommandMode.HIGH_SPEED_BINARY,
            'SimpleFOC': CommandMode.SIMPLEFOC
        }
        mode = mode_map.get(self.mode_var.get(), CommandMode.HUMAN_READABLE)
        self.actuator.interface.command_mode = mode
        # Print info about the port being connected to
        self.log_message(f"Attempting to connect to port: {port} at baudrate: {baudrate}")
        
        if self.actuator.connect():
            self.connected = True
            self.connect_btn.config(text="Disconnect")
            self.connection_status.config(text="Connected", style='Success.TLabel')
            # Enable plot buttons when connected
            self.plot_start_btn.config(state='normal')
            self.log_message(f"Connected to {port} at {baudrate} baud")
            
            # Start status monitoring at 2Hz
            self.start_status_monitoring()
            
            # Auto-load configuration values
            self.log_message("Loading configuration from actuator...")
            self.load_config()
        else:
            self.actuator = None
            messagebox.showerror("Error", f"Failed to connect to {port}")
            
    def disconnect(self) -> None:
        """Disconnect from the actuator."""
        if self.actuator:
            self.stop_monitoring()
            self.stop_status_monitoring()
            self.stop_broadcast_listening()
            self.actuator.disconnect()
            self.actuator = None
            
        self.connected = False
        self.connect_btn.config(text="Connect")
        self.connection_status.config(text="Disconnected", style='Error.TLabel')
        # Disable plot buttons when disconnected
        self.plot_start_btn.config(state='disabled')
        self.plot_stop_btn.config(state='disabled')
        self.log_message("Disconnected from actuator")
        
    def test_connection(self) -> None:
        """Test the connection to the actuator."""
        port = self.port_var.get()
        if not port:
            messagebox.showerror("Error", "Please select a port")
            return
            
        try:
            baudrate = int(self.baudrate_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid baud rate")
            return
            
        self.log_message(f"Testing connection to {port} at {baudrate} baud...")
        
        # Create temporary USB interface and ACBv2 actuator for testing
        test_usb_interface = USBInterface(port, baudrate)
        test_actuator = ACBv2(test_usb_interface)
        
        # Set command mode on the interface
        mode_map = {
            'Human Readable': CommandMode.HUMAN_READABLE,
            'High Speed Binary': CommandMode.HIGH_SPEED_BINARY,
            'SimpleFOC': CommandMode.SIMPLEFOC
        }
        mode = mode_map.get(self.mode_var.get(), CommandMode.HUMAN_READABLE)
        test_actuator.interface.command_mode = mode
        
        if test_actuator.connect():
            self.log_message("✅ Connection successful")
            
            # Test basic commands
            self.log_message("Testing enable command...")
            if test_actuator.enable():
                self.log_message("✅ Enable command successful")
            else:
                self.log_message("❌ Enable command failed")
                
            self.log_message("Testing disable command...")
            if test_actuator.disable():
                self.log_message("✅ Disable command successful")
            else:
                self.log_message("❌ Disable command failed")
                
            # Test get commands
            self.log_message("Testing get_position command...")
            position = test_actuator.get_position()
            if position is not None:
                self.log_message(f"✅ Position: {position:.2f}°")
            else:
                self.log_message("❌ Failed to get position")
                
            test_actuator.disconnect()
            self.log_message("Test completed")
        else:
            self.log_message("❌ Connection failed")
            
    def set_broadcast(self) -> None:
        """Set broadcast frequency."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        frequency = self.broadcast_freq_var.get()
        self.log_message(f"Setting broadcast frequency to {frequency} Hz...")
        if self.actuator.set_broadcast_frequency(frequency):
            if frequency > 0:
                self.log_message(f"✓ Broadcast started at {frequency} Hz")
                # Stop status monitoring when broadcast is active to avoid conflicts
                self.stop_status_monitoring()
                # Start listening for broadcast data
                self.start_broadcast_listening()
            else:
                self.log_message("✓ Broadcast stopped")
                # Stop listening for broadcast data
                self.stop_broadcast_listening()
                # Restart status monitoring when broadcast is stopped
                self.start_status_monitoring()
        else:
            self.log_message("✗ Failed to set broadcast frequency")
            
    def stop_broadcast(self) -> None:
        """Stop broadcast (set frequency to 0)."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        self.broadcast_freq_var.set(0.0)
        self.log_message("Stopping broadcast...")
        if self.actuator.set_broadcast_frequency(0.0):
            self.log_message("✓ Broadcast stopped")
            # Stop listening for broadcast data
            self.stop_broadcast_listening()
            # Restart status monitoring when broadcast is stopped
            self.start_status_monitoring()
        else:
            self.log_message("✗ Failed to stop broadcast")
        
    def set_position(self) -> None:
        """Set actuator position."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        position = self.position_var.get()
        if self.actuator.set_position(position):
            self.log_message(f"Set position to {position}°")
        else:
            self.log_message(f"Failed to set position to {position}°")
            
    def set_velocity(self) -> None:
        """Set actuator velocity."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        velocity = self.velocity_var.get()
        if self.actuator.set_velocity(velocity):
            self.log_message(f"Set velocity to {velocity}°/s")
        else:
            self.log_message(f"Failed to set velocity to {velocity}°/s")
            
    def set_torque(self) -> None:
        """Set actuator torque."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        torque = self.torque_var.get()
        if self.actuator.set_torque(torque):
            self.log_message(f"Set torque to {torque} Nm")
        else:
            self.log_message(f"Failed to set torque to {torque} Nm")
            
    def enable_actuator(self) -> None:
        """Enable the actuator."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        self.log_message("Sending enable command...")
        if self.actuator.enable():
            self.log_message("✓ Actuator enabled successfully")
        else:
            self.log_message("✗ Failed to enable actuator")
            
    def disable_actuator(self) -> None:
        """Disable the actuator."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        self.log_message("Sending disable command...")
        if self.actuator.disable():
            self.log_message("✓ Actuator disabled successfully")
        else:
            self.log_message("✗ Failed to disable actuator")
            
    def home_actuator(self) -> None:
        """Home the actuator."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        if self.actuator.home():
            self.log_message("Actuator homing")
        else:
            self.log_message("Failed to home actuator")
            
    def stop_actuator(self) -> None:
        """Stop the actuator."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        if self.actuator.stop():
            self.log_message("Actuator stopped")
        else:
            self.log_message("Failed to stop actuator")
    
    def recalibrate_sensors(self) -> None:
        """Recalibrate the actuator sensors."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
        
        # Show confirmation dialog
        result = messagebox.askyesno(
            "Recalibrate Sensors", 
            "This will recalibrate the actuator sensors. The motor will be disabled during calibration.\n\n"
            "Continue with recalibration?"
        )
        
        if not result:
            return
            
        self.log_message("Starting sensor recalibration...")
        if self.actuator.recalibrate_sensors():
            self.log_message("✓ Sensor recalibration completed")
            messagebox.showinfo(
                "Recalibration Complete", 
                "Sensor recalibration completed successfully.\n\n"
                "Use 'Save Configuration' to save the new calibration values to EEPROM."
            )
        else:
            self.log_message("✗ Failed to recalibrate sensors")
            messagebox.showerror("Error", "Failed to recalibrate sensors")
            
    def get_position(self) -> None:
        """Get current position."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        position = self.actuator.get_position()
        if position is not None:
            self.position_status.config(text=f"{position:.2f}°")
            self.log_message(f"Current position: {position:.2f}°")
        else:
            self.log_message("Failed to get position")
            
    def get_velocity(self) -> None:
        """Get current velocity."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        velocity = self.actuator.get_velocity()
        if velocity is not None:
            self.velocity_status.config(text=f"{velocity:.2f}°/s")
            self.log_message(f"Current velocity: {velocity:.2f}°/s")
        else:
            self.log_message("Failed to get velocity")
            
    def get_torque(self) -> None:
        """Get current torque."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        torque = self.actuator.get_torque()
        if torque is not None:
            self.torque_status.config(text=f"{torque:.2f} Nm")
            self.log_message(f"Current torque: {torque:.2f} Nm")
        else:
            self.log_message("Failed to get torque")
    
    def get_temperature(self) -> None:
        """Get current board temperature."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        temperature = self.actuator.get_temperature()
        if temperature is not None:
            self.temperature_status.config(text=f"{temperature:.1f}°C")
            self.log_message(f"Board temperature: {temperature:.1f}°C")
        else:
            self.log_message("Failed to get temperature")
    
    def get_bus_voltage(self) -> None:
        """Get current bus voltage."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        bus_voltage = self.actuator.get_bus_voltage()
        if bus_voltage is not None:
            self.bus_voltage_status.config(text=f"{bus_voltage:.2f} V")
            self.log_message(f"Bus voltage: {bus_voltage:.2f} V")
        else:
            self.log_message("Failed to get bus voltage")
    
    def get_internal_temperature(self) -> None:
        """Get current internal STM32 temperature."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        internal_temperature = self.actuator.get_internal_temperature()
        if internal_temperature is not None:
            self.internal_temperature_status.config(text=f"{internal_temperature:.1f}°C")
            self.log_message(f"Internal temperature: {internal_temperature:.1f}°C")
        else:
            self.log_message("Failed to get internal temperature")
    
    def get_velocity_pid(self) -> None:
        """Get velocity PID parameters."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        pid_values = self.actuator.get_velocity_pid()
        if pid_values is not None:
            p, i, d = pid_values
            self.vel_p_var.set(p)
            self.vel_i_var.set(i)
            self.vel_d_var.set(d)
            self.log_message(f"Velocity PID: P={p:.3f}, I={i:.3f}, D={d:.3f}")
        else:
            self.log_message("Failed to get velocity PID")
    
    def set_velocity_pid(self) -> None:
        """Set velocity PID parameters."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        p = self.vel_p_var.get()
        i = self.vel_i_var.get()
        d = self.vel_d_var.get()
        
        if self.actuator.set_velocity_pid(p, i, d):
            self.log_message(f"Set velocity PID: P={p:.3f}, I={i:.3f}, D={d:.3f}")
            self._clear_unsaved_changes('velocity')
        else:
            self.log_message("Failed to set velocity PID")
    
    def get_angle_pid(self) -> None:
        """Get angle PID parameters."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        pid_values = self.actuator.get_angle_pid()
        if pid_values is not None:
            p, i, d = pid_values
            self.angle_p_var.set(p)
            self.angle_i_var.set(i)
            self.angle_d_var.set(d)
            self.log_message(f"Angle PID: P={p:.3f}, I={i:.3f}, D={d:.3f}")
        else:
            self.log_message("Failed to get angle PID")
    
    def set_angle_pid(self) -> None:
        """Set angle PID parameters."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        p = self.angle_p_var.get()
        i = self.angle_i_var.get()
        d = self.angle_d_var.get()
        
        if self.actuator.set_angle_pid(p, i, d):
            self.log_message(f"Set angle PID: P={p:.3f}, I={i:.3f}, D={d:.3f}")
            self._clear_unsaved_changes('angle')
        else:
            self.log_message("Failed to set angle PID")
    
    def get_current_pid(self) -> None:
        """Get current PID parameters."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        pid_values = self.actuator.get_current_pid()
        if pid_values is not None:
            p, i, d = pid_values
            self.current_p_var.set(p)
            self.current_i_var.set(i)
            self.current_d_var.set(d)
            self.log_message(f"Current PID: P={p:.3f}, I={i:.3f}, D={d:.3f}")
        else:
            self.log_message("Failed to get current PID")
    
    def set_current_pid(self) -> None:
        """Set current PID parameters."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        p = self.current_p_var.get()
        i = self.current_i_var.get()
        d = self.current_d_var.get()
        
        if self.actuator.set_current_pid(p, i, d):
            self.log_message(f"Set current PID: P={p:.3f}, I={i:.3f}, D={d:.3f}")
            self._clear_unsaved_changes('current')
        else:
            self.log_message("Failed to set current PID")
    
    def save_config(self) -> None:
        """Save configuration to EEPROM."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        if self.actuator.save_config():
            self.log_message("Configuration saved to EEPROM")
            # Clear all unsaved changes
            self._clear_unsaved_changes('velocity')
            self._clear_unsaved_changes('angle')
            self._clear_unsaved_changes('current')
        else:
            self.log_message("Failed to save configuration")
    
    def load_config(self) -> None:
        """Load configuration from actuator."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        # Load all PID values
        self.get_velocity_pid()
        self.get_angle_pid()
        self.get_current_pid()
        
        # Load downsampling value
        self.get_downsample()
        
        # Clear all unsaved changes since we loaded fresh values
        self._clear_unsaved_changes('velocity')
        self._clear_unsaved_changes('angle')
        self._clear_unsaved_changes('current')
        
        self.log_message("Configuration loaded from actuator")
    
    def get_downsample(self) -> None:
        """Get current motion downsampling value."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        downsample = self.actuator.get_downsample()
        if downsample is not None:
            self.downsample_var.set(downsample)
            self.log_message(f"Motion downsampling: {downsample}")
        else:
            self.log_message("Failed to get motion downsampling")
    
    def set_downsample(self) -> None:
        """Set motion downsampling value."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        downsample = self.downsample_var.get()
        if downsample < 1:
            messagebox.showerror("Error", "Downsampling factor must be 1 or greater")
            return
        
        if self.actuator.set_downsample(downsample):
            self.log_message(f"Set motion downsampling to: {downsample}")
        else:
            self.log_message("Failed to set motion downsampling")
    
    def _on_pid_change(self, pid_type: str) -> None:
        """Handle PID value changes and update visual feedback."""
        # Mark this PID type as having unsaved changes
        self.unsaved_changes[f'{pid_type}_pid'] = True
        
        # Update visual feedback for all entries of this PID type
        for entry in self.pid_entries[pid_type]:
            entry.configure(style='Unsaved.TEntry')
    
    def _clear_unsaved_changes(self, pid_type: str) -> None:
        """Clear unsaved changes visual feedback for a PID type."""
        self.unsaved_changes[f'{pid_type}_pid'] = False
        
        # Reset visual feedback for all entries of this PID type
        for entry in self.pid_entries[pid_type]:
            entry.configure(style='TEntry')
            
    def toggle_monitoring(self) -> None:
        """Toggle real-time monitoring."""
        if not self.monitoring:
            self.start_monitoring()
        else:
            self.stop_monitoring()
            
    def start_monitoring(self) -> None:
        """Start real-time monitoring."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        # Check if plotting is active (which uses broadcast)
        if self.plotter and hasattr(self.plotter, 'plotting') and self.plotter.plotting:
            messagebox.showwarning("Warning", "Plotting is active and using broadcast mode. Stop plotting first to use manual monitoring.")
            return
            
        self.monitoring = True
        self.monitor_btn.config(text="Stop Monitoring")
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.log_message("Started real-time monitoring (Note: Status panel already updates at 2Hz)")
        
    def stop_monitoring(self) -> None:
        """Stop real-time monitoring."""
        self.monitoring = False
        self.monitor_btn.config(text="Start Monitoring")
        self.log_message("Stopped real-time monitoring")
    
    def start_status_monitoring(self) -> None:
        """Start status monitoring at 2Hz."""
        if not self.connected or not self.actuator:
            return
            
        self.status_monitoring = True
        self.status_thread = threading.Thread(target=self.status_monitor_loop, daemon=True)
        self.status_thread.start()
        self.log_message("Started status monitoring at 2Hz")
        
    def stop_status_monitoring(self) -> None:
        """Stop status monitoring."""
        self.status_monitoring = False
        if self.status_thread:
            self.status_thread.join(timeout=1.0)
        self.log_message("Stopped status monitoring")
        
    def status_monitor_loop(self) -> None:
        """Status monitoring loop at 2Hz."""
        while self.status_monitoring and self.connected:
            try:
                # Get all status values
                position = self.actuator.get_position()
                velocity = self.actuator.get_velocity()
                torque = self.actuator.get_torque()
                temperature = self.actuator.get_temperature()
                internal_temperature = self.actuator.get_internal_temperature()
                bus_voltage = self.actuator.get_bus_voltage()
                
                # Update status display
                def update_status():
                    if position is not None:
                        self.position_status.config(text=f"{position:.2f}°")
                    if velocity is not None:
                        self.velocity_status.config(text=f"{velocity:.2f}°/s")
                    if torque is not None:
                        self.torque_status.config(text=f"{torque:.2f} Nm")
                    if temperature is not None:
                        self.temperature_status.config(text=f"{temperature:.1f}°C")
                    if internal_temperature is not None:
                        self.internal_temperature_status.config(text=f"{internal_temperature:.1f}°C")
                    if bus_voltage is not None:
                        self.bus_voltage_status.config(text=f"{bus_voltage:.2f} V")
                
                self.root.after(0, update_status)
                
            except Exception as e:
                self.log_message(f"Status monitoring error: {e}")
                break
                
            time.sleep(0.5)  # 2Hz update rate
        
    def start_broadcast_listening(self) -> None:
        """Start listening for broadcast data."""
        if not self.connected or not self.actuator:
            return
            
        self.broadcast_listening = True
        self.broadcast_thread = threading.Thread(target=self.broadcast_listener_loop, daemon=True)
        self.broadcast_thread.start()
        self.log_message("Started listening for broadcast data")
        
    def stop_broadcast_listening(self) -> None:
        """Stop listening for broadcast data."""
        self.broadcast_listening = False
        if self.broadcast_thread:
            self.broadcast_thread.join(timeout=1.0)
        self.log_message("Stopped listening for broadcast data")
        
    def broadcast_listener_loop(self) -> None:
        """Listen for broadcast data from the actuator."""
        data_buffer = []  # Buffer for batch processing
        last_gui_update = 0
        gui_update_interval = 0.05  # Update GUI every 50ms (20Hz)
        
        while self.broadcast_listening and self.connected and self.actuator:
            try:
                # Access serial connection through the interface
                serial_conn = self.actuator.interface.serial_conn
                if serial_conn and serial_conn.in_waiting > 0:
                    line = serial_conn.readline().decode().strip()
                    if line.startswith("broadcast_data "):
                        # Parse enhanced broadcast data: "broadcast_data pos vel torque temp voltage int_temp"
                        parts = line.split()
                        if len(parts) >= 7:  # Now expecting 6 values + command
                            try:
                                position = float(parts[1])
                                velocity = float(parts[2])
                                torque = float(parts[3])
                                temperature = float(parts[4])
                                bus_voltage = float(parts[5])
                                internal_temperature = float(parts[6])
                                
                                # Add to buffer with all status information
                                data_buffer.append({
                                    'position': position,
                                    'velocity': velocity,
                                    'torque': torque,
                                    'temperature': temperature,
                                    'bus_voltage': bus_voltage,
                                    'internal_temperature': internal_temperature,
                                    'time': time.time()
                                })
                                
                                # Process buffer in batches for better performance
                                if len(data_buffer) >= 5:  # Process every 5 data points
                                    self._process_broadcast_buffer(data_buffer)
                                    data_buffer = []
                                
                                # Update GUI less frequently to avoid lag
                                current_time = time.time()
                                if current_time - last_gui_update >= gui_update_interval:
                                    self._update_gui_from_buffer(data_buffer)
                                    last_gui_update = current_time
                                    
                            except (ValueError, IndexError) as e:
                                self.log_message(f"Failed to parse broadcast data: {e}")
                        elif len(parts) >= 4:
                            # Fallback for old format (3 values + command)
                            try:
                                position = float(parts[1])
                                velocity = float(parts[2])
                                torque = float(parts[3])
                                
                                # Add to buffer with limited data
                                data_buffer.append({
                                    'position': position,
                                    'velocity': velocity,
                                    'torque': torque,
                                    'temperature': None,
                                    'bus_voltage': None,
                                    'internal_temperature': None,
                                    'time': time.time()
                                })
                                
                                # Process buffer in batches for better performance
                                if len(data_buffer) >= 5:  # Process every 5 data points
                                    self._process_broadcast_buffer(data_buffer)
                                    data_buffer = []
                                
                                # Update GUI less frequently to avoid lag
                                current_time = time.time()
                                if current_time - last_gui_update >= gui_update_interval:
                                    self._update_gui_from_buffer(data_buffer)
                                    last_gui_update = current_time
                                    
                            except (ValueError, IndexError) as e:
                                self.log_message(f"Failed to parse broadcast data: {e}")
                                
            except Exception as e:
                self.log_message(f"Broadcast listener error: {e}")
                break
                
            time.sleep(0.001)  # Reduced sleep for faster processing
    
    def _process_broadcast_buffer(self, data_buffer: list) -> None:
        """Process a buffer of broadcast data for plotting."""
        if not data_buffer:
            return
            
        # Get the latest data point
        latest = data_buffer[-1]
        
        # Store data for plotting
        self.data_history['time'].append(latest['time'])
        self.data_history['position'].append(latest['position'])
        self.data_history['velocity'].append(latest['velocity'])
        self.data_history['torque'].append(latest['torque'])
        
        # Keep only last 200 data points (increased for smoother plotting)
        if len(self.data_history['time']) > 200:
            for key in self.data_history:
                self.data_history[key] = self.data_history[key][-200:]
        
        # Send data to plotter if it exists and is plotting
        if self.plotter and hasattr(self.plotter, 'plotting') and self.plotter.plotting:
            self.plotter.add_data_point(latest['position'], latest['velocity'], latest['torque'], latest['time'])
    
    def _update_gui_from_buffer(self, data_buffer: list) -> None:
        """Update GUI elements from broadcast data buffer."""
        if not data_buffer:
            return
            
        # Get the latest data point
        latest = data_buffer[-1]
        
        # Update status display with a single GUI call
        def update_status():
            self.position_status.config(text=f"{latest['position']:.2f}°")
            self.velocity_status.config(text=f"{latest['velocity']:.2f}°/s")
            self.torque_status.config(text=f"{latest['torque']:.2f} Nm")
            
            # Update additional status information if available
            if latest.get('temperature') is not None:
                self.temperature_status.config(text=f"{latest['temperature']:.1f}°C")
            if latest.get('bus_voltage') is not None:
                self.bus_voltage_status.config(text=f"{latest['bus_voltage']:.2f} V")
            if latest.get('internal_temperature') is not None:
                self.internal_temperature_status.config(text=f"{latest['internal_temperature']:.1f}°C")
        
        self.root.after(0, update_status)
        
    def monitor_loop(self) -> None:
        """Real-time monitoring loop for data collection and plotting."""
        while self.monitoring and self.connected:
            try:
                # Get current values (status panel already updates at 2Hz automatically)
                position = self.actuator.get_position()
                velocity = self.actuator.get_velocity()
                torque = self.actuator.get_torque()
                
                # Store data for plotting
                current_time = time.time()
                self.data_history['time'].append(current_time)
                self.data_history['position'].append(position if position is not None else 0)
                self.data_history['velocity'].append(velocity if velocity is not None else 0)
                self.data_history['torque'].append(torque if torque is not None else 0)
                
                # Keep only last 100 data points
                if len(self.data_history['time']) > 100:
                    for key in self.data_history:
                        self.data_history[key] = self.data_history[key][-100:]
                
                # Send data to plotter if it exists and is plotting
                if self.plotter and self.plotter.plotting:
                    self.plotter.add_data_point(
                        position if position is not None else 0,
                        velocity if velocity is not None else 0,
                        torque if torque is not None else 0,
                        current_time
                    )
                
                time.sleep(0.1)  # 10 Hz update rate for data collection
                
            except Exception as e:
                self.log_message(f"Monitoring error: {e}")
                break
                
    def log_message(self, message: str) -> None:
        """Add a message to the log."""
        # Check if log_text exists (it might not be initialized yet)
        if not hasattr(self, 'log_text'):
            return
            
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
    def clear_log(self) -> None:
        """Clear the log display."""
        # Check if log_text exists (it might not be initialized yet)
        if not hasattr(self, 'log_text'):
            return
            
        self.log_text.delete(1.0, tk.END)
        
    def start_plotting(self) -> None:
        """Start real-time plotting."""
        if not self.plotter:
            return
            
        # Check if manual monitoring is active
        if self.monitoring:
            messagebox.showwarning("Warning", "Manual monitoring is active. Stop monitoring first to use plotting with broadcast mode.")
            return
            
        # Start broadcast at 50Hz for plotting
        if self.connected and self.actuator:
            self.log_message("Starting broadcast at 50Hz for plotting...")
            if self.actuator.set_broadcast_frequency(50.0):
                self.log_message("✓ Broadcast started at 50Hz")
                # Stop status monitoring when broadcast is active to avoid conflicts
                self.stop_status_monitoring()
                # Start listening for broadcast data
                self.start_broadcast_listening()
            else:
                self.log_message("✗ Failed to start broadcast for plotting")
                return
        else:
            self.log_message("Not connected to actuator - cannot start plotting")
            return
            
        self.plotter.start_plotting()
        self.plot_start_btn.config(state='disabled')
        self.plot_stop_btn.config(state='normal')
        self.plot_status.config(text="Plotting... (50Hz broadcast)")
        self.log_message("Started real-time plotting with broadcast")
        
    def stop_plotting(self) -> None:
        """Stop real-time plotting."""
        if not self.plotter:
            return
            
        # Stop broadcast when stopping plotting
        if self.connected and self.actuator:
            self.log_message("Stopping broadcast for plotting...")
            if self.actuator.set_broadcast_frequency(0.0):
                self.log_message("✓ Broadcast stopped")
                # Stop listening for broadcast data
                self.stop_broadcast_listening()
                # Restart status monitoring when broadcast is stopped
                self.start_status_monitoring()
            else:
                self.log_message("✗ Failed to stop broadcast")
            
        self.plotter.stop_plotting()
        self.plot_start_btn.config(state='normal')
        self.plot_stop_btn.config(state='disabled')
        self.plot_status.config(text="Ready")
        self.log_message("Stopped real-time plotting")
        
    def clear_plot_data(self) -> None:
        """Clear all plot data."""
        if not self.plotter:
            return
            
        # Stop broadcast and plotting if active
        if self.plotter and hasattr(self.plotter, 'plotting') and self.plotter.plotting:
            self.stop_plotting()
            
        self.plotter.clear_data()
        self.plot_status.config(text="Data cleared")
        self.log_message("Cleared plot data")
        
    def save_plot(self) -> None:
        """Save the current plot to a file."""
        if not self.plotter:
            return
            
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filename:
            self.plotter.save_plot(filename)
            self.plot_status.config(text=f"Saved to {filename}")
            self.log_message(f"Plot saved to {filename}")
        
    def run(self) -> None:
        """Run the GUI application."""
        self.root.mainloop()


def main() -> None:
    """Main entry point for the GUI application."""
    app = ActuatorGUI()
    app.run()


if __name__ == "__main__":
    main()

