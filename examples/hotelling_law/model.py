#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
Hotelling's Law model.
"""

import numpy as np
from mesa.time import SimultaneousActivation
from scipy.spatial.distance import cdist

from abses import Actor, ActorsList, MainModel, PatchCell


class Customer(PatchCell):
    """
    Each patch cell represents a customer.
    Customer prefers to buy from the nearest & cheapest shop.
    """

    def find_preference(self):
        """Find the nearest & cheapest shop."""
        stores: ActorsList[Actor] = self.model.actors
        # Create a list of all shops
        prices = stores.array("price")
        # Create a list of all distances from the customer to each shop
        distances = cdist(
            np.array([self.pos]),
            np.array([shop.at.pos for shop in stores]),
        )[0]
        # Pair each shop to its distance & price
        _pair = dict(zip(stores, distances + prices))
        prefer_store = min(_pair, key=_pair.get)
        self.link.by(prefer_store, link_name="prefer")


class Shop(Actor):
    """
    Shop agent
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.price = 10
        self.next_position = None
        self.next_price = None

    @property
    def area_count(self) -> int:
        """Return the number of customers in the shop's area."""
        return len(self.link.get("prefer", direction="out"))

    def step(self):
        self.adjust_price()
        self.adjust_position()

    def advance(self):
        self.affect_price()
        self.affect_position()

    def adjust_price(self):
        """Evaluate the potential revenue for each possible price change.
        Choose the one with the highest potential revenue."""
        # Save initial price
        init_price = self.price

        # Build a list of all possible prices
        _possible_prices = [init_price - 1, init_price, init_price + 1]

        # Pair each possible price change to its potential revenue
        _potential_revenues = {}
        for price in _possible_prices:
            self.price = price
            self.model.recalculate_preferences()
            _potential_revenues[price] = self.area_count * price
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
        self.price = init_price

    def adjust_position(self):
        """Evaluate the potential areas for each possible move.
        Choose the one with the highest potential area."""
        cell_now = self.at
        # Get all possible candidates for the next position
        _possible_moves = self.at.neighboring(moore=True, include_center=False)

        # Pair each possible move to their potential areas
        _potential_areas = {}
        for move in _possible_moves:
            self.move.to(move)
            self.model.recalculate_preferences()
            _potential_areas[move] = self.area_count

        # Single out the store with the highest potential area and save it
        _choice = max(_potential_areas, key=_potential_areas.get)
        self.next_position = _choice

        # Pull back to initial position if the potential area
        self.move.to(cell_now)

    def affect_price(self) -> None:
        """Change the price of the shop to the next price."""
        self.price = self.next_price

    def affect_position(self) -> None:
        """Change the position of the shop to the next position."""
        self.move.to(self.next_position)


class Hotelling(MainModel):
    """
    Model class for the Hotelling's Law example.
    """

    def setup(self):
        self.schedule = SimultaneousActivation(self)
        num_agents = self.params.get("n_agents", 3)
        # Initialize a grid
        layer = self.nature.create_module(
            cell_cls=Customer, how="from_resolution", shape=(10, 10)
        )

        # Create some agents on random cells
        shops = self.agents.new(Shop, num_agents)
        shops.apply(lambda shop: shop.move.to("random", layer=layer))

    def step(self):
        # recalculate areas and assign them to each agent
        self.recalculate_preferences()

    def recalculate_preferences(self):
        """Let all customers (PatchCell) find their preferences shop."""
        self.nature.major_layer.select().trigger("find_preference")
