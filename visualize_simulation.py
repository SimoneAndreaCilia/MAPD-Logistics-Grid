import json
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Slider, Button
import matplotlib.patches as patches
import numpy as np
import os
from src.enums import CellType, AgentRole
from src.config import AGENT_STRATEGIES

# Visualization Constants
VIS_CONFIG = {
    'colors': {
        'agents': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
        'object': 'gold',
        'health_bg': 'gray',
        'health_high': 'limegreen',
        'health_med': 'gold',
        'health_low': 'red',
        'fov_edge': 'black'
    },
    'markers': {
        'agent_size': 200,
        'object_size': 100,
        'object_marker': 'D'
    },
    'layout': {
        'fig_size': (10, 11),
        'adjust': {'bottom': 0.2, 'top': 0.9, 'left': 0.2, 'right': 0.95}
    }
}

class SimulationVisualizer:
    def __init__(self, log_path, env_path, fig=None, ax=None):
        # 1. Load Data
        self._load_data(log_path, env_path)
        
        # 2. Setup Figure and Axes
        if fig is None or ax is None:
            self._setup_figure()
        else:
            self.fig = fig
            self.ax = ax
            self._apply_styles()
        
        # 3. Setup Plots
        self._setup_plots()
        
        # 4. Setup HUD
        self._setup_hud()
        
        # 5. Setup Interactive Widgets
        self._setup_widgets()
        
        # 6. Precompute
        self.precompute_object_states()
        
        # Initialize legend
        self.ax.legend(handles=self.agent_scatters + [self.object_scatter], 
                       loc='upper right', bbox_to_anchor=(1.1, 1), fontsize='small')

    def _apply_styles(self):
        """Applies styles to an existing figure/axes."""
        layout = VIS_CONFIG['layout']
        # Setup Colors
        self.cmap = plt.cm.colors.ListedColormap(['white', 'gray', 'royalblue', 'limegreen', 'tomato', 'gold'])
        self.bounds = [-0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5]
        self.norm = plt.cm.colors.BoundaryNorm(self.bounds, self.cmap.N)
        
        self.ax.imshow(self.grid, cmap=self.cmap, norm=self.norm)
        self.ax.set_title("MAPD Logistics - Interactive Swarm Visualizer")

    def _load_data(self, log_path, env_path):
        """Loads environment and log data with defensive checks."""
        try:
            with open(env_path, 'r') as f:
                self.env_data = json.load(f)
            
            with open(log_path, 'r') as f:
                self.log_data = json.load(f)
                
            if not self.log_data:
                raise ValueError("Log data is empty")
                
            self.grid = np.array(self.env_data.get('grid', []))
            self.grid_size = self.env_data.get('metadata', {}).get('grid_size', len(self.grid))
            self.initial_objects = [tuple(obj) for obj in self.env_data.get('objects', [])]
            
            self.total_frames = len(self.log_data)
            self.current_frame = 0
            self.is_playing = True
            
            # Dynamic agent initialization
            first_frame_agents = self.log_data[0].get('agents', [])
            self.num_agents = len(first_frame_agents)
            # Use the battery value from the first frame as the maximum capacity
            self.max_batteries = [agent.get('battery', 150) for agent in first_frame_agents]
            
        except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Critical error loading simulation data: {e}")
            raise

    def _setup_figure(self):
        layout = VIS_CONFIG['layout']
        self.fig, self.ax = plt.subplots(figsize=layout['fig_size'])
        plt.subplots_adjust(**layout['adjust'])
        self._apply_styles()

    def _setup_plots(self):
        colors = VIS_CONFIG['colors']
        markers = VIS_CONFIG['markers']
        
        # Agents representation
        self.agent_scatters = []
        self.health_bgs = []
        self.health_fgs = []
        
        for i in range(self.num_agents):
            color = colors['agents'][i % len(colors['agents'])]
            sc = self.ax.scatter([], [], c=color, s=markers['agent_size'], 
                               edgecolors='black', label=f'Agent {i}', zorder=5)
            self.agent_scatters.append(sc)
            
            # Health bars
            bg = patches.Rectangle((0, 0), 0.8, 0.15, facecolor=colors['health_bg'], zorder=6)
            fg = patches.Rectangle((0, 0), 0.8, 0.15, facecolor=colors['health_high'], zorder=7)
            self.ax.add_patch(bg)
            self.ax.add_patch(fg)
            self.health_bgs.append(bg)
            self.health_fgs.append(fg)

        # FOV
        self.selected_agent_idx = None
        self.fov_patch = patches.Polygon(np.zeros((4,2)), closed=True, facecolor='white', 
                                       alpha=0.0, edgecolor=colors['fov_edge'], 
                                       linestyle='--', linewidth=1.5, zorder=3)
        self.ax.add_patch(self.fov_patch)

        # Objects
        self.object_scatter = self.ax.scatter([], [], c=colors['object'], s=markers['object_size'], 
                                            marker=markers['object_marker'], edgecolors='black', 
                                            label='Object', zorder=4)

    def _setup_hud(self):
        self.tick_text = self.fig.text(0.05, 0.85, '', fontweight='bold', fontsize=14)
        self.score_text = self.fig.text(0.05, 0.78, '', fontsize=11, bbox=dict(facecolor='white', alpha=0.5))
        self.objs_text = self.fig.text(0.05, 0.73, '', fontsize=11, bbox=dict(facecolor=VIS_CONFIG['colors']['object'], alpha=0.3))
        self.agent_info_text = self.fig.text(0.05, 0.57, '', fontsize=11, bbox=dict(facecolor='white', alpha=0.0))

    def _setup_widgets(self):
        ax_slider = plt.axes([0.15, 0.08, 0.7, 0.03])
        self.slider = Slider(ax_slider, 'Tick', 0, self.total_frames - 1, valinit=0, valfmt='%d')
        self.slider.on_changed(self.on_slider_change)
        
        ax_prev = plt.axes([0.35, 0.02, 0.1, 0.04])
        self.btn_prev = Button(ax_prev, '<<')
        self.btn_prev.on_clicked(self.prev_frame)
        
        ax_play = plt.axes([0.46, 0.02, 0.1, 0.04])
        self.btn_play = Button(ax_play, 'Play/Pause')
        self.btn_play.on_clicked(self.toggle_play)
        
        ax_next = plt.axes([0.57, 0.02, 0.1, 0.04])
        self.btn_next = Button(ax_next, '>>')
        self.btn_next.on_clicked(self.next_frame)
        
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)

    def _get_battery_style(self, battery_val, max_battery):
        """Calculates percentage and color for battery health bar."""
        # Safety check for negative values as requested by USER
        safe_val = max(0, battery_val)
        pct = safe_val / max_battery
        pct = min(1.0, pct)
        
        colors = VIS_CONFIG['colors']
        if pct > 0.5:
            color = colors['health_high']
        elif pct > 0.2:
            color = colors['health_med']
        else:
            color = colors['health_low']
            
        return pct, color

    def precompute_object_states(self):
        # We need to know which objects are where at each tick
        # Since the log doesn't list object positions, we recreate it
        self.object_states = []
        self.delivery_counts = [] # List of counts per frame: [[a0, a1, a2, a3, a4], ...]
        
        current_objs = set(self.initial_objects)
        
        # Track the carrying state of each agent from the previous tick
        prev_carrying = {} 
        current_delivery_counts = [0] * self.num_agents
        
        for tick in self.log_data:
            for agent in tick['agents']:
                agent_id = agent['id']
                is_carrying = agent['carrying_object']
                pos = tuple(agent['pos'])
                
                # An object is removed only if the agent was NOT carrying it 
                # and now IS carrying it (transition at its current position)
                if is_carrying and not prev_carrying.get(agent_id, False):
                    if pos in current_objs:
                        current_objs.remove(pos)
                
                # Delivery detection: Transition from True -> False while at Warehouse (2) or Entrance (3)
                if not is_carrying and prev_carrying.get(agent_id, False):
                    # Check cell type from grid using current position
                    if 0 <= pos[0] < self.grid_size and 0 <= pos[1] < self.grid_size:
                        cell_type = self.grid[pos[0], pos[1]]
                        if cell_type in [CellType.WAREHOUSE, CellType.ENTRANCE]:
                            current_delivery_counts[agent_id] += 1
                
                prev_carrying[agent_id] = is_carrying
                
            self.object_states.append(list(current_objs))
            self.delivery_counts.append(list(current_delivery_counts))

    def update_plot(self, frame_idx):
        self.current_frame = int(frame_idx)
        tick_info = self.log_data[self.current_frame]
        agents = tick_info.get('agents', [])
        
        # 1. Update Agents
        self._update_agents_plot(agents)
        
        # 2. Update FOV and Info
        self._update_fov_plot(agents)

        # 3. Update Objects
        self._update_objects_plot()

        # 4. Update HUD
        self._update_hud_plot(tick_info)
        
        self.fig.canvas.draw_idle()

    def _update_agents_plot(self, agents):
        for i, agent in enumerate(agents):
            if i >= len(self.agent_scatters): break
            
            pos = agent.get('pos', [0, 0])
            x, y = pos[1], pos[0]
            self.agent_scatters[i].set_offsets([[x, y]])
            
            # Carrying object highlight
            is_carrying = agent.get('carrying_object', False)
            edge_color = VIS_CONFIG['colors']['object'] if is_carrying else 'black'
            line_width = 3 if is_carrying else 1
            self.agent_scatters[i].set_edgecolors(edge_color)
            self.agent_scatters[i].set_linewidths(line_width)
                
            # Health bar update
            battery_val = agent.get('battery', 0)
            pct, color = self._get_battery_style(battery_val, self.max_batteries[i])
            
            hx, hy = x - 0.4, y - 0.45
            self.health_bgs[i].set_xy((hx, hy))
            self.health_fgs[i].set_xy((hx, hy))
            self.health_fgs[i].set_width(0.8 * pct)
            self.health_fgs[i].set_facecolor(color)

    def _update_fov_plot(self, agents):
        if self.selected_agent_idx is not None and self.selected_agent_idx < len(agents):
            agent = agents[self.selected_agent_idx]
            pos = agent.get('pos', [0, 0])
            x, y = pos[1], pos[0]
            
            # Manhattan distance 3 representation
            dx = 3.5
            diamond = np.array([[x, y - dx], [x + dx, y], [x, y + dx], [x - dx, y]])
            self.fov_patch.set_xy(diamond)
            self.fov_patch.set_alpha(0.2)
            
            agent_color = VIS_CONFIG['colors']['agents'][self.selected_agent_idx % len(VIS_CONFIG['colors']['agents'])]
            self.fov_patch.set_facecolor(agent_color)
            
            role = agent.get('role', "Collector") # Fallback to Collector
            if 'carrying_object' in agent:
                carrying_str = "Yes" if agent['carrying_object'] else "No"
            else:
                carrying_str = "Unknown"
                
            delivered = self.delivery_counts[self.current_frame][self.selected_agent_idx]
            strategy_name = AGENT_STRATEGIES.get(self.selected_agent_idx, "Unknown")
            
            info_str = (f"Selected: Agent {self.selected_agent_idx}\n"
                        f"Role: {role}\n"
                        f"Strategy: {strategy_name}\n"
                        f"Battery: {agent.get('battery', 0)}/{self.max_batteries[self.selected_agent_idx]}\n"
                        f"Carrying: {carrying_str}\n"
                        f"Delivered: {delivered}\n"
                        f"Pos: ({x}, {y})")
            
            self.agent_info_text.set_text(info_str)
            self.agent_info_text.set_bbox(dict(facecolor=agent_color, alpha=0.3))
        else:
            self.fov_patch.set_alpha(0.0)
            self.agent_info_text.set_text("")
            self.agent_info_text.set_bbox(dict(facecolor='white', alpha=0.0))

    def _update_objects_plot(self):
        objs = self.object_states[self.current_frame]
        if objs:
            self.object_scatter.set_offsets([[p[1], p[0]] for p in objs])
        else:
            self.object_scatter.set_offsets(np.empty((0, 2)))

    def _update_hud_plot(self, tick_info):
        self.tick_text.set_text(f"Tick: {tick_info.get('tick', 0)}")
        self.score_text.set_text(f"Score: {tick_info.get('score', 0)}")
        self.objs_text.set_text(f"Objects Left: {tick_info.get('objects_left', 0)}")
        self.fig.canvas.draw_idle()

    def on_slider_change(self, val):
        self.update_plot(val)

    def toggle_play(self, event=None):
        self.is_playing = not self.is_playing

    def next_frame(self, event=None):
        if self.current_frame < self.total_frames - 1:
            self.current_frame += 1
            self.slider.set_val(self.current_frame)

    def prev_frame(self, event=None):
        if self.current_frame > 0:
            self.current_frame -= 1
            self.slider.set_val(self.current_frame)

    def on_key(self, event):
        if event.key == ' ':
            self.toggle_play()
        elif event.key == 'right':
            self.is_playing = False
            self.next_frame()
        elif event.key == 'left':
            self.is_playing = False
            self.prev_frame()
        if event.key in [str(i) for i in range(min(10, self.num_agents))]:
            self.selected_agent_idx = int(event.key)
            self.update_plot(self.current_frame)
        elif event.key == 'escape':
            self.selected_agent_idx = None
            self.update_plot(self.current_frame)

    def on_click(self, event):
        if event.inaxes != self.ax:
            return
            
        # Check if clicked near an agent
        clicked_agent = None
        min_dist = float('inf')
        tick_info = self.log_data[self.current_frame]
        
        for i, agent in enumerate(tick_info['agents']):
            x, y = agent['pos'][1], agent['pos'][0]
            dist = (event.xdata - x)**2 + (event.ydata - y)**2
            if dist < 0.6 and dist < min_dist:
                min_dist = dist
                clicked_agent = i
                
        if clicked_agent is not None:
            if self.selected_agent_idx == clicked_agent:
                self.selected_agent_idx = None # Toggle off
            else:
                self.selected_agent_idx = clicked_agent
            self.update_plot(self.current_frame)

    def run_animation(self, show=True):
        def animate(i):
            if self.is_playing:
                if self.current_frame < self.total_frames - 1:
                    self.current_frame += 1
                    self.slider.set_val(self.current_frame)
                else:
                    self.is_playing = False
            return []

        self.ani = animation.FuncAnimation(self.fig, animate, interval=50, blit=False, cache_frame_data=False)
        
        # Grid lines customization
        self.ax.set_xticks(np.arange(-0.5, self.grid_size, 1), minor=True)
        self.ax.set_yticks(np.arange(-0.5, self.grid_size, 1), minor=True)
        self.ax.grid(which='minor', color='black', linestyle='-', linewidth=0.2)
        self.ax.tick_params(which='minor', bottom=False, left=False) # Hide minor ticks but keep grid
        
        if show:
            plt.show()

def run_visualizer(log_path=None, env_path=None, show=True):
    if log_path is None:
        log_path = os.path.join(os.getcwd(), "log_A.json")
    if env_path is None:
        env_path = os.path.join(os.getcwd(), "data", "A.json")
    
    if os.path.exists(log_path) and os.path.exists(env_path):
        vis = SimulationVisualizer(log_path, env_path)
        vis.run_animation(show=show)
        return vis
    else:
        print(f"Error: Required files not found:\nLog: {log_path}\nEnv: {env_path}")
        return None

if __name__ == "__main__":
    run_visualizer()
