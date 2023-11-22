---
title: "ABSESpy: An agent-based modeling framework for social-ecological systems"
tags:
- "Python"
- "Agent-based model"
- "Social-ecological system"
- "Geography"
- "Social science"
authors:
- name: Shuang Song
  orcid: 0000-0002-8112-8780
  affiliation: 1
- name: Shuai Wang
  affiliation: 1
  corresponding: true
- name: Chentai Jiao
  affiliation: 1
- name: Elías José Mantilla
  affiliation: 2
affiliations:
 - name: Faculty of Geographical Science, Beijing Normal University. 100875, Beijing, China.
   index: 1
 - name: Computational Social Sciences Laboratory, Universidad San Francisco de Quito. Diego de Robles s/n y pampite.
   index: 2
date: 06 November 2023
bibliography: "../refs.bib"
---

## Summary

`ABSESpy` is a novel agent-based modeling (ABM) framework that enhances socio-ecological systems (SES) research fidelity. Addressing critical needs in SES study, such as complex decision-making, scaling, and data integration, it features a Branch-Leaf architecture for clear separation and integration of human and natural subsystems, promoting replicability and model coupling. `ABSESpy` also supports modeling human behavior through well-recognized workflows of perception, decision-making definitions, and responses. Moreover, it advances real-world modeling with multiple time operating modes, accommodating the diverse temporal scales of SES phenomena and integrating time-sensitive event simulations. These innovations position `ABSESpy` as a crucial tool in addressing current gaps in SES research, fostering more ABMs for real-world SES issues.

## Statement of need

Social-ecological systems (SES) represent an integrated concept that recognizes the complex and interdependent dynamics between human societies and ecological systems [@folke2010]. Consisting of decision-making agents (representing people, communities, organizations, and environmental components) capable of following heterogeneous objectives [@levin2013], SES has specific needs for research support from agent-based modeling.

However, ABMs' potential is yet to be fully realized in SES researches. Current challenges, such as incorporating human decision-making, portraying socio-ecological networks, and modeling real-world systems, must be addressed [@schulze2017]. Additionally, issues related to data availability, model validation, replicability, and transparency must be systematically tackled to enhance the reliability and applicability of ABM in this field [@gotts2019].

Developing and refining ABM approaches for social-ecological systems are crucial in light of these needs and challenges [@reyers2018]. At the heart of this should be a modeling framework that is portable, scale-flexible, and capable of expressing the interaction of the decision-making agent with the natural environment or ecosystem. `ABSESpy` represents a significant advancement in this regard, offering several features that address the current gaps in SES modeling.

## Design structures

`ABSESpy` introduces a Branch-Leaf architecture central to its functionality. It facilitates a clear separation of the human and natural subsystems within SES research, aligning with the requisite to enhance replicability and extensibility (**Figure 1**).

<div align="center">
	<img src="https://songshgeo-picgo-1302043007.cos.ap-beijing.myqcloud.com/uPic/structure.png" alt="Drawing" style="width: 400px;"/>
</div>

**Figure 1:** *Structure of main components of `ABSESpy` and its Branch-Leaf architecture of modules.*

Integrated by the `MainModel`, the two primary base modules are named as `Base Human` and `Base Nature`, corresponding to components of a typical SES [@reyers2018]. By this architecture, `ABSESpy` enables the addition of specialized sub-modules, thus promoting a tailored modeling approach. The extension `mesa-geo` is embedded as the base driver for the nature subsystem so that most of the different geographic datasets are compatible (`.tif`, `.nc`, `.json`, `.shp`, et al.).

In the SES context, `ABSESpy` conceptualizes agents as `Actors` managed within a unique `ActorsContainer` and can be referred from a temporary `ActorsList`. In human sub-modules, users can define a series of `Actor`'s references by or link each other (between agent and patch, or agent and agent) by inputting advanced query. It simplifies the agents' organization, ensuring each actor can be searched, operated, and able to access global information.

## Human-behavior modeling framework

`ABSESpy` recognizes the centrality of human behavior in SES and, as such, prioritizes the workflow approaching its simulation. To this end, the framework provides an integrative approach based on popular theories of conceptualizing human decision-making (**Figure 2**) [@schluter2017, @beckage2022].

