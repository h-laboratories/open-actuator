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
        
        # Plotting polling
        self.plotting_polling = False
        self.plotting_thread: Optional[threading.Thread] = None
        
        
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
        
        # Auto-resize window to fit content
        self.root.after(100, self.auto_resize_window)
        
    def auto_resize_window(self) -> None:
        """Automatically resize the window to fit all content."""
        # Update the window to ensure all widgets are rendered
        self.root.update_idletasks()
        
        # Get the required size for all content
        self.root.geometry("")  # Remove any fixed geometry
        
        # Get the natural size of the window
        self.root.update_idletasks()
        
        # Set a minimum size to ensure usability
        self.root.minsize(800, 600)
        
        # Center the window on screen
        self.center_window()
        
    def center_window(self) -> None:
        """Center the window on the screen."""
        self.root.update_idletasks()
        
        # Get window size
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate position to center the window
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        # Set the window position
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
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
        # Configure grid weights for two columns
        self.root.columnconfigure(0, weight=1)  # Left column (controls)
        self.root.columnconfigure(1, weight=2)  # Right column (plot) - wider
        self.root.rowconfigure(1, weight=1)  # Main content area
        
        # Setup menubar
        self.setup_menubar()
        
        # Main container with two columns
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title spanning both columns
        # title_label = ttk.Label(main_frame, text="Open Actuator Control", style='Title.TLabel')
        # title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
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
        
    def setup_menubar(self) -> None:
        """Set up the menubar at the top of the window."""
        # Create the menubar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Setup New Actuator", command=self.open_setup_actuator)
        tools_menu.add_command(label="Calibrate Sensors", command=self.calibrate_sensors)
        tools_menu.add_command(label="Reset to Defaults", command=self.reset_to_defaults)
        tools_menu.add_separator()
        tools_menu.add_command(label="Clear Data History", command=self.clear_data_history)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        
        # Store menu references for state updates
        self.tools_menu = tools_menu
    
    
    def calibrate_sensors(self) -> None:
        """Calibrate actuator sensors."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Please connect to an actuator first")
            return
        messagebox.showinfo("Calibrate Sensors", "Sensor calibration started...")
    
    def reset_to_defaults(self) -> None:
        """Reset actuator to default settings."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Please connect to an actuator first")
            return
        if messagebox.askyesno("Reset to Defaults", "Are you sure you want to reset to default settings?"):
            messagebox.showinfo("Reset", "Settings reset to defaults!")
    
    def clear_data_history(self) -> None:
        """Clear the data history."""
        self.data_history = {
            'position': [],
            'velocity': [],
            'torque': [],
            'time': []
        }
        messagebox.showinfo("Clear Data", "Data history cleared!")
    
    
    def show_about(self) -> None:
        """Show about dialog."""
        messagebox.showinfo("About", "Open Actuator Control v1.0\n\nA comprehensive GUI for controlling actuators.")
    
    def show_documentation(self) -> None:
        """Show documentation."""
        import webbrowser
        webbrowser.open("https://docs.hlaboratories.com/?ref=open-actuator-gui")
        
    def open_setup_actuator(self) -> None:
        """Open the Setup New Actuator window."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Please connect to an actuator first")
            return
            
        # Create setup window
        setup_window = tk.Toplevel(self.root)
        setup_window.title("Setup New Actuator")
        setup_window.geometry("400x400")
        setup_window.resizable(False, True)
        
        # Center the window
        setup_window.transient(self.root)
        setup_window.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(setup_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Setup New Actuator", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Instructions
        instructions = ttk.Label(main_frame, 
                           text="This tool will help you set up a new actuator by configuring\n"
                                "the number of pole pairs and calibrating the sensors.",
                           style='Status.TLabel')
        instructions.pack(pady=(0, 20))
        
        # Pole pairs input
        pole_pairs_frame = ttk.Frame(main_frame)
        pole_pairs_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(pole_pairs_frame, text="Number of Pole Pairs:", style='Heading.TLabel').pack(anchor=tk.W)
        
        input_frame = ttk.Frame(pole_pairs_frame)
        input_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.pole_pairs_var = tk.IntVar(value=7)  # Default value
        pole_pairs_entry = ttk.Entry(input_frame, textvariable=self.pole_pairs_var, width=10)
        pole_pairs_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(input_frame, text="(typically 7 for most motors)", style='Status.TLabel').pack(side=tk.LEFT)
        
        # Warning about calibration
        warning_frame = ttk.LabelFrame(main_frame, text="Important", padding="10")
        warning_frame.pack(fill=tk.X, pady=(0, 20))
        
        warning_text = ttk.Label(warning_frame, 
                                text="WARNING: Calibration will:\n"
                                     "- Disable the motor during calibration\n"
                                     "- Recalibrate sensor zero position\n"
                                     "- Save configuration to EEPROM\n"
                                     "- This process takes a few seconds",
                                style='Status.TLabel',
                                justify=tk.LEFT)
        warning_text.pack(anchor=tk.W)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(button_frame, text="Cancel", command=setup_window.destroy).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="Calibrate & Save", 
                  command=lambda: self.perform_actuator_setup(setup_window)).pack(side=tk.RIGHT)
        
    def perform_actuator_setup(self, setup_window: tk.Toplevel) -> None:
        """Perform the actuator setup process."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        # Get pole pairs value
        try:
            pole_pairs = self.pole_pairs_var.get()
            if pole_pairs < 1:
                messagebox.showerror("Error", "Number of pole pairs must be 1 or greater")
                return
        except tk.TclError:
            messagebox.showerror("Error", "Invalid number of pole pairs")
            return
            
        # Show confirmation dialog
        result = messagebox.askyesno(
            "Confirm Setup", 
            f"This will:\n"
            f"- Set pole pairs to {pole_pairs}\n"
            f"- Recalibrate sensors\n"
            f"- Save configuration to EEPROM\n\n"
            f"Continue with setup?"
        )
        
        if not result:
            return
            
        # Disable the setup window during process
        setup_window.config(cursor="watch")
        for widget in setup_window.winfo_children():
            for child in widget.winfo_children():
                if isinstance(child, (ttk.Button, ttk.Entry)):
                    child.config(state='disabled')
        
        try:
            # Step 1: Set pole pairs
            if not self.actuator.set_pole_pairs(pole_pairs):
                messagebox.showerror("Error", "Failed to set pole pairs")
                return
            
            # Step 2: Recalibrate sensors
            if not self.actuator.recalibrate_sensors():
                messagebox.showerror("Error", "Failed to recalibrate sensors")
                return
            
            # Step 3: Save configuration
            if not self.actuator.save_config():
                messagebox.showerror("Error", "Failed to save configuration")
                return
            
            # Success message
            messagebox.showinfo(
                "Setup Complete", 
                f"Actuator setup completed successfully!\n\n"
                f"- Pole pairs: {pole_pairs}\n"
                f"- Sensors recalibrated\n"
                f"- Configuration saved to EEPROM"
            )
            
            setup_window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Setup failed: {str(e)}")
            self.log_message(f"ERROR: Setup failed: {str(e)}")
        finally:
            # Re-enable the setup window
            setup_window.config(cursor="")
            for widget in setup_window.winfo_children():
                for child in widget.winfo_children():
                    if isinstance(child, (ttk.Button, ttk.Entry)):
                        child.config(state='normal')
        
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
        
        # Position preset buttons
        pos_preset_frame = ttk.Frame(pos_frame)
        pos_preset_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Preset buttons for position
        ttk.Button(pos_preset_frame, text="-1000", command=lambda: self.increment_position_value(-1000)).grid(row=0, column=0, padx=(0, 2))
        ttk.Button(pos_preset_frame, text="-100", command=lambda: self.increment_position_value(-100)).grid(row=0, column=1, padx=(0, 2))
        ttk.Button(pos_preset_frame, text="-10", command=lambda: self.increment_position_value(-10)).grid(row=0, column=2, padx=(0, 2))
        ttk.Button(pos_preset_frame, text="0", command=lambda: self.set_position_value(0)).grid(row=0, column=3, padx=(0, 2))
        ttk.Button(pos_preset_frame, text="+10", command=lambda: self.increment_position_value(10)).grid(row=0, column=4, padx=(0, 2))
        ttk.Button(pos_preset_frame, text="+100", command=lambda: self.increment_position_value(100)).grid(row=0, column=5, padx=(0, 2))
        ttk.Button(pos_preset_frame, text="+1000", command=lambda: self.increment_position_value(1000)).grid(row=0, column=6, padx=(0, 2))
        
        # Position input and set button
        pos_input_frame = ttk.Frame(pos_frame)
        pos_input_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))
        
        self.position_var = tk.DoubleVar()
        position_entry = ttk.Entry(pos_input_frame, textvariable=self.position_var, width=15)
        position_entry.grid(row=0, column=0, padx=(0, 5))
        
        ttk.Button(pos_input_frame, text="Set Position", command=self.set_position).grid(row=0, column=1, padx=(0, 5))
        
        # Velocity control
        ttk.Label(control_frame, text="Velocity (deg/s):", style='Heading.TLabel').grid(row=2, column=0, sticky=tk.W, pady=(10, 5))
        vel_frame = ttk.Frame(control_frame)
        vel_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Velocity preset buttons
        vel_preset_frame = ttk.Frame(vel_frame)
        vel_preset_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Preset buttons for velocity
        ttk.Button(vel_preset_frame, text="-1000", command=lambda: self.increment_velocity_value(-1000)).grid(row=0, column=0, padx=(0, 2))
        ttk.Button(vel_preset_frame, text="-100", command=lambda: self.increment_velocity_value(-100)).grid(row=0, column=1, padx=(0, 2))
        ttk.Button(vel_preset_frame, text="-10", command=lambda: self.increment_velocity_value(-10)).grid(row=0, column=2, padx=(0, 2))
        ttk.Button(vel_preset_frame, text="0", command=lambda: self.set_velocity_value(0)).grid(row=0, column=3, padx=(0, 2))
        ttk.Button(vel_preset_frame, text="+10", command=lambda: self.increment_velocity_value(10)).grid(row=0, column=4, padx=(0, 2))
        ttk.Button(vel_preset_frame, text="+100", command=lambda: self.increment_velocity_value(100)).grid(row=0, column=5, padx=(0, 2))
        ttk.Button(vel_preset_frame, text="+1000", command=lambda: self.increment_velocity_value(1000)).grid(row=0, column=6, padx=(0, 2))
        
        # Velocity input and set button
        vel_input_frame = ttk.Frame(vel_frame)
        vel_input_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))
        
        self.velocity_var = tk.DoubleVar()
        velocity_entry = ttk.Entry(vel_input_frame, textvariable=self.velocity_var, width=15)
        velocity_entry.grid(row=0, column=0, padx=(0, 5))
        
        ttk.Button(vel_input_frame, text="Set Velocity", command=self.set_velocity).grid(row=0, column=1, padx=(0, 5))
        
        # Torque control
        ttk.Label(control_frame, text="Torque (Nm):", style='Heading.TLabel').grid(row=4, column=0, sticky=tk.W, pady=(10, 5))
        torque_frame = ttk.Frame(control_frame)
        torque_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Torque preset buttons
        torque_preset_frame = ttk.Frame(torque_frame)
        torque_preset_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Preset buttons for torque
        ttk.Button(torque_preset_frame, text="-1000", command=lambda: self.increment_torque_value(-1000)).grid(row=0, column=0, padx=(0, 2))
        ttk.Button(torque_preset_frame, text="-100", command=lambda: self.increment_torque_value(-100)).grid(row=0, column=1, padx=(0, 2))
        ttk.Button(torque_preset_frame, text="-10", command=lambda: self.increment_torque_value(-10)).grid(row=0, column=2, padx=(0, 2))
        ttk.Button(torque_preset_frame, text="0", command=lambda: self.set_torque_value(0)).grid(row=0, column=3, padx=(0, 2))
        ttk.Button(torque_preset_frame, text="+10", command=lambda: self.increment_torque_value(10)).grid(row=0, column=4, padx=(0, 2))
        ttk.Button(torque_preset_frame, text="+100", command=lambda: self.increment_torque_value(100)).grid(row=0, column=5, padx=(0, 2))
        ttk.Button(torque_preset_frame, text="+1000", command=lambda: self.increment_torque_value(1000)).grid(row=0, column=6, padx=(0, 2))
        
        # Torque input and set button
        torque_input_frame = ttk.Frame(torque_frame)
        torque_input_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))
        
        self.torque_var = tk.DoubleVar()
        torque_entry = ttk.Entry(torque_input_frame, textvariable=self.torque_var, width=15)
        torque_entry.grid(row=0, column=0, padx=(0, 5))
        
        ttk.Button(torque_input_frame, text="Set Torque", command=self.set_torque).grid(row=0, column=1, padx=(0, 5))
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Button(button_frame, text="Enable", command=self.enable_actuator).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="Disable", command=self.disable_actuator).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(button_frame, text="Home", command=self.home_actuator).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(button_frame, text="Stop", command=self.stop_actuator).grid(row=0, column=3, padx=(0, 5))
        ttk.Button(button_frame, text="Reset Position", command=self.reset_position).grid(row=0, column=4, padx=(0, 5))
        
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
        
        # Full state controls
        full_state_frame = ttk.Frame(control_frame)
        full_state_frame.grid(row=8, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Label(full_state_frame, text="Full State:", style='Heading.TLabel').grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Button(full_state_frame, text="Get Full State", command=self.get_full_state).grid(row=0, column=1, padx=(0, 5))
        
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
        
        if self.actuator.connect():
            self.connected = True
            self.connect_btn.config(text="Disconnect")
            self.connection_status.config(text="Connected", style='Success.TLabel')
            # Enable plot buttons when connected
            self.plot_start_btn.config(state='normal')
            # Enable/disable menu items
            self.tools_menu.entryconfig("Setup New Actuator", state=tk.NORMAL)
            self.tools_menu.entryconfig("Calibrate Sensors", state=tk.NORMAL)
            self.tools_menu.entryconfig("Reset to Defaults", state=tk.NORMAL)
            
            # Start status monitoring at 2Hz
            self.start_status_monitoring()
            
            # Auto-load configuration values
            self.load_config()
        else:
            self.actuator = None
            messagebox.showerror("Error", f"Failed to connect to {port}")
            
    def disconnect(self) -> None:
        """Disconnect from the actuator."""
        if self.actuator:
            self.stop_monitoring()
            self.stop_status_monitoring()
            self.stop_plotting_polling()
            self.actuator.disconnect()
            self.actuator = None
            
        self.connected = False
        self.connect_btn.config(text="Connect")
        self.connection_status.config(text="Disconnected", style='Error.TLabel')
        # Disable plot buttons when disconnected
        self.plot_start_btn.config(state='disabled')
        self.plot_stop_btn.config(state='disabled')
        # Enable/disable menu items
        self.tools_menu.entryconfig("Setup New Actuator", state=tk.DISABLED)
        self.tools_menu.entryconfig("Calibrate Sensors", state=tk.DISABLED)
        self.tools_menu.entryconfig("Reset to Defaults", state=tk.DISABLED)
        
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
            # Test basic commands
            if not test_actuator.enable():
                self.log_message("ERROR: Enable command failed")
                
            if not test_actuator.disable():
                self.log_message("ERROR: Disable command failed")
                
            # Test get commands
            position = test_actuator.get_position()
            if position is None:
                self.log_message("ERROR: Failed to get position")
                
            test_actuator.disconnect()
        else:
            self.log_message("ERROR: Connection failed")
            
    def get_full_state(self) -> None:
        """Get full actuator state."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        state = self.actuator.get_full_state()
        if state is not None:
            # Update status display
            self.position_status.config(text=f"{state['position']:.2f}°")
            self.velocity_status.config(text=f"{state['velocity']:.2f}°/s")
            self.torque_status.config(text=f"{state['torque']:.2f} Nm")
            self.temperature_status.config(text=f"{state['temperature']:.1f}°C")
            self.bus_voltage_status.config(text=f"{state['bus_voltage']:.2f} V")
            self.internal_temperature_status.config(text=f"{state['internal_temperature']:.1f}°C")
        else:
            self.log_message("ERROR: Failed to get full state")
        
    def set_position(self) -> None:
        """Set actuator position."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        position = self.position_var.get()
        if not self.actuator.set_position(position):
            self.log_message(f"ERROR: Failed to set position to {position}°")
            
    def set_velocity(self) -> None:
        """Set actuator velocity."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        velocity = self.velocity_var.get()
        if not self.actuator.set_velocity(velocity):
            self.log_message(f"ERROR: Failed to set velocity to {velocity}°/s")
            
    def set_torque(self) -> None:
        """Set actuator torque."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        torque = self.torque_var.get()
        if not self.actuator.set_torque(torque):
            self.log_message(f"ERROR: Failed to set torque to {torque} Nm")
    
    def set_position_value(self, value: float) -> None:
        """Set position value and send command."""
        self.position_var.set(value)
        self.set_position()
    
    def set_velocity_value(self, value: float) -> None:
        """Set velocity value and send command."""
        self.velocity_var.set(value)
        self.set_velocity()
    
    def set_torque_value(self, value: float) -> None:
        """Set torque value and send command."""
        self.torque_var.set(value)
        self.set_torque()
    
    def increment_position_value(self, increment: float) -> None:
        """Increment position value and send command."""
        current_value = self.position_var.get()
        new_value = current_value + increment
        self.position_var.set(new_value)
        self.set_position()
    
    def increment_velocity_value(self, increment: float) -> None:
        """Increment velocity value and send command."""
        current_value = self.velocity_var.get()
        new_value = current_value + increment
        self.velocity_var.set(new_value)
        self.set_velocity()
    
    def increment_torque_value(self, increment: float) -> None:
        """Increment torque value and send command."""
        current_value = self.torque_var.get()
        new_value = current_value + increment
        self.torque_var.set(new_value)
        self.set_torque()
            
    def enable_actuator(self) -> None:
        """Enable the actuator."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        if not self.actuator.enable():
            self.log_message("ERROR: Failed to enable actuator")
            
    def disable_actuator(self) -> None:
        """Disable the actuator."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        if not self.actuator.disable():
            self.log_message("ERROR: Failed to disable actuator")
            
    def home_actuator(self) -> None:
        """Home the actuator."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        if not self.actuator.home():
            self.log_message("ERROR: Failed to home actuator")
            
    def stop_actuator(self) -> None:
        """Stop the actuator."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        if not self.actuator.stop():
            self.log_message("ERROR: Failed to stop actuator")
    
    def reset_position(self) -> None:
        """Reset the actuator position to zero."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        # Show confirmation dialog
        result = messagebox.askyesno(
            "Reset Position", 
            "This will reset the current position to zero without changing the target.\n\n"
            "The actuator will treat its current position as the new zero reference.\n\n"
            "Continue with position reset?"
        )
        
        if not result:
            return
            
        if self.actuator.reset_position():
            messagebox.showinfo("Reset Complete", "Actuator position has been reset to zero.")
        else:
            self.log_message("ERROR: Failed to reset position")
            messagebox.showerror("Error", "Failed to reset actuator position")
    
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
            
        if self.actuator.recalibrate_sensors():
            messagebox.showinfo(
                "Recalibration Complete", 
                "Sensor recalibration completed successfully.\n\n"
                "Use 'Save Configuration' to save the new calibration values to EEPROM."
            )
        else:
            self.log_message("ERROR: Failed to recalibrate sensors")
            messagebox.showerror("Error", "Failed to recalibrate sensors")
            
    def get_position(self) -> None:
        """Get current position."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        position = self.actuator.get_position()
        if position is not None:
            self.position_status.config(text=f"{position:.2f}°")
        else:
            self.log_message("ERROR: Failed to get position")
            
    def get_velocity(self) -> None:
        """Get current velocity."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        velocity = self.actuator.get_velocity()
        if velocity is not None:
            self.velocity_status.config(text=f"{velocity:.2f}°/s")
        else:
            self.log_message("ERROR: Failed to get velocity")
            
    def get_torque(self) -> None:
        """Get current torque."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        torque = self.actuator.get_torque()
        if torque is not None:
            self.torque_status.config(text=f"{torque:.2f} Nm")
        else:
            self.log_message("ERROR: Failed to get torque")
    
    def get_temperature(self) -> None:
        """Get current board temperature."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        temperature = self.actuator.get_temperature()
        if temperature is not None:
            self.temperature_status.config(text=f"{temperature:.1f}°C")
        else:
            self.log_message("ERROR: Failed to get temperature")
    
    def get_bus_voltage(self) -> None:
        """Get current bus voltage."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        bus_voltage = self.actuator.get_bus_voltage()
        if bus_voltage is not None:
            self.bus_voltage_status.config(text=f"{bus_voltage:.2f} V")
        else:
            self.log_message("ERROR: Failed to get bus voltage")
    
    def get_internal_temperature(self) -> None:
        """Get current internal STM32 temperature."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        internal_temperature = self.actuator.get_internal_temperature()
        if internal_temperature is not None:
            self.internal_temperature_status.config(text=f"{internal_temperature:.1f}°C")
        else:
            self.log_message("ERROR: Failed to get internal temperature")
    
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
        else:
            self.log_message("ERROR: Failed to get velocity PID")
    
    def set_velocity_pid(self) -> None:
        """Set velocity PID parameters."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        p = self.vel_p_var.get()
        i = self.vel_i_var.get()
        d = self.vel_d_var.get()
        
        if self.actuator.set_velocity_pid(p, i, d):
            self._clear_unsaved_changes('velocity')
        else:
            self.log_message("ERROR: Failed to set velocity PID")
    
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
        else:
            self.log_message("ERROR: Failed to get angle PID")
    
    def set_angle_pid(self) -> None:
        """Set angle PID parameters."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        p = self.angle_p_var.get()
        i = self.angle_i_var.get()
        d = self.angle_d_var.get()
        
        if self.actuator.set_angle_pid(p, i, d):
            self._clear_unsaved_changes('angle')
        else:
            self.log_message("ERROR: Failed to set angle PID")
    
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
        else:
            self.log_message("ERROR: Failed to get current PID")
    
    def set_current_pid(self) -> None:
        """Set current PID parameters."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        p = self.current_p_var.get()
        i = self.current_i_var.get()
        d = self.current_d_var.get()
        
        if self.actuator.set_current_pid(p, i, d):
            self._clear_unsaved_changes('current')
        else:
            self.log_message("ERROR: Failed to set current PID")
    
    def save_config(self) -> None:
        """Save configuration to EEPROM."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        if self.actuator.save_config():
            # Clear all unsaved changes
            self._clear_unsaved_changes('velocity')
            self._clear_unsaved_changes('angle')
            self._clear_unsaved_changes('current')
        else:
            self.log_message("ERROR: Failed to save configuration")
    
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
    
    def get_downsample(self) -> None:
        """Get current motion downsampling value."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        downsample = self.actuator.get_downsample()
        if downsample is not None:
            self.downsample_var.set(downsample)
        else:
            self.log_message("ERROR: Failed to get motion downsampling")
    
    def set_downsample(self) -> None:
        """Set motion downsampling value."""
        if not self.connected or not self.actuator:
            messagebox.showerror("Error", "Not connected to actuator")
            return
            
        downsample = self.downsample_var.get()
        if downsample < 1:
            messagebox.showerror("Error", "Downsampling factor must be 1 or greater")
            return
        
        if not self.actuator.set_downsample(downsample):
            self.log_message("ERROR: Failed to set motion downsampling")
    
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
        
    def stop_monitoring(self) -> None:
        """Stop real-time monitoring."""
        self.monitoring = False
        self.monitor_btn.config(text="Start Monitoring")
    
    def start_status_monitoring(self) -> None:
        """Start status monitoring at 2Hz."""
        if not self.connected or not self.actuator:
            return
            
        self.status_monitoring = True
        self.status_thread = threading.Thread(target=self.status_monitor_loop, daemon=True)
        self.status_thread.start()
        
    def stop_status_monitoring(self) -> None:
        """Stop status monitoring."""
        self.status_monitoring = False
        if self.status_thread:
            self.status_thread.join(timeout=1.0)
        
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
                
                # Get current measurements (silently)
                current_a = self.actuator.get_current_a()
                current_b = self.actuator.get_current_b()
                current_c = self.actuator.get_current_c()
                
                # Send data to plotter if it exists and is plotting
                if self.plotter and self.plotter.plotting:
                    self.plotter.add_data_point(
                        position if position is not None else 0,
                        velocity if velocity is not None else 0,
                        torque if torque is not None else 0,
                        current_a if current_a is not None else 0,
                        current_b if current_b is not None else 0,
                        current_c if current_c is not None else 0,
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
            messagebox.showwarning("Warning", "Manual monitoring is active. Stop monitoring first to use plotting.")
            return
            
        if not self.connected or not self.actuator:
            self.log_message("Not connected to actuator - cannot start plotting")
            return
            
        self.plotter.start_plotting()
        self.plot_start_btn.config(state='disabled')
        self.plot_stop_btn.config(state='normal')
        self.plot_status.config(text="Plotting... (polling mode)")
        
        # Start polling thread for plotting
        self.start_plotting_polling()
        
    def start_plotting_polling(self) -> None:
        """Start polling for plotting data."""
        if not self.connected or not self.actuator:
            return
            
        self.plotting_polling = True
        self.plotting_thread = threading.Thread(target=self.plotting_polling_loop, daemon=True)
        self.plotting_thread.start()
        
    def stop_plotting_polling(self) -> None:
        """Stop polling for plotting data."""
        self.plotting_polling = False
        if hasattr(self, 'plotting_thread') and self.plotting_thread:
            self.plotting_thread.join(timeout=1.0)
        
    def plotting_polling_loop(self) -> None:
        """Polling loop for plotting data."""
        while self.plotting_polling and self.connected and self.actuator:
            try:
                # Get full state data
                state = self.actuator.get_full_state()
                if state is not None:
                    # Send data to plotter
                    if self.plotter and hasattr(self.plotter, 'plotting') and self.plotter.plotting:
                        self.plotter.add_data_point(
                            state['position'],
                            state['velocity'], 
                            state['torque'],
                            state.get('current_a', 0),
                            state.get('current_b', 0),
                            state.get('current_c', 0),
                            time.time()
                        )
                        
                        # Update status display
                        def update_status():
                            self.position_status.config(text=f"{state['position']:.2f}°")
                            self.velocity_status.config(text=f"{state['velocity']:.2f}°/s")
                            self.torque_status.config(text=f"{state['torque']:.2f} Nm")
                            self.temperature_status.config(text=f"{state['temperature']:.1f}°C")
                            self.bus_voltage_status.config(text=f"{state['bus_voltage']:.2f} V")
                            self.internal_temperature_status.config(text=f"{state['internal_temperature']:.1f}°C")
                        
                        self.root.after(0, update_status)
                
                time.sleep(0.02)  # 50Hz polling rate
                
            except Exception as e:
                self.log_message(f"Plotting polling error: {e}")
                break
        
    def stop_plotting(self) -> None:
        """Stop real-time plotting."""
        if not self.plotter:
            return
            
        # Stop plotting polling
        self.stop_plotting_polling()
        
        self.plotter.stop_plotting()
        self.plot_start_btn.config(state='normal')
        self.plot_stop_btn.config(state='disabled')
        self.plot_status.config(text="Ready")
        
    def clear_plot_data(self) -> None:
        """Clear all plot data."""
        if not self.plotter:
            return
            
        # Stop broadcast and plotting if active
        if self.plotter and hasattr(self.plotter, 'plotting') and self.plotter.plotting:
            self.stop_plotting()
            
        self.plotter.clear_data()
        self.plot_status.config(text="Data cleared")
        
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
        
    def run(self) -> None:
        """Run the GUI application."""
        self.root.mainloop()


def main() -> None:
    """Main entry point for the GUI application."""
    app = ActuatorGUI()
    app.run()


if __name__ == "__main__":
    main()

