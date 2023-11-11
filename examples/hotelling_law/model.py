import numpy as np

from abses import MainModel

from .shop import Shop

# Instantiate a random number generator
rng = np.random.default_rng()


# Calculate euclidean distance between two points
def euclidean_distance(x1, y1, x2, y2):
    return np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


class Hotelling(MainModel):
    """
    Model class for the Hotelling's Law example.
    """

    def __init__(self, N, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.num_agents = N

    def setup(self):
        # Initialize a grid of shape (12, 12)
        self.nature.create_module(how="from_resolution", shape=(12, 12))

        # Create a list of agents
        self.agents.create(Shop, self.num_agents)

        # Placed agents on the grid randomly
        positions = rng.integers(12, size=(self.num_agents, 2), dtype=np.int8)

        for i, agent in enumerate(self.actors):
            agent.put_on_layer(
                layer=self.nature.major_layer, pos=tuple(positions[i])
            )

    def step(self):
        # recalculate areas and assign them to each agent
        areas = self.recalculate_areas()

        for shop in self.actors:
            shop.area_count = areas[shop]

        # trigger all agents to step
        self.actors.trigger("step")

        # let price and positional changes take effect
        self.actors.trigger("advance")

    def recalculate_areas(self):
        areas = {}

        for shop in self.actors:
            areas[shop] = 0

        _width = self.nature.major_layer.width  # columns
        _height = self.nature.major_layer.height  # rows

        for i in range(_height):
            for j in range(_width):
                dist = {}
                for shop in self.actors:
                    _dist = (
                        euclidean_distance(i, j, shop.pos[0], shop.pos[1])
                        + shop.price
                    )
                    dist[shop] = _dist
                _choice = min(dist, key=dist.get)
                areas[_choice] += 1

        return areas
