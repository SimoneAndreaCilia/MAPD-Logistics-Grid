from .utils import SimulationLogger

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
            
        for agent in self.agents:
            if not agent.is_active:
                continue
                
            # Perception
            agent.sense(self.env)
            
            # Communication with those in range
            agent.communicate(self.agents)
            
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
        
    def run(self, log_path="log.json"):
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
