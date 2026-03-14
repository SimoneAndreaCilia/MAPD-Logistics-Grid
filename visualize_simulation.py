import json
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Slider, Button
import matplotlib.patches as patches
import numpy as np
import os

class SimulationVisualizer:
    def __init__(self, log_path, env_path):
        # Load Environment
        with open(env_path, 'r') as f:
            self.env_data = json.load(f)
        
        self.grid = np.array(self.env_data['grid'])
        self.grid_size = self.env_data['metadata']['grid_size']
        self.initial_objects = [tuple(obj) for obj in self.env_data.get('objects', [])]
        
        # Load Logs
        with open(log_path, 'r') as f:
            self.log_data = json.load(f)
        
        self.total_frames = len(self.log_data)
        self.current_frame = 0
        self.is_playing = True
        
        # Setup Figure
        self.fig, self.ax = plt.subplots(figsize=(10, 11))
        # Adjust for buttons and slider at the bottom, and HUD on the left
        plt.subplots_adjust(bottom=0.2, top=0.9, left=0.2, right=0.95)
        
        # Setup Colors
        self.cmap = plt.cm.colors.ListedColormap(['white', 'gray', 'royalblue', 'limegreen', 'tomato', 'gold'])
        self.bounds = [-0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5]
        self.norm = plt.cm.colors.BoundaryNorm(self.bounds, self.cmap.N)
        
        self.ax.imshow(self.grid, cmap=self.cmap, norm=self.norm)
        self.ax.set_title("MAPD Logistics - Interactive Swarm Visualizer")
        
        # Agents representation
        self.agent_scatters = []
        self.agent_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        self.max_batteries = [agent['battery'] for agent in self.log_data[0]['agents']]
        self.health_bgs = []
        self.health_fgs = []
        
        for i in range(5):
            sc = self.ax.scatter([], [], c=self.agent_colors[i], s=200, edgecolors='black', label=f'Agent {i}', zorder=5)
            self.agent_scatters.append(sc)
            
            # Health bars
            bg = patches.Rectangle((0, 0), 0.8, 0.15, facecolor='gray', zorder=6)
            fg = patches.Rectangle((0, 0), 0.8, 0.15, facecolor='limegreen', zorder=7)
            self.ax.add_patch(bg)
            self.ax.add_patch(fg)
            self.health_bgs.append(bg)
            self.health_fgs.append(fg)

        # Field of View (FOV)
        self.selected_agent_idx = None
        self.fov_patch = patches.Polygon(np.zeros((4,2)), closed=True, facecolor='white', alpha=0.0, edgecolor='black', linestyle='--', linewidth=1.5, zorder=3)
        self.ax.add_patch(self.fov_patch)

        # Objects representation
        self.object_scatter = self.ax.scatter([], [], c='gold', s=100, marker='D', edgecolors='black', label='Object', zorder=4)
        
        # HUD - Positioned to the left of the grid in the margin
        self.tick_text = self.fig.text(0.05, 0.85, '', fontweight='bold', fontsize=14)
        self.score_text = self.fig.text(0.05, 0.78, '', fontsize=11, bbox=dict(facecolor='white', alpha=0.5))
        self.objs_text = self.fig.text(0.05, 0.73, '', fontsize=11, bbox=dict(facecolor='gold', alpha=0.3))
        self.agent_info_text = self.fig.text(0.05, 0.65, '', fontsize=11, bbox=dict(facecolor='white', alpha=0.0))
        
        # Slider & Buttons
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
        
        # Keyboard & Mouse events
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        
        # Precompute object lifecycle for fast scrubbing
        self.precompute_object_states()
        
        # Initialize legend with explicit handles to avoid empty artist warnings
        self.ax.legend(handles=self.agent_scatters + [self.object_scatter], 
                       loc='upper right', bbox_to_anchor=(1.1, 1), fontsize='small')

    def precompute_object_states(self):
        # We need to know which objects are where at each tick
        # Since the log doesn't list object positions, we recreate it
        self.object_states = []
        current_objs = set(self.initial_objects)
        for tick in self.log_data:
            for agent in tick['agents']:
                if agent['carrying_object']:
                    p = tuple(agent['pos'])
                    if p in current_objs:
                        current_objs.remove(p)
            self.object_states.append(list(current_objs))

    def update_plot(self, frame_idx):
        self.current_frame = int(frame_idx)
        tick_info = self.log_data[self.current_frame]
        agents = tick_info['agents']
        
        # Agents update
        for i, agent in enumerate(agents):
            pos = agent['pos']
            x, y = pos[1], pos[0]
            self.agent_scatters[i].set_offsets([[x, y]])
            
            if agent['carrying_object']:
                self.agent_scatters[i].set_edgecolors('gold')
                self.agent_scatters[i].set_linewidths(3)
            else:
                self.agent_scatters[i].set_edgecolors('black')
                self.agent_scatters[i].set_linewidths(1)
                
            # Health bar update
            # Now displaying raw battery values since agents have 100 or 150 battery
            pct = agent['battery'] / self.max_batteries[i]
            pct = max(0.0, min(1.0, pct))
            
            hx = x - 0.4
            hy = y - 0.45
            self.health_bgs[i].set_xy((hx, hy))
            self.health_fgs[i].set_xy((hx, hy))
            self.health_fgs[i].set_width(0.8 * pct)
            
            if pct > 0.5:
                self.health_fgs[i].set_facecolor('limegreen')
            elif pct > 0.2:
                self.health_fgs[i].set_facecolor('gold')
            else:
                self.health_fgs[i].set_facecolor('red')

        # FOV update
        if self.selected_agent_idx is not None:
            agent = agents[self.selected_agent_idx]
            x, y = agent['pos'][1], agent['pos'][0]
            
            # Manhattan distance 3 diamond: covers cells at distance <= 3
            # We use 3.5 to encompass the full grid cells
            dx = 3.5
            diamond = np.array([
                [x, y - dx],
                [x + dx, y],
                [x, y + dx],
                [x - dx, y]
            ])
            self.fov_patch.set_xy(diamond)
            self.fov_patch.set_alpha(0.2)
            self.fov_patch.set_facecolor(self.agent_colors[self.selected_agent_idx])
            
            role = "Scout" if self.selected_agent_idx >= 3 else "Collector"
            
            info_str = f"Selected: Agent {self.selected_agent_idx}\nRole: {role}\nBattery: {agent['battery']}/{self.max_batteries[self.selected_agent_idx]}\nPos: ({agent['pos'][1]}, {agent['pos'][0]})"
            self.agent_info_text.set_text(info_str)
            self.agent_info_text.set_bbox(dict(facecolor=self.agent_colors[self.selected_agent_idx], alpha=0.3))
        else:
            self.fov_patch.set_alpha(0.0)
            self.agent_info_text.set_text("")
            self.agent_info_text.set_bbox(dict(facecolor='white', alpha=0.0))

        # Objects update
        objs = self.object_states[self.current_frame]
        if objs:
            self.object_scatter.set_offsets([[p[1], p[0]] for p in objs])
        else:
            self.object_scatter.set_offsets(np.empty((0, 2)))

        self.tick_text.set_text(f"Tick: {tick_info['tick']}")
        self.score_text.set_text(f"Score: {tick_info.get('score', 0)}")
        self.objs_text.set_text(f"Objects Left: {tick_info['objects_left']}")
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
        elif event.key in ['0', '1', '2', '3', '4']:
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

    def run_animation(self):
        def animate(i):
            if self.is_playing:
                if self.current_frame < self.total_frames - 1:
                    self.current_frame += 1
                    self.slider.set_val(self.current_frame)
                else:
                    self.is_playing = False
            return []

        ani = animation.FuncAnimation(self.fig, animate, interval=50, blit=False, cache_frame_data=False)
        
        # Grid lines customization
        self.ax.set_xticks(np.arange(-0.5, self.grid_size, 1), minor=True)
        self.ax.set_yticks(np.arange(-0.5, self.grid_size, 1), minor=True)
        self.ax.grid(which='minor', color='black', linestyle='-', linewidth=0.2)
        self.ax.tick_params(which='minor', bottom=False, left=False) # Hide minor ticks but keep grid
        
        plt.show()

if __name__ == "__main__":
    LOG_PATH = os.path.join(os.getcwd(), "log_A.json")
    ENV_PATH = os.path.join(os.getcwd(), "data", "A.json")
    
    if os.path.exists(LOG_PATH) and os.path.exists(ENV_PATH):
        vis = SimulationVisualizer(LOG_PATH, ENV_PATH)
        vis.run_animation()
    else:
        print("Required files not found (log_A.json or data/A.json)")
