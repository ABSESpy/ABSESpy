---
title: background
authors: SongshGeo
date: 2023-01-10
long_name: Agent-Based Social-ecological systems Modelling Framework in Python
name: AB-SESpy
state: ongoing
banner_icon: 💻
banner: "https://songshgeo-picgo-1302043007.cos.ap-beijing.myqcloud.com/uPic/abses_github_repo.svg"
banner_y: 0.52
SES: social-ecological systems
github: https://github.com/SongshGeo
email: songshgeo@gmail.com
website: https://cv.songshgeo.com
---

## Complex Adaptive Systems (CAS)

## Emergence (or emergent)

> [!INFO]Definition
> Since simple rules produce complex behavior in hard-to-predict ways, the macroscopic behavior of such systems is sometimes called emergent ^[@mitchell2009].

To be more specific, there are **four types of emergencies**:

=== "Simple Emergence"
	![CleanShot2023-01-17at11.29.48@2x](https://songshgeo-picgo-1302043007.cos.ap-beijing.myqcloud.com/uPic/CleanShot%202023-01-17%20at%2011.29.48@2x.png){:style="height:130px; width:200px" align='right'}
	> Without any bottom-top feedback, each component uniquely determines the state at the next moment. This form of emergence is characterised by fragility, where the destruction of a single component can cause the system to stop working.

=== "Weak Emergence"

	> If the macro pattern can only be simulated from the micro components' dynamics, then he is weakly emergent. It can be made stable (e.g., ants foraging) or non-stable (e.g., financial markets, subordination).

=== "Multiple Emergence"

	> Both negative feedback that makes the system stable and positive feedback that makes the system non-stable. Many complex patterns are emergent as a result.

=== "Strong Emergence"

	> Emergent systems that emerge at a higher level of organisation or complexity, such as culture, language and writing systems, life, and geographic zoning...

## Human Behaviour Framework

> [!INFO]Quote
> 	> This framework allows for biases, habituation and other cognitive processes that shape human perception of climate change and the influence of social norms, social learning and other social processes on spreading information and factors that shape decision-making and behaviour ^[@beckage2022].

We applied the framework for representing human behaviour that consists of **cognition, contagion and behavioural response (CCR framework)** ^[@beckage2022]:

=== "Cognition"

	> **Cognition** represents the human processing of information around the ecological system.

=== "Contagion"

	> **Contagion** represents spreading information, beliefs and behaviour through social networks.

=== "Response"

	> **Response** is the resultant behaviour or action.

The `ABSESpy` fully embedded the three aspects of human behaviour in a different part of the model:

1. **Cognition**: developed as an essential feature of each `Actor`.
2. **Contagion**: human model can automatically [generate SEN for modelling](#TODO) this.
3. **Response**: customised by users under the [IAD framework](#TODO) ^[@ostrom2005].

Therefore, to apply this **cognition-contagion-response (CCR)** human behaviour modelling framework, users can follow [this workflow example](#TODO).
