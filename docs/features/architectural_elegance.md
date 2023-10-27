# Architectural Elegance for Modular Socio-Ecological Systems Modeling

The beauty of `ABSESpy` lies in its architectural elegance, which offers modularity, flexibility, and user-driven customization. At the heart of `ABSESpy` is its Branch-Leaf structure, which organizes various modules to ensure clear differentiation and integration as needed.

<div align="center">
	<img src="https://songshgeo-picgo-1302043007.cos.ap-beijing.myqcloud.com/uPic/structure.png" alt="Drawing" style="width: 400px;"/>
</div>

## The Branch-Leaf Architecture

The **[Main Model](api/model.md)** is the foundation of `ABSESpy`, which stores several parameters and global variables. Attached to this foundational model are two essential modules:

- **Base Human**: This module focuses on the human aspect, offering insights and simulations related to human behavior, decisions, and interactions.
- **Base Nature**: As the name suggests, this module is all about the natural environments, allowing for simulations and analyses of different ecological components.

This structure is designed because of social-ecological systems' essential components, users can learn more about the background from [this wiki page](#TODO). Users can see [this tutorial](#TODO) for organizing their model to use the architecture fully.

## Loosely coupled sub-modules

Under the umbrella of the basic modules, users can add more sub-modules, tailoring the system to suit complex modeling needs. This extensibility ensures that `ABSESpy` can evolve with your project's requirements.

Every module in `ABSESpy` is loosely coupled. This design choice means users can write their implementations for different functional modules and seamlessly combine them within the overall SES model. A switch mechanism further enhances this feature, enabling users to turn on or off specific module functionalities as required quickly.

## A unique container of agents

In the social-ecological system (SES) context of `ABSESpy`, all entities are termed "`Actors`." These actors are the observers of the model. They are stored in a specialized container, aptly named the **Actors Container**. This container is unique for a specific model so that all the related operations can easily be organized.

## Advantages of the structure

The setups introduced above ensure that:

1. **Separation of Concerns**: Natural modules, which might include multiple spatial data layers, are distinctly separated from human modules. The latter delves into the intricate logic of actor actions across social, economic, and other functional systems.
2. **Modular Testing**: Users can run, test, and analyze different functional modules in isolation, ensuring precise and focused outcomes.
3. **Global to Individual Observations**: While every actor can access global model information, they possess unique attributes, ensuring a blend of macro and micro perspectives.
4. **Structured Parameter Management**: `ABSESpy` employs a well-structured parameter system to manage model parameters. For an in-depth understanding, please refer to the dedicated _[Parameter Management Documentation](#TODO)_.

> [!INFO]In Progress
> This document is a work in progress if you see any errors, or exclusions or have any problems, please [get in touch with us](https://github.com/absespy/ABSESpy/issues).
