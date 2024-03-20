---
title: Get Started
authors: Shuang Song
date: 2024-03-10
---

## Introduction

`ABSESpy` has been designed to be a flexible and easy-to-use framework for agent-based modeling (ABM) of social-ecological systems (SES). It is built on top of the [Mesa] framework, which is a popular ABM framework in Python. `ABSESpy` provides a set of tools and utilities to help users to build, run, and analyze ABM models of SESs.

This getting-started tutorial help you to run the simplest workflow with `ABSESpy` framework. If you have agent-based modeling experience and prefer to learn using `ABSESpy` by examples, you can check out the [official examples].

Following diagram shows the basic structure of the `ABSESpy`'s API. Take it easy, you don't have to be familiar with all the features in this beginning stage. You can always go to the [API documentation] page to find a specific feature.

![abses_API](https://songshgeo-picgo-1302043007.cos.ap-beijing.myqcloud.com/uPic/abses_API.png)

## Get `ABSESpy` model running

Assuming you've successfully installed `ABSESpy`, along with all its dependencies, and properly configured the environment to import the module into your workspace. Running the first blank model that performs no action is straightforward - simply import, initialize, and run...

```python title='model.py'
from abses import MainModel

model = MainModel()
model.run_model(steps=3)  # How many steps to run
```

!!! warning

    Without the arg `steps`, `.run_model` will run indefinitely unless stopped manually. Unless the ending condition can be found in the configurations.

## Custom the basic modules

As the name "socio-ecological system" suggests, it usually includes two basic subsystems: social subsystem and ecological subsystem.
Each of these subsystem has multiple processes, and a specific model can only care some of them according to the settings.

`ABSESpy` translates the structure into two modules: human and natural.
Each of the two modules can attach a set of sub-modules for simulating specific processes (This usually needs to be included based on practical issues and expertise).

!!! info

    === "ABSESpy diagram"

        <figure markdown>
        ![model_diagram](https://songshgeo-picgo-1302043007.cos.ap-beijing.myqcloud.com/uPic/model_diragram.png){ width="300" }
        <figcaption>
            Diagram of how `ABSESpy` simulates a SES
            </figcaption>
        </figure>

    === "SES diagram"

        <figure markdown>
        ![SES](https://songshgeo-picgo-1302043007.cos.ap-beijing.myqcloud.com/uPic/ses.png){ width="300" }
        <figcaption>
            Diagram of Socio-ecological System
            </figcaption>
        </figure>

        Structures of `ABSESpy` mimic the basic structure of a social-ecosystem system (SES) (1).
        { .annotate }

        1.  More information of SES can be learned in the [wiki pages](../wiki/about.md).

Therefore, the default model `MainModel` provided by `ABSESpy` has `BaseNature` and `BaseHuman` as the two basic modules. They can be accessed through attributes `human` and `nature`.

!!! Example

    === "human"

        ```python
        model = MainModel()
        type(model.human)

        # output
        >>> abses.human.BaseHuman
        ```

    === "nature"

        ```python
        model = MainModel()
        type(model.nature)

        # output
        >>> abses.nature.BaseNature
        ```

Users can custom the modules by inheriting `BaseNature`, `BaseHuman`, and `MainModel` from the three basic Components (1).
{ .annotate }

1. `ABSESpy` uses the term "Component" representing the modules, including not only `BaseNature` and `BaseHuman`, but also the sub-modules attached with `BaseNature` and `BaseHuman`.

Generally, each users are four methods can

!!! example

    === "model.py"

        ```python title='model.py'
        from abses import MainModel
        # Import the custom modules.
        from human import CustomHuman
        from nature import CustomNature

        model = MainModel(human_class=Human, nature_class=Nature)
        model.run_model(steps=3)  # How many steps to run

        # output
        >>> Setup the nature module.
        >>> Setup the human module.
        >>> Nature in the step 0.
        >>> Human in the step 0.
        >>> Nature in the step 1.
        >>> Human in the step 1.
        >>> Nature in the step 2.
        >>> Human in the step 2.
        >>> End of the nature module.
        >>> End of the human module.
        ```

    === "human.py"

        ```python title='human.py'
        from abses import BaseHuman

        class CustomHuman(BaseHuman):
            """A custom Human module.
            """

            def initialize(self):
                print("Initializing the human module.")

            def setup(self):
                print("Setup the human module.")

            def step(self):
                print(f"Human in the step {self.time.tick}.")

            def end(self):
                print("End of the human module.")
        ```

    === "nature.py"

        ```python title='nature.py'
        from abses import BaseNature

        class CustomNature(BaseNature):
            """A custom Nature module.
            """

            def initialize(self):
                print("Initializing the nature module.")

            def setup(self):
                print("Setup the nature module.")

            def step(self):
                print(f"Nature in the step {self.time.tick}.")

            def end(self):
                print("End of the nature module.")
        ```

    === "File tree"

        ```shell
        root
        └── src
            ├── human.py
            ├── model.py
            └── nature.py
        ```

        The following project structure is recommended for maintaining:

        1. `root` is the project directory.
        2. `src` contains all the source codebase.
        3. `model.py` is your model.
        4. In the`human.py`, custom logics of the social subsystem.
        5. In the `nature.py`, custom logics of the eco-subsystem.

In the above example, we customize the two components `Nature` and `Human`, then import them from source to be used as args for the model.
We wrote four different methods for each component:

- `initialize`: called when the model is initialized.
- `setup`: called when the model is going to start running.
- `step`: called in the each time step of the model.
- `end`: called when the model has finished running.

<!-- By default, the triggered steps for each component are following the workflow bellow: -->

## Create and manage agents

Agent-based model means, some actors will be included in the artificial SES. `ABSESpy` provides an `AgentsContainer` to store and manage the agents, which can be accessed through the attribute `model.agents`. Under the context of SES, an agent sometimes is also called a social `Actor` (1). For creating such actors, we need to import the class `Actor`, which can also be customized by inheriting.
{ .annotate }

1. social actor - who is not only influenced by the system, but also has motility to make decisions for changing the system

```python
from abses import Actor, MainModel


class MyActor(Actor):
    """A customized actor"""

    def say_hi(self) -> str:
        print(f"Hello, world! I'm a new {self.breed}!")


model = MainModel()
actors = model.agents.new(Actor, 5)
my_actor = model.agents.new(MyActor, singleton=True)

my_actor.say_hi()
print(model.agents)

# output
>>> "Hello, world! I'm a new MyActor!"
>>> "<AgentsContainer: (5)Actor; (1)MyActor>"
```

In the above example, we customize the new breed (1) of actor -`MyActor`.
Then, we created five default `Actor` instances and one `MyActor` instance. All of the instances are stored in the `AgentsContainer` and attached to the model, so that users can access, add, delete, query, and change agents anytime they need through the `AgentsContainer`.
{ .annotate }

1. By default, breed of an agent is just it's class name. User can change this behavior by overriding `breed` class property.

## Configuration of the model

As you would have expected, modeling a real-world SES is far more complex than the example codes above. Luckily, one of the zens of `ABSESpy` is to separate the configuration and the model logic. As long as we configure it as follows, you will find that the ABSESpy framework is suitable for modeling of any complexity:

```python title='main.py'
from abses import MainModel, Actor

class MyModel(MainModel):
    """Customized model."""

    def setup(self):
        n_agents = self.params.get('init_agents')
        self.agents.new(Actor, n_agents)

    def step(self):
        n_agents = self.params.get('n_agents')
        self.agents.new(Actor, n_agents)

    def end(self):
        n_agents = len(self.agents)
        print(f"In {self.time}, there are {n_agents} actors.")

# A nested dictionary of parameters
parameters = {
    'time': {'start': '2000-01-01', 'end': '2003-03-21', 'months': 8, 'years': 2},
    'model': {'init_agents': 5, 'n_agents': 1}
}

# Initialize the model and run it.
model = MyModel(parameters=parameters)
model.run_model()
```

Not scared by these parameters, are you? Things are very simple:

1. `MainModel` accepts a nested dictionary as parameters.
2. In the parameters, `time` describes the time start/step/end rules, while `model` provided two parameters which can be parsed by the model.
3. In the `time` section, `start = '2000-01-01'` means when the model start to run, it mimic the day on 01th Jan. 2000. Similarly, `end = '2003-03-21'` means when the model time reach the day on 21th March 2003. Each time step simulates two years and eight months because of two parameters: `months = 8` and `years = 2`.
4. According to the the customized functions `setup`, the model will add some initial actors based on the parameter `init_agents` provided. Similarly, the customized functions `step`, the model will add some actors in each step based on the parameters `n_agents`.
5. Okay! Elementary math time! When will the running model should be end? How many actors will be there when it ends?

```python
# output
>>> "In <TimeDriver: 2005-05-01 00:00:00>, there are 7 actors."
```

!!! tip

    You don't have to worry about writing a long long nested dictionary for the parameters in practice. `ABSESpy` allows users to easily manage complex parameters by [using configuration files].

## What to do for the next

Congratulations! So far, you have become familiar with the main concepts of the `ABSESpy` framework and know how to run a model.

We encourage you to return to our [Guide Checklist], find out the feature or example model which most attractive to you.

Once you've decide to develop your own ABM by using `ABSESpy`, our well-organized [API documentation] should be a good reference. We also have [detailed tutorials] for users from different levels, happy coding!

<!-- Links -->
  [Guide Checklist]: guide_checklist.md
  [detailed tutorials]: ../tutorial/tutorial.md
  [using configuration files]: ../tutorial/beginner/manage_parameters.ipynb
  [API documentation]: ../api/api.md
  [official examples]: ../examples/official.md
  [Mesa]: https://github.com/projectmesa/mesa
