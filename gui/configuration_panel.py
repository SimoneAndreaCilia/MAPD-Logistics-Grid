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
        self.num_agents_var = self._create_input_group("Number of Agents (1-50)", "5")
        self.num_agents_var.trace_add("write", lambda *args: self._update_agent_list())
        
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

        # 5. Agent Configuration Table
        tk.Label(self.container, text="Agent Roles & Strategies", font=FONT_BOLD, bg=COLOR_BG_LIGHT, fg=COLOR_FG).pack(anchor=tk.W, pady=(PADDING_M, 2))
        
        # Scrollable area for agent configurations
        self.agent_config_container = tk.Frame(self.container, bg=COLOR_BG, bd=1, relief=tk.SUNKEN)
        self.agent_config_container.pack(fill=tk.BOTH, expand=True, pady=PADDING_S)

        self.canvas = tk.Canvas(self.agent_config_container, bg=COLOR_BG, highlightthickness=0, height=200)
        self.scrollbar = ttk.Scrollbar(self.agent_config_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=COLOR_BG)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Column Headers
        header_frame = tk.Frame(self.scrollable_frame, bg=COLOR_BG)
        header_frame.pack(fill=tk.X, padx=PADDING_S, pady=2)
        tk.Label(header_frame, text="Agent", width=10, bg=COLOR_BG, fg=COLOR_FG, font=FONT_SMALL).pack(side=tk.LEFT)
        tk.Label(header_frame, text="Role", width=15, bg=COLOR_BG, fg=COLOR_FG, font=FONT_SMALL).pack(side=tk.LEFT)
        tk.Label(header_frame, text="Strategy", width=15, bg=COLOR_BG, fg=COLOR_FG, font=FONT_SMALL).pack(side=tk.LEFT)

        self.agent_rows = []
        self.strategies = ["Frontier", "Spiral", "WallFollower", "Greedy", "RandomTarget"]
        self.roles = ["Scout", "Collector", "Coordinator"]

        self._update_agent_list()

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

    def _update_agent_list(self):
        """Update the agent configuration rows based on num_agents_var."""
        try:
            val = self.num_agents_var.get()
            if not val: return
            num_agents = int(val)
            if num_agents > 50: num_agents = 50 # Limit for UI performance
            if num_agents < 1: return
        except ValueError:
            return

        # Clear existing rows
        for row in self.agent_rows:
            for widget in row['widgets']:
                widget.destroy()
            row['frame'].destroy()
        self.agent_rows.clear()

        # Create new rows
        for i in range(num_agents):
            row_frame = tk.Frame(self.scrollable_frame, bg=COLOR_BG)
            row_frame.pack(fill=tk.X, padx=PADDING_S, pady=1)

            label = tk.Label(row_frame, text=f"Agent {i}", width=10, bg=COLOR_BG, fg=COLOR_FG)
            label.pack(side=tk.LEFT)

            # Role Selection
            role_var = tk.StringVar(value=self.roles[i % len(self.roles)])
            role_combo = ttk.Combobox(row_frame, textvariable=role_var, values=self.roles, state="readonly", width=12)
            role_combo.pack(side=tk.LEFT, padx=PADDING_S)

            # Strategy Selection
            strat_var = tk.StringVar(value="Frontier")
            strat_combo = ttk.Combobox(row_frame, textvariable=strat_var, values=self.strategies, state="readonly", width=12)
            strat_combo.pack(side=tk.LEFT, padx=PADDING_S)

            self.agent_rows.append({
                'frame': row_frame,
                'widgets': [label, role_combo, strat_combo],
                'role_var': role_var,
                'strat_var': strat_var
            })

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
        self._update_agent_list()
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
            
            # Collect per-agent configs
            agent_configs = []
            for row in self.agent_rows[:num_agents]:
                agent_configs.append({
                    "role": row['role_var'].get(),
                    "strategy": row['strat_var'].get()
                })

            return {
                "num_agents": num_agents,
                "grid_size": (grid_w, grid_h),
                "duration": duration,
                "battery": battery,
                "agent_configs": agent_configs,
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
