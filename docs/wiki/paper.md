---
title: "ABSESpy: A Python package for social-ecological system modeling"
author: ['Shuang Song', 'Elías José Mantilla', 'Boyu Wang', 'Andrew Crooks', 'Shuai Wang^*']
uni: Beijing Normal University
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
- name: Shuai Wang^[corresponding author]
  affiliation: 1
  corresponding: true
- name: Boyu Wang
  affiliation: 2
- name: Andrew Crooks
  affiliation: 2
- name: Elías José Mantilla
  affiliation: 3
affiliations:
 - name: Beijing Normal University
   index: 1
 - name: School of Engineering, University of Applied Sciences Saarbrücken, Goebenstr. 40, 66117 Saarbrücken, Germany
   index: 2
date: 06 November 2023
bibliography: paper.bib
---
## Summary

`ABSESpy` is a novel agent-based modeling framework designed to enhance the fidelity of socio-ecological systems (SES) research. Addressing critical needs in SES study, such as complex decision-making, scaling, and data integration, it features a Branch-Leaf architecture for clear separation and integration of human and natural elements, promoting replicability and scalability. The system supports dynamic human behavior modeling through advanced interaction, perception, decision-making definitions, and appropriate response mechanisms. Moreover, `ABSESpy` advances temporal modeling with multiple time management modes, accommodating the diverse temporal scales of SES phenomena and integrating time-sensitive event simulations. These innovations position `ABSESpy` as a crucial tool in addressing current gaps in SES research, fostering more reliable and applicable outcomes in understanding and managing socio-ecological interactions.

## Statement of need

Social-ecological systems (SES) represent an integrated concept that recognizes the complex and interdependent dynamics between human societies and ecological systems [@folke2010]. Consisting of decision-making agents (representing people, communities, organizations, and environmental components) capable of following heterogeneous objectives [@levin2013], SES has specific needs for research support from agent-based modeling.

However, ABMs' potential is yet to be fully realized in SES research. Current challenges, such as accurately reflecting human decision-making, integrating social networks, scaling, and modeling adaptation and learning, need to be addressed [@schulze2017]. Additionally, issues related to data availability, model validation, replicability, and transparency must be systematically tackled to enhance the reliability and applicability of ABM in this field [@gotts2019].

Developing and refining ABM approaches for social-ecological systems are crucial in light of these needs and challenges. At the heart of this should be a modeling framework that is portable, scale-flexible, and capable of expressing the interaction of the decision-making agent with the natural environment or ecosystem. `ABSESpy` represents a significant advancement in this regard, offering several features that address the current gaps in SES modeling.

## Design structures

`ABSESpy` introduces a Branch-Leaf architecture central to its functionality, providing a systematic approach to modeling social-ecological systems (SES). This foundational framework facilitates a clear separation of the human and natural elements within SES research, aligning with the requisite to enhance replicability and scalability in modeling complex systems (**Figure 1**).

<div align="center">
	<img src="https://songshgeo-picgo-1302043007.cos.ap-beijing.myqcloud.com/uPic/structure.png" alt="Drawing" style="width: 400px;"/>
</div>

**Figure 1:** *Structure of main components of `ABSESpy` and its Branch-Leaf architecture of modules.*

### Integrative Branch-Leaf System

The Main Model anchors the system at its nucleus, holding essential parameters and global variables for SES simulations. Two primary modules emerge from this pivot: **Base Human** and **Base Nature**. The former addresses the complexities of human behaviors and social interactions, while the latter is dedicated to ecological components and processes. This bifurcated structure reflects the intertwined yet distinct facets of SES, allowing for individual module development and subsequent integration, which is pivotal for tackling the inherent complexities of SES.

### Modular Development and Replicability

Under the guiding principles of this architecture, `ABSESpy` enables the addition of specialized sub-modules, thus promoting a tailored modeling approach. The flexibility inherent in this loosely coupled design allows researchers to create, modify, and integrate diverse modules without compromising the overall system integrity. Such a configuration fosters modular development and testing and advances the model's replicability—a critical challenge in contemporary SES research.

### Actor-Oriented Model Dynamics

Central to the SES modeling in `ABSESpy` is conceptualizing entities as "`Actors`," managed within an **Actors Container**. This specialized container simplifies the organization and operation of the entities, ensuring that each actor's unique attributes and the global model information are coherently synthesized. This design element responds directly to the need for models that balance capturing individual decision-making processes and the broader system dynamics.

In conclusion, the structural organization of `ABSESpy` addresses several of the critical challenges in SES research by providing a modular, replicable, and scalable framework that facilitates a nuanced examination of complex socio-ecological interactions. Through its architectural clarity, `ABSESpy` ensures that the intricate relationships and processes inherent in SES are adequately represented, analyzed, and understood.

## Human-behavior modeling framework

