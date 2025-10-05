"""
Real-time data plotting for actuator monitoring.

This module provides real-time plotting capabilities for position,
velocity, and torque data from the actuator.
"""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from typing import Dict, List, Any, Optional
import threading
import time


class ActuatorPlotter:
    """
    Real-time plotter for actuator data.
    
    Provides live plotting of position, velocity, and torque data
    with configurable update rates and data history.
    """
    
    def __init__(self, parent: tk.Widget, max_points: int = 100):
        """
        Initialize the plotter.
        
        Args:
            parent: Parent widget for the plotter
            max_points: Maximum number of data points to display
        """
        self.parent = parent
        self.max_points = max_points
        self.data_history: Dict[str, List[float]] = {
            'time': [],
            'position': [],
            'velocity': [],
            'torque': []
        }
        self.plotting = False
        self.plot_thread: Optional[threading.Thread] = None
        
        # Initialize with fixed 60-second window
        self.window_duration = 60.0  # 60 seconds
        self.current_time = time.time()
        self.initialize_fixed_window()
        
        self.setup_plot()
        
    def initialize_fixed_window(self) -> None:
        """Initialize the plotter with a fixed 60-second window."""
        # Initialize with empty data but fixed time window
        self.data_history = {
            'time': [],
            'position': [],
            'velocity': [],
            'torque': []
        }
        
    def setup_plot(self) -> None:
        """Set up the matplotlib plot."""
        # Create figure with subplots and increased spacing
        self.fig = Figure(figsize=(12, 8), dpi=100)
        self.fig.suptitle('Actuator Real-time Data', fontsize=14, fontweight='bold')
        
        # Create subplots with increased spacing
        self.ax_position = self.fig.add_subplot(3, 1, 1)
        self.ax_velocity = self.fig.add_subplot(3, 1, 2)
        self.ax_torque = self.fig.add_subplot(3, 1, 3)
        
        # Adjust subplot spacing to prevent overlap
        self.fig.subplots_adjust(hspace=0.4)
        
        # Configure subplots with fixed time axis
        self.ax_position.set_title('Position (degrees)')
        self.ax_position.set_ylabel('Position (°)')
        self.ax_position.set_xlim(-self.window_duration, 0)  # Fixed time window
        self.ax_position.grid(True, alpha=0.3)
        
        self.ax_velocity.set_title('Velocity (degrees/second)')
        self.ax_velocity.set_ylabel('Velocity (°/s)')
        self.ax_velocity.set_xlim(-self.window_duration, 0)  # Fixed time window
        self.ax_velocity.grid(True, alpha=0.3)
        
        self.ax_torque.set_title('Torque (Newton-meters)')
        self.ax_torque.set_ylabel('Torque (Nm)')
        self.ax_torque.set_xlabel('Time (seconds)')
        self.ax_torque.set_xlim(-self.window_duration, 0)  # Fixed time window
        self.ax_torque.grid(True, alpha=0.3)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, self.parent)
        self.canvas.draw()
        
        # Initialize empty plots
        self.position_line, = self.ax_position.plot([], [], 'b-', linewidth=2, label='Position')
        self.velocity_line, = self.ax_velocity.plot([], [], 'g-', linewidth=2, label='Velocity')
        self.torque_line, = self.ax_torque.plot([], [], 'r-', linewidth=2, label='Torque')
        
        # Add legends
        self.ax_position.legend()
        self.ax_velocity.legend()
        self.ax_torque.legend()
        
    def add_data_point(self, position: float, velocity: float, torque: float, timestamp: Optional[float] = None) -> None:
        """
        Add a new data point to the plot.
        
        Args:
            position: Position value in degrees
            velocity: Velocity value in degrees/second
            torque: Torque value in Newton-meters
            timestamp: Broadcast timestamp (if None, uses current time)
        """
        if timestamp is None:
            timestamp = time.time()
        
        # Update current time reference
        self.current_time = timestamp
        
        # Add to data history
        self.data_history['time'].append(timestamp)
        self.data_history['position'].append(position)
        self.data_history['velocity'].append(velocity)
        self.data_history['torque'].append(torque)
        
        # Maintain fixed window - remove data older than window_duration
        cutoff_time = timestamp - self.window_duration
        while (self.data_history['time'] and 
               self.data_history['time'][0] < cutoff_time):
            for key in self.data_history:
                self.data_history[key] = self.data_history[key][1:]
        
        # Don't update plot immediately - let the plot loop handle it
        # This prevents blocking the data collection thread
            
    def start_plotting(self) -> None:
        """Start the real-time plotting."""
        self.plotting = True
        self.plot_thread = threading.Thread(target=self.plot_loop, daemon=True)
        self.plot_thread.start()
        
    def stop_plotting(self) -> None:
        """Stop the real-time plotting."""
        self.plotting = False
        
    def plot_loop(self) -> None:
        """Main plotting loop."""
        last_update = 0
        update_interval = 0.02  # 50 Hz update rate for smooth plotting
        
        while self.plotting:
            try:
                current_time = time.time()
                if current_time - last_update >= update_interval:
                    self.update_plot()
                    last_update = current_time
                else:
                    time.sleep(0.001)  # Small sleep to prevent excessive CPU usage
            except Exception as e:
                print(f"Plotting error: {e}")
                break
                
    def update_plot(self) -> None:
        """Update the plot with current data."""
        if not self.data_history['time']:
            return
            
        # Convert to relative time (negative seconds from current time)
        current_time = self.current_time
        relative_time = [t - current_time for t in self.data_history['time']]
            
        # Update position plot
        self.position_line.set_data(relative_time, self.data_history['position'])
        self.ax_position.relim()
        self.ax_position.autoscale_view()
        
        # Update velocity plot
        self.velocity_line.set_data(relative_time, self.data_history['velocity'])
        self.ax_velocity.relim()
        self.ax_velocity.autoscale_view()
        
        # Update torque plot
        self.torque_line.set_data(relative_time, self.data_history['torque'])
        self.ax_torque.relim()
        self.ax_torque.autoscale_view()
        
        # Redraw canvas (use draw() for faster updates)
        self.canvas.draw()
        
    def clear_data(self) -> None:
        """Clear all data from the plot."""
        for key in self.data_history:
            self.data_history[key] = []
            
        # Reset plots
        self.position_line.set_data([], [])
        self.velocity_line.set_data([], [])
        self.torque_line.set_data([], [])
        
        # Redraw
        self.canvas.draw()
        
    def get_canvas(self) -> FigureCanvasTkAgg:
        """Get the matplotlib canvas widget."""
        return self.canvas
        
    def save_plot(self, filename: str) -> None:
        """
        Save the current plot to a file.
        
        Args:
            filename: Path to save the plot
        """
        self.fig.savefig(filename, dpi=300, bbox_inches='tight')


