import numpy as np

from abses import Actor

# Instantiate a random number generator
rng = np.random.default_rng()


class Shop(Actor):
    """
    Shop agent
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.price = 10
        self.area_count = 0
        self.id = rng.integers(
            1e6, 1e7
        )  # FIXME: no two agents should have the same id
        # cached results
        self.next_position = None
        self.next_price = None

    def __repr__(self):
        return f"Shop {self.id}"

    def step(self):
        self.adjust_price()
        self.adjust_position()

    def advance(self):
        self.affect_price()
        self.affect_position()

    def adjust_price(self):
        # Save initial price
        initial_price = self.price

        print(f"Ajusting price for {self.id} currently sits at {self.price}")

        # Build a list of all possible prices
        _possible_prices = [self.price - 1, self.price, self.price + 1]

        # Pair each possible price change to its potential revenue
        _potential_revenues = {}
        for price in _possible_prices:
            self.price = price
            _potential_revenues[price] = (
                self.model.recalculate_areas()[self] * price
            )
        # Check if all potential revenues are 0
        # if so, decrease price by 1
        if all(value == 0 for value in _potential_revenues.values()):
            self.next_price = self.price - 1
        # Otherwise, choose the price with the highest potential revenue
        else:
            self.next_price = max(
                _potential_revenues, key=_potential_revenues.get
            )

        # Reset price to initial price
        self.price = initial_price

        print(f"Next price for {self.id} will be {self.next_price}")

    def adjust_position(self):
        # Save initial position
        initial_pos = self.pos

        # Get all possible candidates for the next position
        _possible_moves = self.model.nature.major_layer.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        # Pair each possible move to their potential areas
        _potential_areas = {}
        for move in _possible_moves:
            self.move_to(move)
            _potential_areas[move] = self.model.recalculate_areas()[self]

        # Single out the store with the highest potential area and savi it
        _choice = max(_potential_areas, key=_potential_areas.get)
        self.next_position = _choice

        # Pull back to initial position if the potential area
        self.move_to(initial_pos)

    def affect_price(self):
        self.price = self.next_price

    def affect_position(self):
        self.move_to(self.next_position)
