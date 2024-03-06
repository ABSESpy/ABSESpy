#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from typing import Optional, Set

from abses.links import LinkNode

try:
    import networkx as nx
except ImportError as exc:
    raise ImportError(
        "You need to install networkx to use this function."
    ) from exc


def convert_to_networkx(
    nodes: Set[LinkNode], link_name: Optional[str]
) -> nx.Graph:
    """Convert a set of LinkNodes to a networkx graph."""
    graph = nx.Graph()
    graph.add_nodes_from(nodes)  # 添加节点
    for node in nodes:
        for target in node.linked(link_name=link_name):
            # 添加边，并标注连接类型
            graph.add_edge(node, target, link_name=link_name)
    return graph
