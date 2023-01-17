#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/


import numpy as np

from abses.factory import Patch


def get_tested_patches():
    # 在不使用工厂 PatchFactory 的情况下创建一个的 Patch
    shape = (4, 5)
    array = np.arange(20).reshape(shape)
    mask = np.zeros(shape, bool)
    mask[2, 2] = True  # 只有最中间的点是 True

    # 不建立标注数组和空间参考的 patch，测试数学计算
    patch1 = Patch(array, name="no_father", xarray=False)
    # 测试 buffer 函数
    patch2 = Patch(mask, name="no_father_mask", xarray=False)
    return patch1, patch2


def test_arr_calculation():
    patch1, patch2 = get_tested_patches()
    adj8_1 = patch2.arr.buffer(neighbors=8, buffer=1)
    adj8_2 = patch2.arr.buffer(neighbors=8, buffer=2)
    adj4_1 = patch2.arr.buffer(neighbors=4, buffer=1)
    adj4_2 = patch2.arr.buffer(neighbors=4, buffer=2)
    # 只有一个单元格是 True 的矩阵经过 buffer 计算后分别有多少 True 单元格：
    adjs_masks = (adj8_1, adj8_2, adj4_1, adj4_2)
    assert tuple([adj.sum() for adj in adjs_masks]) == (9, 20, 5, 12)

    # 查看哪些位置是 True
    patch = Patch(adj4_1, "adj81")
    cells = patch.arr.where()
    assert cells == [(1, 2), (2, 1), (2, 2), (2, 3), (3, 2)]

    # 没有用 PatchFactory 类创建的 Patch 不可以转换为 xarray
    try:
        patch1.to_xarray()
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
