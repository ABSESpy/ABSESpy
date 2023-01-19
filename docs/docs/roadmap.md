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
- [x] 变量完成
- [ ] 重构整个项目
	- [ ] Mediator 步骤方法私有
	- [x] Agents Container 单例模式
- [ ] `Actor` 抽象类
	- [ ] Actor 使用 `relationship`储存与其它`agents`的关系
	- [ ] Actor 使用 `ownership` 储存与斑块变量的关系
- [ ] 变量才生成空间数据 `patch`，中间仅作数组运算
- [ ] 测试完毕，模型的测试写稳固
- [ ] 文档初步写完
- [x] 更新图标 zepix

## v-0.0.2 🎉
- [ ] `human` 模块重构，自带图 `graph`
- [ ] 使用新框架设计 Agent 的交互
- [ ] 修改删掉邻居人数不一样的测试问题
- [ ] 变量在返回之前可以按注册时逻辑进行预处理

## v-0.0.3 🎉
- [ ] 并行运算 dask
- [ ] [GPU](https://zhuanlan.zhihu.com/p/148693465) 加速 [cupy](https://www.jianshu.com/p/b5a6ee8564df) 替代一部分的 numpy
- [ ] **Actors** as agent templates from the **IAD framework** and **MoHuB** framework.

## v-0.0.4 🎉
- [ ] 自动生成 SES network
