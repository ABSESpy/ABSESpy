from mesa.datacollection import DataCollector
from mesa.space import SingleGrid

from abses import MainModel

from .agents import SchellingAgent


class Schelling(MainModel):
    """Model class for the Schelling segregation model."""

    def __init__(self, seed=None, **kwargs):
        """Create a new Schelling model.

        Args:
            width: Width of the grid
            height: Height of the grid
            density: Initial chance for a cell to be populated (0-1)
            minority_pc: Chance for an agent to be in minority class (0-1)
            homophily: Minimum number of similar neighbors needed for happiness
            radius: Search radius for checking neighbor similarity
            seed: Seed for reproducibility
        """
        super().__init__(seed=seed, **kwargs)
        height, width = int(self.p.height), int(self.p.width)
        # Initialize grid
        self.grid = SingleGrid(width, height, torus=True)

        # Track happiness
        self.happy = 0

        # Set up data collection
        self.datacollector = DataCollector(
            model_reporters={
                "happy": "happy",
                "pct_happy": lambda m: (m.happy / len(m.agents)) * 100
                if len(m.agents) > 0
                else 0,
                "population": lambda m: len(m.agents),
                "minority_pct": lambda m: (
                    sum(1 for agent in m.agents if agent.type == 1)
                    / len(m.agents)
                    * 100
                    if len(m.agents) > 0
                    else 0
                ),
            },
            agent_reporters={"agent_type": "type"},
        )

        # Create agents and place them on the grid
        for _, pos in self.grid.coord_iter():
            if self.random.random() < self.p.density:
                agent_type = 1 if self.random.random() < self.p.minority_pc else 0
                agent = SchellingAgent(self, agent_type)
                self.grid.place_agent(agent, pos)

        # Collect initial state
        self.datacollector.collect(self)

    def step(self):
        """Run one step of the model."""
        self.happy = 0  # Reset counter of happy agents
        self.agents.shuffle_do("step")  # Activate all agents in random order
        self.datacollector.collect(self)  # Collect data
        self.running = self.happy < len(self.agents)  # Continue until everyone is happy