ABSESpy recognizes the centrality of human agents in SES and, as such, prioritizes the realistic simulation of their behavior. To this end, the framework provides an integrative approach that allows users to (**Figure 2**):

1. **Define Interactions**: Agents within the system actively interact with both natural and social systems. `ABSESpy` facilitates the specification of these interactions, enabling agents to engage with their environment in a contextually relevant manner.
2. **Define Perceptions**: From direct environmental observations to complex communications with other agents, the `ABSESpy` framework allows users to define a `perception` variable for a nuanced representation of how agents gather information and form their understanding of the environment.
3. **Define Decision-making processes**: At the core of ABSESpy's human behavior simulation is the ability of agents to evaluate choices and make decisions. Users can implement decision-making logic, capturing how human agents might process information and select courses of action.
4. **Response Mechanisms**: Consequent to decision-making, agents must exhibit appropriate responses. ABSESpy's framework delineates mechanisms through which agents can actualize their decisions —e.g., spatial relocation, attribute changes, altering environment, or other forms of interaction.

<div align="center">
	<img src="https://songshgeo-picgo-1302043007.cos.ap-beijing.myqcloud.com/uPic/MoHuB.png" alt="Drawing" style="width: 400px;"/>
</div>

**Figure 2:** *Decision-making workflow for simulating human behavior.*

In sum, `ABSESpy` provides an advanced behavior simulation framework, a testament to the synthesis of theoretical and practical approaches in human behavior modeling. By translating theoretical constructs into user-friendly, operational components, `ABSESpy` empowers researchers to bridge the gap between conceptual models and their tangible application in SES. This aligns to achieve fidelity in representing human behavior and enhances the capability for replicable and verifiable modeling in large-scale SES research endeavors.

## Real-world SES modeling enhancements

<div align="center">
	<img src="https://songshgeo-picgo-1302043007.cos.ap-beijing.myqcloud.com/uPic/schedule.png" alt="Drawing" style="width: 400px;"/>
</div>

**Figure 3:** *Calendar time module enhances real-world social-ecological system modeling approaches.*

`ABSESpy` integrates an innovative time control mechanism to bridge the gap between agent-based modeling and the multifaceted nature of real-world events. These are attributions from a `TimeDriver` module that manages the association of ABM with real-world time (**Figure 3**). For example, we can implement three functions here: Advanced Time Management, Integration of Dynamical Data-based Variables, and Event-Driven Simulations.

### Advanced Time Management

In addition to the standard tick-based time advancement, `ABSESpy` introduces two additional temporal modes to match the diverse scales of SES phenomena better.

- In a **Duration Mode**, users can define the length of time that each simulation step represents, thus allowing for variable temporal resolutions. This capability enables the model to represent time intervals that can vary from minutes to years, depending on the specific requirements of the SES being modeled.
- On the other hand, the **Irregular Mode** addresses the non-uniformity of specific SES processes; this mode allows for irregular time steps, whereby different simulation intervals can represent varying lengths of time. This flexibility is crucial when modeling events that do not follow a linear timeline, such as erratic ecological phenomena or sporadic human activities.

### Integration of Dynamical Data-based Variables

A core component of SES modeling is utilizing dynamic, temporal data. ABSESpy's approach to data integration involves:

- **Dynamic Variable Updates**: The framework automates the updating of variables with time-series data, negating the need for manual data refreshes and recalculations. It supports real-time data feeds, ensuring that the model reflects current conditions.
- **Spatial Data Handling**: SES models frequently rely on geographically and temporally specific data. ABSESpy facilitates the integration of spatial data sets, providing tools for handling and querying raster data in conjunction with temporal variables.

### Event-Driven Simulations

Finally, the `time_condition` decorator in ABSESpy introduces a nuanced layer of time-based event handling. By leveraging this decorator, modelers can set temporal conditions for executing events, enabling simulations to react to time-specific triggers. This aspect is especially pertinent for phenomena with distinct temporal patterns, like migratory behaviors or seasonal cycles.

## Conclusions

In summary, `ABSESpy` Facilitates independent module creation, enabling detailed analysis and integration of complex SES components. Applying an advanced human behavior framework, `ABSESpy` clarifies agent definition and tracking, offering solutions for SES's human decision-making complexities. By providing sophisticated time control and data integration tools, `ABSESpy` enables a more accurate and nuanced representation of SES dynamics, meeting the intricate requirements of real-world problem-solving and decision-making support. By integrating these capabilities, ABSESpy explicitly addresses the previously identified gaps in SES modeling, paving the way for more accurate, reliable, and applicable SES research outcomes.

## Acknowledgment

This research has been supported by the National Natural Science Foundation of China (grant no. 42041007) and the National Natural Science Foundation of China Joint Fund for Scientific Research on Yellow River (grant no. U2243601).

## References
