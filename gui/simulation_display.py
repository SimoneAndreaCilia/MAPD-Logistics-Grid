import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from .style import *
from visualize_simulation import SimulationVisualizer

class SimulationDisplay(tk.Frame):
    """
    Component for visualization of the simulation grid.
    Now hosts the embedded Matplotlib visualizer.
    """
    
    def __init__(self, parent):
        super().__init__(parent, bg="white", bd=1, relief=tk.SUNKEN)
        self.visualizer = None
        self.canvas_widget = None
        self._setup_ui()

    def _setup_ui(self):
        """Set up the visualization container and initial placeholder."""
        self.container = tk.Frame(self, bg="white")
        self.container.pack(fill=tk.BOTH, expand=True)
        
        self.placeholder_label = tk.Label(
            self.container, 
            text="Simulation Visualization Area\n[Ready for Live Data]", 
            bg="white", fg=COLOR_BORDER,
            font=FONT_TITLE,
            justify=tk.CENTER
        )
        self.placeholder_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
    def load_simulation(self, log_path: str, env_path: str):
        """Initialize the visualizer and embed it into the frame."""
        # Clear previous visualization if exists
        if self.canvas_widget:
            self.canvas_widget.destroy()
        if self.placeholder_label:
            self.placeholder_label.destroy()
            self.placeholder_label = None

        try:
            # Create a new figure for the GUI with white background
            fig, ax = plt.subplots(figsize=(8, 8), dpi=100)
            fig.patch.set_facecolor("white")
            ax.set_facecolor("white")
            
            # Initialize the visualizer with our figure/axes
            self.visualizer = SimulationVisualizer(log_path, env_path, fig=fig, ax=ax)
            self.visualizer.run_animation(show=False)
            
            # Create the Tkinter canvas
            self.canvas = FigureCanvasTkAgg(fig, master=self.container)
            self.canvas_widget = self.canvas.get_tk_widget()
            self.canvas_widget.pack(fill=tk.BOTH, expand=True)
            self.canvas.draw()
            
        except Exception as e:
            self.log_message(f"Failed to load visualizer: {str(e)}")
            import traceback
            traceback.print_exc()

    def log_message(self, message: str):
        """Update the UI with a status message."""
        if not self.placeholder_label:
            self.placeholder_label = tk.Label(
                self.container, text="", bg="white", fg=COLOR_ACCENT,
                font=FONT_MAIN, justify=tk.CENTER
            )
            self.placeholder_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        self.placeholder_label.config(text=f"Status: {message}")

    def cleanup(self):
        """Stop animations and close figures to allow clean exit."""
        if self.visualizer and hasattr(self.visualizer, 'ani'):
            try:
                self.visualizer.ani.event_source.stop()
            except:
                pass
        
        # Close all figures associated with this display
        plt.close('all')
