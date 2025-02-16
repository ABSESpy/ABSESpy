#!/usr/bin/env python 3.11.0
# -*-coding:utf-8 -*-
# @Author  : Shuang (Twist) Song
# @Contact   : SongshGeo@gmail.com
# GitHub   : https://github.com/SongshGeo
# Website: https://cv.songshgeo.com/

from datetime import datetime

import pytest

from abses import MainModel
from abses.time import TimeDriver, parse_datetime


class TestTimeInitialization:
    """测试时间驱动器的初始化功能"""

    @pytest.fixture
    def default_time(self) -> TimeDriver:
        """基础时间驱动器"""
        return TimeDriver(MainModel())

    @pytest.fixture
    def yearly_time(self) -> TimeDriver:
        """年度推进的时间驱动器"""
        parameters = {
            "time": {
                "years": 1,
                "start": "2000",
                "end": "2020",
            }
        }
        return TimeDriver(MainModel(parameters=parameters))

    def test_default_initialization(self, default_time):
        """测试默认初始化
        验证:
        1. 当前时间正确设置
        2. 初始状态正确
        """
        now = datetime.now()
        assert default_time.dt.day == now.day
        assert default_time.dt.month == now.month
        assert default_time.dt.year == now.year
        assert default_time.tick == 0
        assert default_time.duration is None
        assert len(default_time.history) == 1

    @pytest.mark.parametrize(
        "params,expected",
        [
            ({"start": "2000"}, 2000),
            ({"start": "2000-01"}, 2000),
            ({"start": "2000-01-01"}, 2000),
        ],
    )
    def test_start_time_formats(self, params, expected):
        """测试不同格式的开始时间
        验证:
        1. 支持多种时间格式
        2. 正确解析年份
        """
        time = TimeDriver(MainModel({"time": params}))
        assert time.year == expected

    def test_invalid_start_time(self):
        """测试无效的开始时间
        验证:
        1. 无效字符串时间
        2. 错误类型时间
        """
        with pytest.raises(ValueError):
            TimeDriver(MainModel({"time": {"start": "invalid"}}))
        with pytest.raises(TypeError):
            TimeDriver(MainModel({"time": {"start": 123}}))


class TestTimeDuration:
    """测试时间步长相关功能"""

    @pytest.fixture
    def base_time(self) -> TimeDriver:
        """从2000年开始的时间驱动器"""
        return TimeDriver(MainModel({"time": {"start": "2000"}}))

    @pytest.mark.parametrize(
        "duration,expected_next",
        [
            ({"years": 1}, 2001),
            ({"years": 5}, 2005),
            ({"years": 10}, 2010),
        ],
    )
    def test_year_duration(self, duration, expected_next):
        """测试年度步长
        验证:
        1. 正确前进指定年数
        2. 历史记录正确更新
        """
        time = TimeDriver(MainModel({"time": {**{"start": "2000"}, **duration}}))
        time.go()
        assert time.year == expected_next
        assert len(time.history) == 2

    @pytest.mark.parametrize(
        "duration",
        [
            {"years": -1},
            {"months": -1},
        ],
    )
    def test_invalid_duration(self, duration):
        """测试无效的时间步长
        验证:
        1. 负数时间单位
        2. 无效时间单位
        """
        with pytest.raises((ValueError, KeyError)):
            TimeDriver(MainModel({"time": duration}))


class TestTimeProgression:
    """测试时间推进功能"""

    @pytest.fixture
    def yearly_time(self) -> TimeDriver:
        """年度推进的时间驱动器"""
        parameters = {
            "time": {
                "years": 1,
                "start": "2000",
                "end": "2020",
            }
        }
        return TimeDriver(MainModel(parameters=parameters))

    def test_normal_progression(self, yearly_time):
        """测试正常时间推进
        验证:
        1. 时间正确前进
        2. 计数器正确增加
        3. 历史记录正确更新
        """
        yearly_time.go()
        assert yearly_time.year == 2001
        assert yearly_time.tick == 1
        assert len(yearly_time.history) == 2

    def test_progression_to_end(self, yearly_time):
        """测试推进到结束时间
        验证:
        1. 正确停止在结束时间
        2. 模型状态正确更新
        """
        yearly_time.go(19)  # 推进到2019年
        assert yearly_time.year == 2019
        yearly_time.go()  # 推进到2020年
        assert yearly_time.year == 2020

    def test_expected_ticks(self, yearly_time):
        """测试预期时间步数
        验证:
        1. 初始预期步数正确
        2. 中途更改时间后预期步数更新
        """
        assert yearly_time.expected_ticks == 20
        yearly_time.to("2019")
        assert yearly_time.expected_ticks == 1


class TestTimeManipulation:
    """测试时间操作功能"""

    @pytest.fixture
    def manipulatable_time(self) -> TimeDriver:
        """可操作的时间驱动器"""
        return TimeDriver(MainModel({"time": {"start": "2000"}}))

    @pytest.mark.parametrize(
        "target,expected_year",
        [
            ("2010", 2010),
            ("2020", 2020),
            ("1900", 1900),
        ],
    )
    def test_time_to(self, manipulatable_time, target, expected_year):
        """测试时间跳转
        验证:
        1. 正确跳转到目标时间
        2. 历史记录正确重置
        """
        manipulatable_time.to(target)
        assert manipulatable_time.year == expected_year
        assert len(manipulatable_time.history) == 1

    def test_invalid_time_to(self, manipulatable_time):
        """测试无效的时间跳转
        验证:
        1. 无效时间字符串
        2. 无效时间类型
        """
        with pytest.raises(ValueError):
            manipulatable_time.to("invalid")
        with pytest.raises(TypeError):
            manipulatable_time.to(123)


class TestTimeComparison:
    """测试时间比较功能"""

    @pytest.fixture
    def time_2000(self) -> TimeDriver:
        """创建一个从2000年开始的 TimeDriver"""
        model = MainModel({"time": {"start": "2000"}})
        return model.time

    @pytest.mark.parametrize(
        "other_time,expected",
        [
            ("1999", True),  # 早于当前时间
            ("2000", False),  # 等于当前时间
            ("2001", False),  # 晚于当前时间
        ],
    )
    def test_time_comparison(
        self, time_2000: TimeDriver, other_time: str, expected: bool
    ):
        """测试时间比较操作
        验证:
        1. 与字符串时间的比较
        2. 与datetime对象的比较
        3. 与其他TimeDriver实例的比较
        """
        other_dt = parse_datetime(other_time)  # 使用我们自己的parse_datetime
        assert (time_2000 > other_dt) == expected


class TestIrregularTime:
    """测试不规则时间模式"""

    @pytest.fixture
    def irregular_time(self) -> TimeDriver:
        """创建一个不规则时间模式的 TimeDriver"""
        model = MainModel({"time": {"irregular": True, "start": "2000"}})
        return model.time

    @pytest.mark.parametrize(
        "kwargs,expected_date",
        [
            ({"years": 1}, "2001"),
            ({"months": 6}, "2000-07-01"),
            ({"days": 15}, "2000-01-16"),
            ({"hours": 12}, "2000-01-01 12:00:00"),
        ],
    )
    def test_irregular_progression(
        self, irregular_time: TimeDriver, kwargs: dict, expected_date: str
    ):
        """测试不规则时间推进
        验证:
        1. 可以按不同时间单位前进
        2. 时间计算准确
        """
        irregular_time.go(ticks=1, **kwargs)
        expected = parse_datetime(expected_date)  # 使用我们自己的parse_datetime
        assert irregular_time.dt == expected
