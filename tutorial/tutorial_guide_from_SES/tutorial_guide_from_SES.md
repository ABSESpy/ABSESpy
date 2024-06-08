# :checkered_flag: I'm familiar with SES

<!-- 如果你了解SES相关的概念，你应该知道[非线性的突变]是非常重要的特征，ABM的优点就是能够揭示并模拟它们。当然 SES 还有其他特征，我们强烈建议从具体的案例模型开始，了解ABM这个方法如何帮助你识别SES的具体特征。 -->
If you understand the concepts related to SES, you should know that [emergence] is a very important feature, and the advantage of ABM is that it can reveal and simulate it.
Of course, SES has other features, we strongly recommend starting with specific case models to understand how the ABM method can help you identify the specific features of SES.

!!! warning

    We are actively developing different cases, some of the following examples will be available soon.

| SES features      | Related case model                          |
| ----------- | ------------------------------------ |
| :material-merge: Emergence       | :bulb: [Fire]  |
| :material-chart-line: Dynamic       | :bulb: [Predation] |
| :fontawesome-solid-person-circle-question: Human decision making    | :bulb: [Hotelling] |
| :material-police-badge-outline: Real-world policies    | :bulb: Water allocation |

<!-- 还有一件事，如果你有使用Python实现过地表过程/人类社会过程模型，你可以轻松地将它们作为子模块嵌入到`ABSESpy`中使用，因为`ABSESpy`提供了与SES结构完全匹配的框架结构，并且实现了子模块的自由耦合。 -->
One more thing, if you have implemented ecological/social processes models using [Python], you can easily embed them as submodules into an ABM with `ABSESpy`.
This is because `ABSESpy`'s framework structure perfectly [matches the SES structure] and designed for easily coupling.

<!-- links -->
  [emergence]: ../wiki/concepts/emergence.md
  [matches the SES structure]: ../tutorial/beginner/organize_model_structure.ipynb
  [Hotelling]: ../tutorial/beginner/hotelling_tutorial.ipynb
  [Fire]: ../tutorial/completing/fire_tutorial.ipynb
  [Predation]: ../tutorial/beginner/predation_tutorial.ipynb
