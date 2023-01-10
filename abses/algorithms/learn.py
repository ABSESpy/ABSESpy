#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

import numpy as np


# 随机选择一个；根据偏好学习；就是得分 -> 概率
def fermi_ruler(profits_diff, k=0.5):
    # G. Szabó, G. Fáth, "Evolutionary games on graphs," Phys. Rep. 446, 97 2007
    # 1 / (1 + np.exp((n_{sx} - k_h) / k))
    # n_{sx}: 周围邻居中采取与个体x相同策略的邻居数目
    # k_h: degree/2
    # 可以在群体里选择一部分人（从众个体）
    # 可以在群体里定义一部分收益个体
    return 1 / (1 + np.exp(profits_diff / k))
