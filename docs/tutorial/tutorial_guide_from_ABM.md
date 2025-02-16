# :checkered_flag: I'm familiar with ABM

<!-- 如果你了解ABM相关的概念，并有基本的Python编程经验，那么使用`ABSESpy`应该比较容易。
请不要被SES的概念吓到，这只是一个研究人类与环境交互的理论框架。
你只需要明白，使用`ABSESpy`会在哪些方面帮助你提升开发效率，它适用于哪一类多主体建模。

事实上，大多数发表的多主体模型都含有环境要素，只是它们没有用SES的概念。 -->

If you understand the concepts related to ABM and have basic Python programming experience, then using `ABSESpy` should be relatively easy.
Don't be intimidated by the term SES, it's just a theoretical framework for studying human-environment interactions.

!!! note

    In fact, most published ABMs contain an environmental system, they just don't use the concept of SES.

The following table may help you to understand what aspects of using `ABSESpy` can help improve your development efficiency and which type of agent-based modeling it suits.

| Check box      | Related sources                          |
| ----------- | ------------------------------------ |
| :material-grid: A space for the agents to move around; normally a Grid Space.       | :bulb: Spatial data |
| :material-clock-time-two: The model time corresponds to a concrete real world time. | :bulb: [Time control] |
| :material-human-greeting: Agents have decisions to do, like human. | :bulb: [Human behavior framework] |
| :material-database-cog: Data input/output, especially real-world geo-data. | :bulb: Data management |

Besides the above specific features, an overall implementation of ABM by using `ABSESpy` can be found from the [get-started tutorial].

<!-- links -->
  [get-started tutorial]: ../home/get_started.md

  <!-- [wiki pages]: ../wiki/about.md -->
  <!-- [Spatial data]: ../ -->
  [Time control]: ../tutorial/beginner/time_control.ipynb
