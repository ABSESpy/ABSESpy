#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

"""
测试对象，对象是所有可以被用户自定义的对象，包括：自然模块，人类模块，子模块，主体。
"""

import pytest

from abses.bases import _Notice, _Observer


@pytest.fixture(name="objects_fixture")
def setup_notice_observer():
    """创造两个可供测试的对象"""
    observer = _Observer()
    notice = _Notice()
    return notice, observer


def test_notice_add_glob_vars(objects_fixture):
    """测试为通知添加全局变量"""
    notice, _ = objects_fixture
    setattr(notice, "new_var", 100)
    notice.add_glob_vars("new_var")
    assert "new_var" in notice.glob_vars
    # 不可以添加没有定义的变量
    with pytest.raises(AttributeError):
        notice.add_glob_vars("missing_var")


def test_notice_attach(objects_fixture):
    """测试添加观察者"""
    notice, observer = objects_fixture
    assert observer not in notice.observers
    notice.attach(observer)
    assert observer in notice.observers


def test_notice_detach(objects_fixture):
    """测试移除观察者"""
    notice, observer = objects_fixture
    notice.attach(observer)
    assert observer in notice.observers
    notice.detach(observer)
    assert observer not in notice.observers


def test_observer_notification(objects_fixture):
    """测试通知观察者"""
    notice, observer = objects_fixture
    setattr(notice, "test_var", 10)
    notice.add_glob_vars("test_var")
    notice.attach(observer)
    assert hasattr(observer, "test_var")
    assert observer.test_var == 10