class PlotWindow:
    """
    Standalone window for actuator data plotting.
    
    Provides a separate window with real-time plotting capabilities
    that can be used alongside the main GUI.
    """
    
    def __init__(self, parent: Optional[tk.Tk] = None):
        """
        Initialize the plot window.
        
        Args:
            parent: Parent window (optional)
        """
        self.window = tk.Toplevel(parent) if parent else tk.Tk()
        self.window.title("Actuator Data Plotter")
        self.window.geometry("800x600")
        
        # Create plotter
        self.plotter = ActuatorPlotter(self.window)
        
        # Pack canvas
        self.plotter.get_canvas().get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Control frame
        control_frame = ttk.Frame(self.window)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Control buttons
        self.start_btn = ttk.Button(control_frame, text="Start Plotting", command=self.start_plotting)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_btn = ttk.Button(control_frame, text="Stop Plotting", command=self.stop_plotting)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.clear_btn = ttk.Button(control_frame, text="Clear Data", command=self.clear_data)
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.save_btn = ttk.Button(control_frame, text="Save Plot", command=self.save_plot)
        self.save_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Status label
        self.status_label = ttk.Label(control_frame, text="Ready")
        self.status_label.pack(side=tk.RIGHT)
        
    def start_plotting(self) -> None:
        """Start the plotting."""
        self.plotter.start_plotting()
        self.status_label.config(text="Plotting...")
        
    def stop_plotting(self) -> None:
        """Stop the plotting."""
        self.plotter.stop_plotting()
        self.status_label.config(text="Stopped")
        
    def clear_data(self) -> None:
        """Clear all data."""
        self.plotter.clear_data()
        self.status_label.config(text="Data cleared")
        
    def save_plot(self) -> None:
        """Save the current plot."""
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filename:
            self.plotter.save_plot(filename)
            self.status_label.config(text=f"Saved to {filename}")
            
    def add_data_point(self, position: float, velocity: float, torque: float, timestamp: Optional[float] = None) -> None:
        """
        Add a data point to the plot.
        
        Args:
            position: Position value in degrees
            velocity: Velocity value in degrees/second
            torque: Torque value in Newton-meters
            timestamp: Broadcast timestamp (if None, uses current time)
        """
        self.plotter.add_data_point(position, velocity, torque, timestamp)
        
    def show(self) -> None:
        """Show the plot window."""
        self.window.mainloop()

