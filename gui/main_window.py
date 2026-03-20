import tkinter as tk
from tkinter import ttk
import sys
import os

# Import GUI components
from .style import *
from .configuration_panel import ConfigurationPanel
from .simulation_display import SimulationDisplay

class SimulationGUI(tk.Tk):
    """
    Main Application Window for MAPD_Logistics simulation.
    Orchestrates the UI layout and coordinates configuration with execution.
    """
    
    def __init__(self, start_callback):
        super().__init__()
        self.start_callback = start_callback
        
        self.title("MAPD_Logistics - Multi-Agent System Simulation")
        self.geometry("1100x750")
        self.configure(bg=COLOR_BG)
        
        # Set window icon (optional, would need an ico file)
        # self.iconbitmap("icon.ico")
        
        self._setup_layout()
        self.centre_window()
        
        # 3. Protocol for window closing
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        """Handle cleanup when the window is closed."""
        try:
            if hasattr(self, 'display_panel'):
                self.display_panel.cleanup()
        except:
            pass
        self.destroy()
        sys.exit(0)

    def _setup_layout(self):
        """Build the main window structure."""
        
        # 0. Bottom Status Bar (Create early so other components can update it during init)
        self.status_bar = tk.Frame(self, bg=COLOR_BG_LIGHT, height=25, bd=1, relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = tk.Label(
            self.status_bar, text="Initializing...", font=FONT_SMALL,
            bg=COLOR_BG_LIGHT, fg=COLOR_FG
        )
        self.status_label.pack(side=tk.LEFT, padx=PADDING_M)

        # 1. Top Bar
        self.top_bar = tk.Frame(self, bg=COLOR_BG_LIGHT, height=50, bd=0)
        self.top_bar.pack(side=tk.TOP, fill=tk.X)
        self.top_bar.pack_propagate(False)
        
        tk.Label(
            self.top_bar, text="MAPD_Logistics Simulation", font=FONT_TITLE, 
            bg=COLOR_BG_LIGHT, fg=COLOR_FG
        ).pack(side=tk.LEFT, padx=PADDING_L)
        
        tk.Label(
            self.top_bar, text="v1.0.0 | Documentation", font=FONT_SMALL,
            bg=COLOR_BG_LIGHT, fg=COLOR_ACCENT, cursor="hand2"
        ).pack(side=tk.RIGHT, padx=PADDING_L)

        # 2. Main Content (Left: Config, Right: Display)
        self.content = tk.Frame(self, bg=COLOR_BG)
        self.content.pack(fill=tk.BOTH, expand=True)

        self.display_panel = SimulationDisplay(self.content)
        self.display_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=PADDING_M, pady=PADDING_M)

        self.config_panel = ConfigurationPanel(
            self.content, 
            start_callback=self._handle_start,
            reset_callback=self._handle_reset
        )
        self.config_panel.pack(side=tk.LEFT, fill=tk.Y, padx=0, pady=0)
        self.config_panel.pack_propagate(False)
        self.config_panel.configure(width=350)

    def centre_window(self):
        """Centres the window on the screen."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def set_status(self, text: str, type: str = "info"):
        """Update the status bar with colored feedback."""
        if not hasattr(self, 'status_label') or not self.status_label.winfo_exists():
            return
            
        color = COLOR_FG
        if type == "error": color = COLOR_ERROR
        elif type == "success": color = COLOR_SUCCESS
        
        self.status_label.config(text=text, fg=color)

    def _handle_start(self, config):
        """Relay configuration to the main entry point callback."""
        self.set_status("Executing simulation with configured parameters...", "success")
        self.display_panel.log_message("Simulation running...")
        
        # We might want to disable buttons while running
        self.config_panel.btn_start.config(state="disabled")
        
        # Use an update to ensure UI reflects the "Simulation running..." message
        self.update()
        
        try:
            # Execute simulation (suppress standalone visualizer)
            log_path, env_path = self.start_callback(config, show_vis=False)
            
            if log_path and env_path:
                self.set_status("Simulation complete. Loading visualization...", "success")
                self.display_panel.load_simulation(log_path, env_path)
                self.set_status("Simulation visualization ready.", "success")
            else:
                self.set_status("Simulation failed to generate logs.", "error")
                
        except Exception as e:
            self.set_status(f"Error: {str(e)}", "error")
            import traceback
            traceback.print_exc()
        finally:
            if hasattr(self, 'config_panel') and self.config_panel.winfo_exists():
                self.config_panel.btn_start.config(state="normal")

    def _handle_reset(self):
        """Reset the status UI."""
        self.set_status("Configuration reset to defaults.", "info")
        self.display_panel.log_message("Waiting for configuration...")

def launch_gui(start_callback):
    """Entry point to launch the GUI standalone."""
    app = SimulationGUI(start_callback)
    app.mainloop()
