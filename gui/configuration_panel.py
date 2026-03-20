import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, List, Optional
from .style import *

class ConfigurationPanel(tk.Frame):
    """
    Configuration panel for setting simulation parameters.
    Handles input validation and provides a modular UI component.
    """
    
    def __init__(self, parent, start_callback, reset_callback):
        super().__init__(parent, bg=COLOR_BG_LIGHT, bd=1, relief=tk.RAISED)
        self.start_callback = start_callback
        self.reset_callback = reset_callback
        
        self._setup_ui()
        self.reset_to_defaults()

    def _setup_ui(self):
        """Initialize UI components."""
        # Content padding
        self.container = tk.Frame(self, bg=COLOR_BG_LIGHT)
        self.container.pack(fill=tk.BOTH, expand=True, padx=PADDING_L, pady=PADDING_L)

        # Title
        tk.Label(
            self.container, 
            text="Simulation Configuration", 
            font=FONT_TITLE, 
            bg=COLOR_BG_LIGHT, 
            fg=COLOR_ACCENT
        ).pack(anchor=tk.W, pady=(0, PADDING_L))

        # 0. Map Selection
        tk.Label(self.container, text="Select Map (A/B)", font=FONT_BOLD, bg=COLOR_BG_LIGHT, fg=COLOR_FG).pack(anchor=tk.W, pady=(0, 2))
        self.map_var = tk.StringVar(value="A")
        self.map_combo = ttk.Combobox(self.container, textvariable=self.map_var, values=["A", "B"], state="readonly")
        self.map_combo.pack(fill=tk.X, pady=(0, PADDING_M))

        # 1. Number of Agents
        self.num_agents_var = self._create_input_group("Number of Agents (1-100)", "5")
        
        # 2. Grid Dimensions
        grid_frame = tk.Frame(self.container, bg=COLOR_BG_LIGHT)
        grid_frame.pack(fill=tk.X, pady=PADDING_S)
        tk.Label(grid_frame, text="Grid Size (W x H)", font=FONT_BOLD, bg=COLOR_BG_LIGHT, fg=COLOR_FG).pack(anchor=tk.W)
        
        dim_inputs = tk.Frame(grid_frame, bg=COLOR_BG_LIGHT)
        dim_inputs.pack(fill=tk.X, pady=2)
        
        self.grid_w_var = tk.StringVar(value="25")
        self.grid_h_var = tk.StringVar(value="25")
        
        tk.Entry(dim_inputs, textvariable=self.grid_w_var, width=5, **STYLE_CONFIG).pack(side=tk.LEFT)
        tk.Label(dim_inputs, text=" x ", bg=COLOR_BG_LIGHT, fg=COLOR_FG).pack(side=tk.LEFT)
        tk.Entry(dim_inputs, textvariable=self.grid_h_var, width=5, **STYLE_CONFIG).pack(side=tk.LEFT)

        # 3. Simulation Duration
        self.duration_var = self._create_input_group("Simulation Ticks (1-10000)", "750")

        # 4. Battery Capacity
        self.battery_var = self._create_input_group("Agent Battery Capacity (10-1000)", "500")

        # 5. Agent Roles (Multi-select)
        tk.Label(self.container, text="Agent Roles", font=FONT_BOLD, bg=COLOR_BG_LIGHT, fg=COLOR_FG).pack(anchor=tk.W, pady=(PADDING_M, 2))
        self.roles_vars = {
            "Scout": tk.BooleanVar(value=True),
            "Collector": tk.BooleanVar(value=True),
            "Coordinator": tk.BooleanVar(value=True)
        }
        roles_frame = tk.Frame(self.container, bg=COLOR_BG_LIGHT)
        roles_frame.pack(fill=tk.X)
        for role, var in self.roles_vars.items():
            tk.Checkbutton(
                roles_frame, text=role, variable=var, 
                bg=COLOR_BG_LIGHT, fg=COLOR_FG, selectcolor=COLOR_BG,
                activebackground=COLOR_BG_LIGHT, activeforeground=COLOR_ACCENT
            ).pack(side=tk.LEFT, padx=(0, PADDING_M))

        # 6. Agent Strategies
        tk.Label(self.container, text="Strategy Algorithm", font=FONT_BOLD, bg=COLOR_BG_LIGHT, fg=COLOR_FG).pack(anchor=tk.W, pady=(PADDING_M, 2))
        self.strategy_var = tk.StringVar(value="Frontier")
        strategies = ["Frontier", "WallFollower", "Spiral", "Greedy", "RandomTarget"]
        # Customizing ttk combo for dark mode is tricky, using a basic dropdown style
        self.strategy_combo = ttk.Combobox(self.container, textvariable=self.strategy_var, values=strategies, state="readonly")
        self.strategy_combo.pack(fill=tk.X, pady=2)

        # Buttons
        button_frame = tk.Frame(self.container, bg=COLOR_BG_LIGHT)
        button_frame.pack(fill=tk.X, pady=(PADDING_L, 0))

        self.btn_reset = tk.Button(
            button_frame, text="Reset to Default", command=self.reset_to_defaults,
            bg=COLOR_BG_LIGHT, fg=COLOR_FG, relief=tk.FLAT, bd=1,
            padx=PADDING_M, pady=PADDING_S, highlightbackground=COLOR_BORDER
        )
        self.btn_reset.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, PADDING_S))

        self.btn_start = tk.Button(
            button_frame, text="Start Simulation", command=self._on_start_click,
            bg=COLOR_ACCENT, fg="white", font=FONT_BOLD, relief=tk.FLAT,
            padx=PADDING_M, pady=PADDING_S
        )
        self.btn_start.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(PADDING_S, 0))

    def _create_input_group(self, label_text: str, default_val: str) -> tk.StringVar:
        """Helper to create a label and entry group."""
        tk.Label(self.container, text=label_text, font=FONT_BOLD, bg=COLOR_BG_LIGHT, fg=COLOR_FG).pack(anchor=tk.W, pady=(PADDING_M, 0))
        var = tk.StringVar(value=default_val)
        entry = tk.Entry(self.container, textvariable=var, **STYLE_CONFIG)
        entry.pack(fill=tk.X, pady=2)
        return var

    def reset_to_defaults(self):
        """Reset all fields to default values."""
        self.map_var.set("A")
        self.num_agents_var.set("5")
        self.grid_w_var.set("25")
        self.grid_h_var.set("25")
        self.duration_var.set("750")
        self.battery_var.set("500")
        self.strategy_var.set("Frontier")
        for var in self.roles_vars.values():
            var.set(True)
        if self.reset_callback:
            self.reset_callback()

    def _validate_inputs(self) -> Optional[Dict[str, Any]]:
        """Validate user inputs and return a config dict."""
        try:
            num_agents = int(self.num_agents_var.get())
            if not (1 <= num_agents <= 100): raise ValueError("Agents must be 1-100")
            
            grid_w = int(self.grid_w_var.get())
            grid_h = int(self.grid_h_var.get())
            if not (10 <= grid_w <= 500 and 10 <= grid_h <= 500):
                raise ValueError("Grid dim must be 10-500")
                
            duration = int(self.duration_var.get())
            if not (1 <= duration <= 10000): raise ValueError("Ticks must be 1-10000")
            
            battery = int(self.battery_var.get())
            if not (10 <= battery <= 1000): raise ValueError("Battery must be 10-1000")
            
            selected_roles = [role for role, var in self.roles_vars.items() if var.get()]
            if not selected_roles:
                raise ValueError("At least one role must be selected")

            return {
                "num_agents": num_agents,
                "grid_size": (grid_w, grid_h),
                "duration": duration,
                "battery": battery,
                "roles": selected_roles,
                "strategy": self.strategy_var.get(),
                "map_name": self.map_var.get()
            }
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
            return None

    def _on_start_click(self):
        """Handle start button click."""
        config = self._validate_inputs()
        if config and self.start_callback:
            self.start_callback(config)
