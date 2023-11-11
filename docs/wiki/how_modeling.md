# How Does a Modeler Build an ABM

source:: https://gistbok.ucgis.org/bok-topics/agent-based-modeling

While there are many approaches to building ABMs, most modeling endeavors consider the concepts below to build a useful model. These concepts are presented in a framework called the Overview, Design Concepts, Details (ODD) Protocol, developed by Grimm et al. (2006), which helps agent-based modelers communicate the details of their model using a common framework.

**4.1 Agents**

The first step in developing any ABM is to define the agents, and individuals represented within the model. Agents represent individuals either moving through space, changing space, or both. Moving agents are the focus of models that typically simulate walking, migrating, driving, evacuating, etc. Models in which agents make space decisions are typically applied to urban growth, agriculture, and resource use processes. Agents can change space directly, for example, by building a road in an undeveloped area, or indirectly by creating a policy that influences other agents to change the landscape. Like people and animals, agents have several states where they can exist. Examples of binary state sets include alive or dead, hungry or satiated, buyer or seller, calm or panicked, etc.

**4.2 Environment**

All agents exist and make decisions within a specified environment. Each agent resides at a specific location for some time and decides whether to move to another location or change some characteristics about that location. Environments can be represented by a gridded space where locations exist as individual cells containing one or more agents at any given time. Alternatively, environments can be represented as networks in which agents exist at nodes and travel across arcs, or as vector spaces in which agents are located at points, along lines, or in polygons. In all cases, locations contain attributes that agents evaluate to determine if they should move or act in a way that changes the characteristics of some location.

**4.3 Behaviors**

Agent behaviors have two important elements: their objectives and decision-making process. To be a legitimate ABM, agents must have at least one explicitly-defined objective they are trying to achieve. This dictates where they move to or how they decide to change a characteristic of where they currently reside. The decision-making process is specified as a set of rules that govern agents' decisions to achieve their objectives. Decisions can be thought of as ‘if-then’ statements, whereby an agent evaluates _if_ it or the environment is in a specific state and _then_ takes an action. For example, an elk agent’s behavior could be written as, _IF I am in a hungry state AND food is low in the current cell, THEN move forward one cell_.   

**4.4 Interaction**

Agents can react with each other either directly or indirectly. Direct interactions take place when the state of an agent is directly impacted by the behavior of another agent. For example, an agent seeking a home to purchase will have a direct interaction with a homeowner who sells that first agent its property. Many ABMs in ecology are defined by direct interactions between predators and their prey. Indirect interactions occur when one agent makes a decision to either move to a new cell or change the cell’s characteristic, which in turn influences what another agent decides to do at some future moment in the simulation.

**4.5 Adapting and Learning**

Some ABMs are coded in ways to allow agents to adapt to system dynamics. Agents can be programmed to behave a certain way under a specific set of circumstances, and then change their behavior when those circumstances change. More sophisticated ABMs program agents to allow them to learn from their actions to improve their decisions in the future. Agents can evaluate how successful their current decision was with regards to helping them achieve their objective. Using an approach like reinforcement learning, for example, provides an agent with positive or negative rewards when it makes beneficial or adverse decisions, respectively, at a specific location. An accumulation of rewards is then used to inform whether or not the agent should take the same action in the future. In this sense, agents become somewhat “intelligent” objects, and the emergent patterns are then a result of a more evolutionary process. Furthermore, more advanced models can be developed in ways to allow agents to utilize learning for generating new behaviors or rules in order to adapt to changing conditions.

**4.6 Time Steps**

The concept of time is important in ABMs due to the fact that such models are simulating dynamic processes. Time is most commonly represented as discrete time steps, where each step is defined by the duration of time that allows all agents the opportunity to evaluate their current state and subsequently take an action. If agent decisions occur relatively rapidly, such as when one is making decisions about how to walk through a crowd, then time steps should be relatively short such that each time step represents several seconds or a single minute. Conversely, if agent actions represent a more gradual process, such as choosing when to purchase a new home and move, then time steps are much longer – on the order of days, months, or years.

**4.7 Stochasticity and the Number of Model Runs**

Stochasticity is a result of agent actions that are probabilistic in nature, such as allowing an agent to turn left 50% of the time when facing a travel impediment. Models with a high number of probabilistic events typically result in highly stochastic processes, which require many runs in order to observe a signal from the spatial patterns emerging from the model simulation. Models with little stochasticity will not exhibit much difference from one run to the other, therefore requiring fewer runs to understand the potential for variation in model outcomes.