import pytest

from .examples.fire import Forest, Tree


@pytest.mark.parametrize(
    "cfg",
    [
        {"model": {"density": 0.8, "shape": (100, 100)}, "time": {"end": 50}},
        {"model": {"density": 0.2, "shape": (100, 100)}, "time": {"end": 50}},
        {"model": {"density": 0.8, "shape": (100, 100)}, "time": {"end": 10}},
        {"model": {"density": 0.2, "shape": (100, 100)}, "time": {"end": 10}},
    ],
)
class TestFire:
    def test_init(self, cfg):
        """Test initialization."""
        model = Forest(parameters=cfg)
        assert model is not None

    def test_setup(self, cfg):
        """Test setup."""
        model = Forest(parameters=cfg)
        model.run_model()
        assert model.time.tick in [10, 50]