<div align="center">
	<img src="https://songshgeo-picgo-1302043007.cos.ap-beijing.myqcloud.com/uPic/MoHuB.png" alt="Drawing" style="width: 400px;"/>
</div>

**Figure 2:** *Decision-making workflow for simulating human behavior.*


When practicing, `ABSESpy` provides an advanced behavior simulation framework, including the following main steps:

1. **Perceptions**: From direct environmental observations to social communications, users can define a `perception` variable to represent how agents gather information and form their understanding of the environment.
2. **Decision-making**: By evaluating the potential choices of a decision, decision-making logic can be implemented to capture how human agents might process information and select courses of action.
3. **Response**: Consequent to decision-making, agents exhibit responses for actualizing their strategies —e.g., spatial relocation, attribute changes, altering environment, or other forms of interaction.

By translating theoretical constructs into user-friendly, operational components, `ABSESpy` empowers researchers to bridge the gap between conceptual models and their tangible application in SES.

## Real-world SES modeling enhancements

`ABSESpy` integrates an innovative time control mechanism to bridge the gap between ABMs and real-world SESs. These are attributions from a `TimeDriver` module that manages the association of ABM with real-world time (**Figure 3**).

<div align="center">
	<img src="https://songshgeo-picgo-1302043007.cos.ap-beijing.myqcloud.com/uPic/schedule.png" alt="Drawing" style="width: 400px;"/>
</div>

**Figure 3:** *Calendar time module enhances real-world social-ecological system modeling approaches.*

In addition to the standard tick-based time advancement, users can implement two temporal modes for matching the diverse scales of SES phenomena. (1) In a "Duration Mode," users can define the length of time that each simulation step represents, thus allowing for variable temporal resolutions. This capability enables the model to represent time intervals vary from minutes to years, depending on the specific requirements of the SES being modeled. (2) The "Irregular Mode" addresses the non-uniformity of specific SES processes; this mode allows for irregular time steps, whereby different simulation intervals can represent varying lengths of time. This flexibility is crucial when modeling events that do not follow a linear timeline, such as erratic ecological phenomena or sporadic human activities.

A calendar schedule enables `ABSESpy` to import and utilize dynamic, temporal datasets. `ABSESpy` automates the updating of variables with time-series data, negating the need for manual data refreshes and recalculations. It supports real-time data feeds, ensuring that the model reflects current conditions. The `ABSESpy` introduces a time-based event handler (`time_condition` decorator) based on the same idea. By leveraging this decorator, temporal conditions for executing events can be set, enabling simulations to react to time-specific triggers. This aspect is especially pertinent for phenomena with distinct temporal patterns, like migratory behaviors or seasonal cycles.

## Positioning and comparison

`ABSESpy` facilitates independent module creation, enabling an advanced human behavior framework and providing sophisticated time control and data integration tools. `ABSESpy` allows a more accurate and nuanced representation of SES dynamics, meeting the intricate requirements of real-world problem-solving and decision-making support. Its goal is to become a specialized package for the emerging SES field based on the `mesa` project, similar to the existing `abce` (a package aimed at providing an economic problem modeling framework, also a `mesa` package). Therefore, `ABSESpy` can take advantage of most of the benefits from the related projects (e.g., `mesa` and `mesa-geo`), such as visualization and geographic data processing.

A possible competitor is `AgentPy`, but its goal remains to be a general ABM framework. Due to the need for more mature geographic data processing extensions like `mesa-geo`, building `ABSESpy` on top of the `mesa` project allows users to deal with real-world SES problems while putting less coding effort into setting up their model projects. Currently, many open-source SES models are published on the platform `CoMSES`; they primarily serve as heuristic models using `netlogo` software as their modeling foundation. The visible advantage of `ABSESpy` lies in its well-structured design, which is suitable for large-scale SES modeling projects. It calls upon vast amounts of actual data for real-world problem modeling rather than merely heuristic modeling. Its tree-like structure allows `ABSESpy` users to couple models together, maximizing Python's advantages as a "glue language".

## Acknowledgment

This research has been supported by the National Natural Science Foundation of China (grant no. 42041007) and the National Natural Science Foundation of China Joint Fund for Scientific Research on Yellow River (grant no. U2243601).

## References
