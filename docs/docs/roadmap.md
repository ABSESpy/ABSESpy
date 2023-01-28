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

## v-0.0.1 🎉

### Features
- [x] **Actors:** `Actor` 的创建、查改、储存
- [x] **Actors:** 选取可自动更新的行动者集合并读取、更新属性
- [ ] **Actors**: 从`Patch`和自己的位置读取属性、改变世界
- [ ] **Nature**: 自动读取空间数据作为 `Patch` 变量
- [x] **Nature**: 将 `Actors` 添加到空间并进行位置增删查改
- [x] **Model**: 模型运行自动化，全程记录流程进度日志
- [x] **Experiment**: 自行开始重复实验，参数敏感性分析

- [ ] 变量才生成空间数据 `patch`，中间仅作数组运算
- [ ] 初步完成项目文档


## v-0.0.2 🎉
- [ ] 文档初步写完
- [ ] **human**: 模块自动生成所有主体的复杂网络
- [ ] Actor 使用 `ownership` 储存与斑块变量的关系
- [ ] 使用新框架设计 Agent 的交互
- [ ] 修改删掉邻居人数不一样的测试问题
- [ ] 变量在返回之前可以按注册时逻辑进行预处理

## v-0.0.3 🎉
- [ ] 并行运算 dask
- [ ] [GPU](https://zhuanlan.zhihu.com/p/148693465) 加速 [cupy](https://www.jianshu.com/p/b5a6ee8564df) 替代一部分的 numpy
- [ ] **Actors** as agent templates from the **IAD framework** and **MoHuB** framework.

## v-0.0.4 🎉
- [ ] 自动生成 SES network
- [ ] 重构边界 `Boundaries`
