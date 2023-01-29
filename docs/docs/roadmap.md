---
title: roadmap
authors: SongshGeo
date: 2023-01-10
long_name: Agent-Based Social-ecological systems Modelling Framework in Python
name: AB-SESpy
state: open
banner_icon: 💻
banner: "https://songshgeo-picgo-1302043007.cos.ap-beijing.myqcloud.com/uPic/abses_github_repo.svg"
banner_y: 0.52
SES: social-ecological systems
github: https://github.com/SongshGeo
email: songshgeo@gmail.com
website: https://cv.songshgeo.com
---

## [v-0.0.1 🎉](logs/../../logs/v-0.0.1.md)

### Features

- [x] **Actors:** `Actor` 的创建、查改、储存
- [x] **Actors:** 选取可自动更新的行动者集合并读取、更新属性
- [x] **Actors**: 从`Patch`和自己的位置读取属性、改变世界
- [x] **Nature**: 自动读取空间数据作为 `Patch` 变量
- [x] **Nature**: 将 `Actors` 添加到空间并进行位置增删查改
- [x] **Model**: 模型运行自动化，全程记录流程进度日志
- [x] **Experiment**: 自行开始重复实验，参数敏感性分析
- [x] **Document**: 基本功能的介绍
- [x] **Build**: 初步完成项目架构


## v-0.0.2 🎉

- [ ] **API**: 文档初步写完
- [ ] **doc**: 中文 README
- [ ] **example**: 上传第一个大型模型完整案例
- [ ] **human**: 模块自动生成所有主体的复杂网络
- [ ] **Actor**: 使用 `ownership` 储存与斑块变量的关系
- [ ] **Variable**: 变量在返回之前可以按注册时逻辑进行预处理

## v-0.0.3 🎉

- [ ] 使用 `dask` 实现并行运算
- [ ] [GPU](https://zhuanlan.zhihu.com/p/148693465) 加速 [cupy](https://www.jianshu.com/p/b5a6ee8564df) 替代一部分的 numpy
- [ ] **Actors** as agent templates from the **IAD framework** and **MoHuB** framework.

## v-0.0.4 🎉

- [ ] 重构边界 `Boundaries`
