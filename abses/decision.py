#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

import inspect
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
    Type,
    TypeAlias,
    Union,
)

from abses.tools.func import camel_to_snake

if TYPE_CHECKING:
    from abses.actor import Actor

Strategy: TypeAlias = Union[str, None, bool, Number]


class Decision:
    """Decision class of actor."""

    __strategies__: Optional[Dict] = None
    _strategies: Optional[Dict] = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.validate_strategies(cls.__strategies__)
        cls.set_strategies(cls.__strategies__)

    def __init__(self, agent: Actor = None) -> None:
        self._agent: Actor = agent
        self._strategy: Any = self._setup()

    def __repr__(self) -> str:
        return f"<{self.name}: {self.now}>"

    @classmethod
    @property
    def name(cls) -> str:
        """Get the name of the decision.
        By default, this will be a snake name of class name.
        Users can custom it by assigning a class attribute `name_as`.

        Example:
            ```python
            class TestDecision(Decision):
                pass
            >>> decision = TestDecision()
            >>> decision.name
            >>> 'test_decision'

            class TestDecision(Decision):
                name_as: str = 'decision'
            >>> decision = TestDecision()
            >>> decision.name
            >>> 'decision'
            ```
        """
        default_name = camel_to_snake(cls.__name__)
        return getattr(cls, "name_as", default_name)

    @classmethod
    def validate_strategies(cls, strategies: Strategy):
        """Check if the strategies valid."""
        if not isinstance(strategies, Dict):
            raise TypeError(
                f"So far, only discrete strategies are supported, you should set '__strategies__' class attribute with a dictionary of strategies when subclassing 'Decision', got {type(strategies)} instead."
            )

    @classmethod
    def set_strategies(cls, strategies: Strategy) -> None:
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
    def making(cls, method: Callable) -> Callable:
        """A decorator makes this decision."""

        @wraps(method)
        def decorated(self: Actor, *args, **kwargs):
            cls.validate_decision_maker(self)
            result = method(self, *args, **kwargs)
            cls.validate_strategy(result)
            return result

        decorated.__making__ = cls
        return decorated

    @classmethod
    def response(cls, strategy: Strategy) -> Callable:
        """Change the decorated function into a response methods."""

        def decorator(func) -> Callable:
            @wraps(func)
            def wrapper(self: Actor, *args, **kwargs):
                if not hasattr(self, "decisions"):
                    raise AttributeError(
                        f"{self.breed} doesn't have an attribute 'decisions'"
                    )
                if not isinstance(
                    getattr(self, "decisions"), _DecisionFactory
                ):
                    raise TypeError("Type of a decision must be decision.")
                decision_obj = self.decisions.get(cls.name)
                if not decision_obj.has_strategy(strategy):
                    raise TypeError(
                        f"Decision '{cls.name}' doesn't have strategy {strategy}."
                    )
                return func(self, *args, **kwargs)

            wrapper.__response__ = cls
            wrapper.__expected__ = strategy
            return wrapper

        # decorator.__response__ = cls
        return decorator

    @classmethod
    def validate_decision_maker(cls, agent: Actor):
        """Validate maker of this decision."""
        from abses.actor import Actor

        if not isinstance(agent, Actor):
            raise TypeError(
                f"Decision maker should be an instance of 'Actor' class, got {type(agent)} instead."
            )

    @classmethod
    def validate_strategy(cls, strategy: Strategy) -> None:
        """Validate a strategy choice.

        Parameters:
            strategy:
                The strategy to validate.

        Raises:
            KeyError:
                If the strategy is not a valid choice.
        """
        if not cls.has_strategy(strategy=strategy):
            raise KeyError(
                f"Decision '{cls.__name__}' doesn't have a valid strategy {strategy}."
            )

    @classmethod
    def has_strategy(cls, strategy: Strategy) -> bool:
        """Is a specific strategy existing in this decision?

        Parameters:
            strategy:
                The strategy to validate.

        Returns:
            If the strategy exists, return True, otherwise returns False.
        """
        return strategy in cls.strategies.keys()

    @property
    def now(self) -> Any:
        """The strategy now."""
        return self._strategy

    def _setup(self) -> Any:
        if init_strategy := self.setup():
            self.validate_strategy(init_strategy)
        return init_strategy

    def setup(self) -> None:
        """Overwrite to setup an initial strategy for this decision."""

    def _find_methods(self, symbol="making") -> Callable:
        methods = inspect.getmembers(self.agent, predicate=inspect.ismethod)
        for _, func in methods:
            if hasattr(func, f"__{symbol}__"):
                yield func

    def _make(self) -> Any:
        for making_decision in self._find_methods("making"):
            result = making_decision()
            for response in self._find_methods("response"):
                if response.__expected__ == result:
                    response()
        return self.make()

    def make(self) -> None:
        """Overwrite this method to do something else after make decision."""


class _DecisionFactory:
    """Creating and containing decisions of an agent."""

    def __init__(
        self, agent: Actor, decisions: Optional[Iterable[Decision]] = None
    ) -> None:
        self.agent: Actor = agent
        self._decisions: Dict[str, Decision] = {}
        self.parse_decisions(decisions)

    @property
    def agent(self) -> Actor:
        """Decision-maker, who has these decisions."""
        return self._agent

    @agent.setter
    def agent(self, agent: Actor) -> None:
        from abses.actor import Actor

        if not isinstance(agent, Actor):
            raise TypeError(
                f"Agent must be an instance of 'Actor' class, got {type(agent)} instead."
            )
        self._agent = agent

    def parse_decisions(self, decisions: Iterable[Type[Decision]]):
        """Parse decisions and save into the container.

        Parameters:
            decisions:
                Iterable `Decision` class.

        Raises:
            TypeError:
                If the input decision is not a subclass of `Decision`.
        """
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

    def making(self) -> None:
        """Making decisions."""
        for d in self._decisions.values():
            d._make()
