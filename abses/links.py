#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from __future__ import annotations

from typing import Dict, Iterable, Iterator, List, Optional, Self, Set


class _LinkNode:
    """节点类"""

    def __init__(self) -> None:
        self._linking_me: Dict[str, Set[Self]] = {}
        self._linking_to: Dict[str, Set[Self]] = {}

    @classmethod
    @property
    def breed(cls) -> str:
        """种类"""
        return cls.__name__

    @property
    def links(self) -> Set[str]:
        """链接"""
        return tuple(self._linking_to.keys())

    def is_linked_by(self, node: _LinkNode, link_name: Optional[str]) -> bool:
        """是否被连接"""
        return node in self._linking_me.get(link_name, set())

    def is_linking_to(self, node: _LinkNode, link_name: Optional[str]) -> bool:
        """是否连接"""
        return node in self._linking_to.get(link_name, set())

    def link_to(
        self,
        node: _LinkNode,
        link_name: Optional[str],
        mutual: bool = False,
    ) -> None:
        """将行动者与其它行动者或地块建立连接"""
        if link_name not in self._linking_to:
            self._linking_to[link_name] = set()
        self._linking_to[link_name].add(node)
        # 如果对方那没有记录被自己连接，那么让它记录
        if not node.is_linked_by(self, link_name):
            node.link_by(self, link_name)
        # 如果是相互连接，那么让对方也连接自己
        if mutual:
            node.link_to(self, link_name, mutual=False)

    def link_by(
        self, node: _LinkNode, link_name: str, mutual: bool = True
    ) -> bool:
        """是否被连接"""
        if link_name not in self._linking_me:
            self._linking_me[link_name] = set()
        self._linking_me[link_name].add(node)
        if not node.is_linking_to(self, link_name):
            node.link_to(self, link_name)
        if mutual:
            node.link_by(self, link_name, mutual=False)

    def _clean_link_name(
        self, link_name: Optional[str | Iterable[str]]
    ) -> List[str]:
        """清理链接名称"""
        if link_name is None:
            link_name = self.links
        if isinstance(link_name, str):
            link_name = [link_name]
        if not isinstance(link_name, Iterable):
            raise TypeError(f"{link_name} is not an iterable.")
        return link_name

    def remove_me_from_others(
        self, link_name: Optional[str | Iterable[str]] = None
    ):
        """将行动者从其它人的链接中移除。"""
        link_name = self._clean_link_name(link_name)
        for name in self.links:
            if name not in link_name:
                continue
            self.clear_links_to(name)
            self.clear_links_by(name)

    def clear_links_to(self, link_name: str) -> None:
        """清除连接"""
        to_clean = self._linking_to.pop(link_name)
        for node in to_clean:
            node.unlink_by(self, link_name, mutual=False)

    def clear_links_by(self, link_name: str) -> None:
        """清除连接"""
        to_clean = self._linking_me.pop(link_name)
        for node in to_clean:
            node.unlink_to(self, link_name, mutual=False)

    def unlink_with(self, node, link_name: str) -> None:
        """删除链接"""
        self.unlink_by(node=node, link_name=link_name)
        self.unlink_to(node=node, link_name=link_name)

    def unlink_to(
        self, node: _LinkNode, link_name: Optional[str], mutual: bool = False
    ):
        """删除连接"""
        self._linking_to[link_name].remove(node)
        if node.is_linked_by(self, link_name):
            node.unlink_by(self, link_name)
        if mutual and node.is_linking_to(self, link_name):
            node.unlink_to(self, link_name, mutual=False)

    def unlink_by(self, node: _LinkNode, link_name: str, mutual: bool = False):
        """删除连接"""
        self._linking_me[link_name].remove(node)
        if node.is_linking_to(self, link_name):
            node.unlink_to(self, link_name)
        if mutual and node.is_linked_by(self, link_name):
            node.unlink_by(self, link_name, mutual=False)

    def linked(self, link_name: str) -> Iterator[_LinkNode]:
        """获取相关联的所有其它主体"""
        return iter(self._linking_to[link_name])
