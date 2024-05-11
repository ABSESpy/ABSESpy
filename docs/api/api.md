---
title: API Reference Guide Map
authors: SongshGeo
date: 2024-03-10
---

Following diagram shows the basic structure of the `ABSESpy`'s API.

![abses_API](https://songshgeo-picgo-1302043007.cos.ap-beijing.myqcloud.com/uPic/abses_API.png)

You may wanna check out:

## Implementation

Have a basic idea on how to implement your own model based on `ABSESpy`.

- 🌍 Generally, the default [`BaseNature`](../api/nature.md) is enough in most cases, but you may want to create a layer ([`PatchModule`](../api/layer.md)) as a world where actors live.
- 🗺️ Wait, if you want more flexibility to operate the grid cells, it's a good idea to customize [`PatchCell`](../api/cells.md).
- 🤖 Now, introducing your custom agents (actors in social-ecological system context) by custom a subclass of [`Actor`](../api/agents.md).
- (🥷 *Advanced skill*) Considering what decisions your agents need to make, apply our advanced decision-making framework. You may need to check the docs of [`Decision`](../api/decisions.md).
- 🧪 Finally, using [`Experiment`](../api/experiment.md) for batch runs and testing different parameters.

## Operation

Useful operations snippets and API for better implementation.

- 📁 Learn to create, manage, and operate your agents by referring [`AgentsContainer`](../api/container.md) and [`ActorsList`](../api/sequences.md).
- 🕙 Relate your model to real time by [`TimeDriver`](../api/time.md).
- 🚶 Actors can be easily moved by referring [`Movements`](../api/move.md)
- 🔗 You may also want to implement interlinks between the actors by referring [`Links`](../api/links.md).
- 🎲 Randomize your agents' performance in batch by checkout [`ListRandom`](../api/random.md) or use [`Mesa`'s API](https://mesa.readthedocs.io/en/stable/best-practices.html#randomization) to do random for a specific Actor.
