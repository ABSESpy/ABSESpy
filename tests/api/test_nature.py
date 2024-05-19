#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""测试自然模块
"""

import numpy as np
import pytest
import rasterio as rio
import rioxarray as rxr
import xarray
from shapely.geometry import box

from abses.actor import Actor
from abses.cells import raster_attribute
from abses.main import MainModel
from abses.nature import PatchCell, PatchModule
from abses.sequences import ActorsList


class MockPatchCell(PatchCell):
    """测试斑块"""

    def __init__(self, *agrs, x=1, y=2, **kwargs):
        super().__init__(*agrs, **kwargs)
        self._x = x
        self._y = y

    @raster_attribute
    def x(self) -> int:
        """x"""
        return self._x

    @x.setter
    def x(self, value) -> None:
        self._x = value

    @raster_attribute
    def y(self) -> int:
        """y"""
        return self._y

    @y.setter
    def y(self, value) -> None:
        self._y = value


class TestPatchModulePositions:
    """测试斑块模型的位置选取"""

    @pytest.mark.parametrize(
        "row, col, expected",
        [
            (0, 1, (0, 1)),
            (1, 1, (1, 1)),
            (1, 0, (1, 0)),
            (0, 0, (0, 0)),
        ],
    )
    def test_pos_and_indices(self, module: PatchModule, row, col, expected):
        """测试位置和索引。
        pos 应该是和 cell 的位置一致
        indices 应该是和 cell 的索引一致。
        """
        # arrange
        cell = module.array_cells[row, col]
        # act / assert
        assert cell.indices == expected

    @pytest.mark.parametrize(
        "index, expected_value",
        [
            ((1, 1), 3),
            ((0, 0), 0),
        ],
    )
    def test_array_cells(self, module: PatchModule, index, expected_value):
        """测试数组单元格"""
        # arrange
        module.apply_raster(np.arange(4).reshape(1, 2, 2), "test")
        # act / assert
        cell = module.array_cells[index[0], index[1]]
        assert cell.test == expected_value


class TestPatchModule:
    """测试斑块模型"""

    @pytest.mark.parametrize(
        "y_changed, expected",
        [
            (2, 8),
            # ('1', '1111'),
            (2.5, 10),
        ],
    )
    def test_setup_attributes(self, model: MainModel, y_changed, expected):
        """测试斑块提取属性"""
        # arrange / act
        module = model.nature.create_module(
            how="from_resolution",
            shape=(2, 2),
            cell_cls=MockPatchCell,
        )
        for cell in module:
            cell.y = y_changed
        # assert
        assert "x" in module.cell_properties
        assert "y" in module.cell_properties
        assert "x" in module.attributes
        assert "y" in module.attributes
        assert len(module.attributes) == 2
        assert module.get_raster("x").sum() == 4
        assert module.get_raster("y").sum() == expected

    @pytest.mark.parametrize(
        "shape, num",
        [
            ((5, 6), 5),
            ((1, 1), 1),
        ],
    )
    def test_properties(self, model: MainModel, shape, num):
        """测试一个斑块模块"""
        # arrange / act
        module = model.nature.create_module(
            how="from_resolution",
            shape=shape,
            cell_cls=MockPatchCell,
        )
        coords = module.coords

        # assert
        assert module.shape2d == shape
        assert module.shape3d == (1, *shape)
        assert module.array_cells.shape == shape
        assert isinstance(module.random.choice(num), (ActorsList, PatchCell))
        assert "x" in coords and "y" in coords
        assert len(coords["x"]) == shape[1]
        assert len(coords["y"]) == shape[0]

    def test_selecting_by_value(self, model: MainModel, module: PatchModule):
        """测试选择斑块"""
        # arrange
        model.agents.new(Actor, singleton=True)
        # act
        cells = module.select("init_value")
        # assert
        assert len(cells) == 3  # init_value = [0, 1, 2, 3]

    @pytest.mark.parametrize(
        "shape, geometry, expected_len, expected_sum",
        [
            ((2, 2), (0, 0, 2, 2), 4, 6),
            ((3, 3), (1, 1, 3, 3), 4, 12),
            ((3, 3), (1, 1, 2, 2), 1, 4),
            ((3, 3), (0, 0, 2, 2), 4, 20),
        ],  # 这里box是从左下角到右上角进行选择的
    )
    def test_selecting_by_geometry(
        self, model: MainModel, shape, geometry, expected_len, expected_sum
    ):
        """测试使用地理图形选择斑块"""
        # arrange
        module = model.nature.create_module(how="from_resolution", shape=shape)
        actor: Actor = module.array_cells[0, 0].agents.new(
            Actor, singleton=True
        )
        module.apply_raster(
            np.arange(shape[0] * shape[1]).reshape(module.shape3d),
            attr_name="test",
        )
        # act
        cells = module.select(where=box(*geometry))
        cells.apply(
            lambda cell: cell.link.to(
                actor, link_name="test_link", mutual=True
            )
        )
        # assert
        assert len(cells) == expected_len
        assert cells.array("test").sum() == expected_sum
        assert actor.link.get("test_link") == cells

    @pytest.mark.parametrize(
        "func_name, attr, data_type, dims",
        [
            ("get_xarray", "test", xarray.DataArray, 2),
            ("get_xarray", None, xarray.DataArray, 3),
            ("get_raster", "test", np.ndarray, 3),
            ("get_raster", None, np.ndarray, 3),
            ("get_rasterio", "test", rio.DatasetReader, 2),
            ("get_rasterio", None, rio.DatasetReader, 2),
        ],
    )
    def test_get_data(
        self, module: PatchModule, attr, data_type, func_name, dims
    ):
        """测试获取数据数组"""
        # arrange
        data = np.random.random(module.shape3d)
        module.apply_raster(data, "test")
        # act
        got_data = getattr(module, func_name)(attr)
        # assert
        assert len(got_data.shape) == dims
        assert isinstance(got_data, data_type), f"{type(got_data)}"

    @pytest.mark.parametrize(
        "cell_pos, linked",
        [
            ((2, 1), (True, True)),
            ((0, 0), (False, False)),
            ((2, 2), (False, True)),
            ((0, 3), (False, True)),
        ],
    )
    def test_cell_linked_by_two_agents(
        self, model: MainModel, cell_pos, linked
    ):
        """测试批量将一些斑块连接到某个主体"""
        # arrange
        module = model.nature.create_module(
            how="from_resolution", shape=(4, 4)
        )
        box1, box2 = box(*(0, 0, 2, 2)), box(*(1, 1, 4, 4))
        agent1 = model.agents.new(Actor, singleton=True, geometry=box1)
        agent2 = model.agents.new(Actor, singleton=True, geometry=box2)

        # act
        module.select(box1).apply(
            lambda c: c.link.to(agent1, "link", mutual=True)
        )
        module.select(box2).apply(
            lambda c: c.link.to(agent2, "link", mutual=True)
        )

        # assert
        row, col = cell_pos
        linked_agents = module.array_cells[row, col].link.get("link")
        assert (agent1 in linked_agents, agent2 in linked_agents) == linked

    @pytest.mark.parametrize(
        "ufunc, expected",
        [
            (lambda c: c.init_value, np.arange(4)),
            (
                lambda c: c.agents.has(),
                np.array([1, 0, 0, 0]),
            ),
        ],
    )
    def test_apply(
        self,
        module: PatchModule,
        ufunc,
        expected,
        cell_0_0: PatchCell,
    ):
        """Testing"""
        # arrange
        cell_0_0.agents.new(Actor, singleton=True)
        # act
        result = module.apply(ufunc=ufunc)
        # assert
        assert result.shape == module.shape2d
        np.testing.assert_array_equal(result, expected.reshape(module.shape2d))

    def test_copy_layer(self, model, module: PatchModule):
        """测试复制图层"""
        layer2 = model.nature.create_module(
            how="copy_layer", layer=module, name="test2"
        )
        assert module.shape2d == layer2.shape2d
        assert layer2.name == "test2"


class TestBaseNature:
    """测试基本自然模块"""

    def test_attributes(self, model: MainModel, module: PatchModule):
        """测试选择主要图层"""
        assert model.nature.major_layer is module
        assert model.nature.total_bounds is module.total_bounds
        assert module in model.nature.modules
        with pytest.raises(TypeError):
            model.nature.major_layer = "Wrong type"

    def test_module_select(self, model: MainModel):
        """测试创建模块"""
        # arrange
        module2 = model.nature.create_module(
            how="from_resolution", name="test", major_layer=True
        )
        # act & assert
        assert model.nature.test is module2
        assert model.nature.major_layer is module2
        assert model.nature.shape2d == module2.shape2d
        assert model.nature.shape3d == module2.shape3d
        result = model.nature.out_of_bounds((3, 3))
        result2 = module2.out_of_bounds((3, 3))
        assert result == result2

    @pytest.mark.parametrize(
        "row, col",
        [
            (53, 156),
            (97, 56),
            (78, 115),
            (67, 87),
            (64, 73),
        ],
    )
    def test_transform(self, model: MainModel, farmland_data, row, col):
        """Test transform point coords."""
        # arrange
        module = model.nature.create_module(
            raster_file=farmland_data, how="from_file"
        )
        xda = rxr.open_rasterio(farmland_data)
        # act
        x1, y1 = xda.rio.transform() * (col, row)
        x = module.coords["x"][col].item()
        y = module.coords["y"][row].item()
        # assert
        assert np.isclose(x, x1, rtol=1e-2), f"{x}: {x1}"
        assert np.isclose(y, y1, rtol=1e-2), f"{y}: {y1}"


class MockModule(PatchModule):
    """用于测试"""


class MockCell(PatchCell):
    """用于测试"""


class TestCreatingNewPatch:
    """测试创建新斑块"""

    @pytest.mark.parametrize(
        "module_cls, cell_cls",
        [
            (PatchModule, PatchCell),
            (MockModule, MockCell),
        ],
    )
    def test_setup_layer(
        self,
        model: MainModel,
        module_cls,
        cell_cls,
    ) -> PatchModule:
        """创建一个新的斑块"""
        # arrange / act
        layer = model.nature.create_module(
            how="from_resolution",
            module_cls=module_cls,
            name="testing",
            cell_cls=cell_cls,
        )
        # assert
        assert layer.name == "testing"
        assert issubclass(module_cls, PatchModule)
        assert issubclass(layer.cell_cls, cell_cls)
        assert isinstance(layer.cells.random.choice(), cell_cls)
        assert isinstance(layer, module_cls)
