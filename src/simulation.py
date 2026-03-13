from .utils import SimulationLogger, manhattan_distance, has_line_of_sight

class Simulation:
    def __init__(self, env, agents, max_ticks=750):
        self.env = env
        self.agents = agents
        self.max_ticks = max_ticks
        self.current_tick = 0
        self.logger = SimulationLogger()
        self.is_done = False
        
        self.total_objects = len(env.get_ground_truth_objects())
        self.score = 0
        
    def step(self):
        """
        Executes a TICK for the simulation.
        In this round-robin design, each agent in sequence 
        executes a sense->communicate->decide_and_move.
        Each move by a single agent advances time by 1 tick.
        The function runs until `current_tick` advances.
        """
        if self.is_done:
            return
            
        self.handle_communications()
        
        for agent in self.agents:
            if not agent.is_active:
                continue
                
            # Perception
            agent.sense(self.env)
            
            # Populate nearby agents for collision avoidance
            agent.nearby_agents = []
            for other in self.agents:
                if other.id != agent.id and other.is_active:
                    if manhattan_distance(agent.pos, other.pos) <= agent.vision_range:
                        if has_line_of_sight(self.env, agent.pos, other.pos):
                            agent.nearby_agents.append(other.pos)
            
            # Decision and Movement
            moved = agent.decide_and_move(self.env)
            
            if moved:
                self.current_tick += 1
                
                # Record state for this tick
                objects_left = len(self.env.get_ground_truth_objects())
                
                # Quick score calculation (e.g., reward for collected/delivered objects, penalty for average ticks)
                # The score is not well defined, we calculate a simple one.
                objects_collected = self.total_objects - objects_left
                self.score = (objects_collected * 100) - self.current_tick
                
                self.log_state(objects_left)
                
                if objects_left == 0 or self.current_tick >= self.max_ticks:
                    self.is_done = True
                    break
                    
    def log_state(self, objects_left):
        agents_data = []
        for a in self.agents:
            agents_data.append({
                "id": a.id,
                "pos": a.pos,
                "battery": a.battery,
                "carrying_object": a.carrying_object,
                "active": a.is_active
            })
        self.logger.add_tick_state(self.current_tick, agents_data, self.score, objects_left)
        
    def handle_communications(self):
        """
        Check all unique pairs of active agents. 
        If they are within communication range, trigger map/data merging.
        """
        # Reset connection status at the start of the tick
        for agent in self.agents:
            if agent.is_active:
                agent.is_connected = False
                
        for i in range(len(self.agents)):
            a1 = self.agents[i]
            if not a1.is_active:
                continue
            for j in range(i + 1, len(self.agents)):
                a2 = self.agents[j]
                if not a2.is_active:
                    continue
                    
                # Calculate Manhattan Distance
                dist = abs(a1.pos[0] - a2.pos[0]) + abs(a1.pos[1] - a2.pos[1])
                # If they are within range of either agent
                if dist <= a1.comm_range or dist <= a2.comm_range:
                    a1.sync_data(a2)
                    a2.sync_data(a1)
                    a1.is_connected = True
                    a2.is_connected = True
        
    def run(self, log_path="log.json"):
        # Log initial state (Tick 0)
        objects_left = len(self.env.get_ground_truth_objects())
        self.log_state(objects_left)
        
        while not self.is_done:
            self.step()
            
            # Fallback if no more moves are possible (all inactive or similar)
            active_agents = any(a.is_active for a in self.agents)
            if not active_agents:
                self.is_done = True
                
        self.logger.save_log(log_path)
        print(f"Simulation ended at tick {self.current_tick}.")
        print(f"Objects left: {len(self.env.get_ground_truth_objects())}")
        print(f"Log saved to {log_path}")
