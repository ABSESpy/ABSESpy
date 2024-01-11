# Find your start point to use `ABSESpy`

## :thinking: Is `ABSESpy` my thing?

For using `ABSESpy`, you'd better to have basic experience with [Python]. Then, choose the best description of your knowledge background:

[:computer: I'm familiar with ABM](https://groups.google.com/g/absespy){ .md-button }
[:earth_asia: I'm familiar with SES](https://groups.google.com/g/absespy){ .md-button }

:hatching_chick: If you're unfamiliar with ABM or SES, we recommend visiting our [wiki pages] to gain a basic understanding.

## :checkered_flag: I'm familiar with ABM

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

## :checkered_flag: I'm familiar with SES

<!-- 如果你了解SES相关的概念，你应该知道[非线性的突变]是非常重要的特征，ABM的优点就是能够揭示并模拟它们。当然 SES 还有其他特征，我们强烈建议从具体的案例模型开始，了解ABM这个方法如何帮助你识别SES的具体特征。 -->
If you understand the concepts related to SES, you should know that [emergence] is a very important feature, and the advantage of ABM is that it can reveal and simulate it.
Of course, SES has other features, we strongly recommend starting with specific case models to understand how the ABM method can help you identify the specific features of SES.

!!! warning

    We are actively developing different cases, some of the following examples would be available soon.

| SES features      | Related case model                          |
| ----------- | ------------------------------------ |
| :material-merge: Emergence       | :bulb:Forest wild fire  |
| :material-chart-line: Dynamic       | :bulb: Wolf-sheep-grass model |
| :fontawesome-solid-person-circle-question: Human decision making    | :bulb: [Hotelling] |
| :material-police-badge-outline: Real-world policies    | :bulb: Water allocation |

<!-- 还有一件事，如果你有使用Python实现过地表过程/人类社会过程模型，你可以轻松地将它们作为子模块嵌入到`ABSESpy`中使用，因为`ABSESpy`提供了与SES结构完全匹配的框架结构，并且实现了子模块的自由耦合。 -->
One more thing, if you have implemented ecological/social processes models using [Python], you can easily embed them as submodules into an ABM with `ABSESpy`.
This is because `ABSESpy`'s framework structure perfectly [matches the SES structure] and designed for easily coupling.

<!-- links -->
  [get-started tutorial]: ../home/get_started.md
  [emergence]: ../docs/wiki/concepts/emergence.md

  <!-- [wiki pages]: ../wiki/about.md -->
  <!-- [Spatial data]: ../ -->
  [Time control]: ../tutorial/beginner/time_control.ipynb
  <!-- [Data management]: ../ -->
  [Human behavior framework]: ../tutorial/advanced/human_behavior_simulation.ipynb

  [matches the SES structure]: ../tutorial/beginner/organize_model_structure.ipynb
  [Hotelling]: ../tutorial/beginner/hotelling_tutorial.ipynb
