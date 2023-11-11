# Human behavior modeling framework

Simulating human behavior is paramount in the dynamic realm of Socio-Ecological Systems (SES) modeling. As critical actors, humans play a pivotal role in shaping the interactions and outcomes within SES. Recognizing the complexity and nuances of human actions, ABSESpy introduces an advanced framework to model intricate human behaviors effectively.

<div align="center">
	<img src="https://songshgeo-picgo-1302043007.cos.ap-beijing.myqcloud.com/uPic/MoHuB.png" alt="Drawing" style="width: 400px;"/>
</div>

The beauty of ABSESpy lies in its framework that seamlessly integrates these user-defined functions, creating a smooth workflow that mirrors the intricacies of human behavior in the real world. When implementing this human behavior framework with ABSESpy, users are allowed to define key elements of decision-making step by step with the following concepts:

- **Decision**: First, define the types of decisions that an actor can make. A particular type of decision can be made by various types of actors. However, pre-defining what the decision types are helps users to better understand and organize their models.
- **Perception**: Actors make decisions based on their perception of the surrounding world, including both the natural and social environments.
- **Evaluate**: As the process of evaluating perceptions can vary, different actors may have different methods of evaluating decisions. Users can choose different evaluation methods for the same decision across various actors.
- **Response**: Finally, based on the decision-making process, actors respond and their actions impact the surrounding environment.
