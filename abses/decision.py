#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

from functools import wraps
from numbers import Number
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    TypeAlias,
    Union,
)

from abses.tools.func import camel_to_snake

if TYPE_CHECKING:
    from abses.actor import Actor

Strategy: TypeAlias = Union[str, None, bool, Number]


def response(decision: str, strategy: Strategy) -> Callable:
    """Change the decorated function into a response methods."""

    def decorator(func) -> Callable:
        @wraps(func)
        def wrapper(self: Actor, *args, **kwargs):
            if not hasattr(self, "decisions"):
                raise AttributeError(
                    f"{self.breed} doesn't have an attribute 'decisions'"
                )
            if not isinstance(getattr(self, "decisions"), DecisionFactory):
                raise TypeError("Type of a decision must be decision.")
            decision_obj = self.decisions.get(decision)
            if not decision_obj.has_strategy(strategy):
                raise TypeError(
                    f"Decision '{decision}' doesn't have strategy {strategy}."
                )
            return func(self, *args, **kwargs)

        return wrapper

    return decorator


class Decision:
    """Decision class of actor."""

    __strategies__: Optional[Dict] = None
    _strategies: Optional[Dict] = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.validate_strategies(cls.__strategies__)
        cls.set_strategies(cls.__strategies__)

    def __init__(self, agent: Actor = None, name: str = None) -> None:
        self._agent: Actor = agent
        self._name = name

    @property
    def name(self) -> str:
        """Get the name of the decision."""
        if self._name:
            return self._name
        default_name = camel_to_snake(self.__class__.__name__)
        return getattr(self.__class__, "name_as", default_name)

    @classmethod
    def validate_strategies(cls, strategies: Strategy):
        """Check if the strategies valid."""
        if not isinstance(strategies, Dict):
            raise TypeError(
                f"So far, only discrete strategies are supported, you should set '__strategies__' class attribute with a dictionary of strategies when subclassing 'Decision', got {type(strategies)} instead."
            )

    @classmethod
    def set_strategies(cls, strategies: Strategy):
        """Parsing strategies and save into properties."""
        cls._strategies = strategies

    @classmethod
    @property
    def strategies(cls) -> Dict:
        """Possible strategies."""
        return cls._strategies

    @property
    def agent(self) -> Actor:
        """Decision-maker."""
        return self._agent

    @classmethod
    def making(cls, method: Callable):
        """Making this decision."""

        @wraps(method)
        def decorated(self: Actor, *args, **kwargs):
            cls.validate_decision_maker(self)
            self.decisions._register(method)
            result = method(*args, **kwargs)
            cls.validate_strategy(result)
            return result

        return decorated

    @classmethod
    def validate_decision_maker(cls, agent: Actor):
        """Validate maker of this decision."""
        from abses.actor import Actor

        if not isinstance(agent, Actor):
            raise TypeError(
                f"Decision maker should be an instance of 'Actor' class, got {type(agent)} instead."
            )

    @classmethod
    def validate_strategy(cls, strategy: Strategy):
        """Validate a strategy choice."""
        if not cls.has_strategy(strategy=strategy):
            raise KeyError(
                f"Decision '{cls.__name__}' doesn't have a valid strategy {strategy}."
            )

    @classmethod
    def has_strategy(cls, strategy: Strategy) -> bool:
        """Is a specific strategy exist?"""
        return strategy in cls.strategies.keys()

    def _make(self) -> Any:
        return self.make()

    def make(self) -> Any:
        """Make decision."""


class DecisionFactory:
    """Creating and containing decisions of an agent."""

    def __init__(
        self, agent: Actor, decisions: Optional[Iterable[Decision]] = None
    ) -> None:
        self.agent = agent
        self._decisions = {}
        self.parse_decisions(decisions)
        self._methods = {}

    @property
    def agent(self) -> Actor:
        """Decision-maker."""
        return self._agent

    @agent.setter
    def agent(self, agent: Actor) -> None:
        from abses.actor import Actor

        if not isinstance(agent, Actor):
            raise TypeError(
                f"Agent must be an instance of 'Actor' class, got {type(agent)} instead."
            )
        self._agent = agent

    def parse_decisions(self, decisions: Iterable[Decision]):
        """Parse decisions."""
        for d in decisions:
            if not issubclass(d, Decision):
                raise TypeError(
                    f"Decision must be an subclass of 'Decision' class, got {type(d)} instead."
                )
            obj = d(agent=self.agent)
            self._decisions[obj.name] = obj

    def __getattribute__(self, __name: str) -> Any:
        if __name.startswith("_"):
            return super().__getattribute__(__name)
        if __name in self._decisions:
            return self._decisions[__name]
        return super().__getattribute__(__name)

    def keys(self) -> List[str]:
        """Get all decision names."""
        return list(self._decisions.keys())

    def get(self, name: str) -> Decision:
        """Get a decision by its name."""
        if name not in self._decisions:
            raise KeyError(
                f"Decision '{name}' doesn't exist in {self.keys()}."
            )
        return self._decisions[name]

    def making(self):
        """Making decisions."""
        for d in self._decisions.values():
            d._make()

    def _register(self, method: Callable):
        """Register a method as a decision making function."""
        method = getattr(self.agent, method)
