#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/


import numpy as np

from abses.factory import Patch, PatchFactory

creator = "SongshGeo"


def get_tested_patches():
    # 在不使用工厂 PatchFactory 的情况下创建一个的 Patch
    shape = (4, 5)
    mask = np.zeros(shape, bool)
    mask[2, 2] = True  # 只有最中间的点是 True

    # 不建立标注数组和空间参考的 patch，测试数学计算
    # 测试 buffer 函数
    patch2 = Patch(mask, name="no_father_mask", xarray=False)
    return patch2


def test_arr_calculation():
    patch = get_tested_patches()
    adj8_1 = patch.arr.buffer(neighbors=8, buffer=1)
    adj8_2 = patch.arr.buffer(neighbors=8, buffer=2)
    adj4_1 = patch.arr.buffer(neighbors=4, buffer=1)
    adj4_2 = patch.arr.buffer(neighbors=4, buffer=2)
    # 只有一个单元格是 True 的矩阵经过 buffer 计算后分别有多少 True 单元格：
    adjs_masks = (adj8_1, adj8_2, adj4_1, adj4_2)
    assert tuple([adj.sum() for adj in adjs_masks]) == (9, 20, 5, 12)

    # 查看哪些位置是 True
    patch = Patch(adj4_1, "adj81")
    cells = patch.arr.where()
    assert cells == [(1, 2), (2, 1), (2, 2), (2, 3), (3, 2)]

    # 没有用 PatchFactory 类创建的 Patch 不可以转换为 xarray
    try:
        patch.to_xarray()
    except Exception as e:
        assert "father" in e.__str__()


def test_patch_sort():
    # 测试排序
    patch3 = Patch(np.array([[3, 2, 5], [1, 4, 0]]), "sort")

    # 沿着最近的轴排序（不推荐）
    assert (patch3.arr.sort(axis=-1) == np.array([[2, 3, 5], [0, 1, 4]])).all()

    # axis=None 时先应用 `flatten`再排序
    assert (patch3.arr.sort(axis=None) == np.array([0, 1, 2, 3, 4, 5])).all()

    # 沿特定轴排序
    assert (patch3.arr.sort(axis=0) == np.array([[1, 2, 0], [3, 4, 5]])).all()
    assert (patch3.arr.sort(axis=1) == np.array([[2, 3, 5], [0, 1, 4]])).all()


def get_factory_tested_patch():
    base_patch = get_tested_patches()
    adj4_1 = base_patch.arr.buffer(neighbors=4, buffer=1)
    # 创建一个默认的斑块工厂
    ph = PatchFactory(model=30, creator=creator, shape=adj4_1.shape)
    assert ph.shape == adj4_1.shape == ph.geo.shape
    created_patch = ph.create_patch(adj4_1, "adj41")
    return ph, created_patch


# def test_patch_factory_attrs():
#     ph, patch4 = get_factory_tested_patch()
#     # 坐标轴，可以指示每个栅格之间的距离
#     assert (ph.x == np.array([0, 10, 20, 30, 40])).all()
#     assert (ph.y == np.array([0, 10, 20, 30])).all()
#     assert ph.dims == (
#         "x",
#         "y",
#     )  # 维度名称 默认是(x,y)，有些空间数据可能是 (lon, lat), (longitude, latitude)
#     # 掩膜
#     assert (
#         ph.mask
#         == np.array(
#             [
#                 [True, True, True, True, True],
#                 [True, False, False, False, True],
#                 [True, False, False, False, True],
#                 [True, False, False, False, True],
#             ]
#         )
#     ).all()
#     # 没有被掩膜覆盖的地方
#     assert (
#         ph.accessible
#         == np.array(
#             [
#                 [False, False, False, False, False],
#                 [False, True, True, True, False],
#                 [False, True, True, True, False],
#                 [False, True, True, True, False],
#             ]
#         )
#     ).all()
#     assert ph.attrs == {"creator": "SongshGeo"}  # 附加属性
#     assert ph.boundary is None  # 边界情况

#     assert patch4.xda.attrs["creator"] == creator
#     # 默认的坐标参考系统
#     assert ph.show_georef()["crs"] == "WGS 84"
#     assert patch4.rio.area == 100.0


def test_patch_factories():
    shape = (3, 3)
    arr1 = np.ones(shape)
    empty_factory = PatchFactory(model=1, shape=shape)
    empty_factory.geo.setup_from_shape(shape)
    # create through arr
    var1 = empty_factory.create_patch(arr1, "var1")
    # create through a single value
    var2 = empty_factory.create_patch(1, "var2")
    assert var1.all() == var2.all()
    assert var1.name == "var1"

    full_factory = PatchFactory(
        model=1, shape=shape, test="testing extra attr"
    )
    empty_factory.geo.setup_from_shape(shape)
    patch_str = full_factory.create_patch("str", "str_patch")
    assert patch_str.name == "str_patch"
    assert full_factory.attrs["test"] == "testing extra attr"
