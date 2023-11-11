
In Socio-Ecological Systems (SES) modeling, a real-world event's natural or human-induced duration can range from seconds to centuries. Recognizing the importance of time in modeling real-world problems, ABSESpy introduces a superior time control mechanism that stands out from traditional agent-based modeling frameworks.

<div align="center">
	<img src="https://songshgeo-picgo-1302043007.cos.ap-beijing.myqcloud.com/uPic/schedule.png" alt="Drawing" style="width: 400px;"/>
</div>

## Real-time Mode: Simulating the Actual Progression of Time

Unlike traditional frameworks that rely solely on a simple time counter (often called 'tick'), `ABSESpy` brings forth the **Real-time Mode** as an extension of the conventional timing system of agent-based modeling frameworks. Through this feature, here are three modes that set `ABSESpy` apart:

- **['tick' mode] Tick-tick Time Intervals**: the same as traditional agent-based modeling framework and, by default, `ABSESpy` records each simulating step as an increment of counting ticker.
- **['duration' mode] Customizable Time Intervals**: Users can define any desired time interval for each simulation step. This interval can represent a minute, an hour, a day, or any other real-world period, allowing for a more authentic representation of SES dynamics.
- **['irregular' mode] Variable Time Steps Per Tick**: This mode empowers users to assign different time durations for each tick, granting unmatched flexibility. Whether a particular phase in your model needs to represent a day, and another a month, free-time mode has got you covered.

## Auto-update Dynamic Variables

Of the most important reasons to use real-world data and time is dynamically loading and updating time-series datasets. Talk is cheap, please see [this time control tutorial](../../tutorial/lessons/time_control).

Dynamic data may be beneficial because modeling the real-world SES problem often requires various datasets as inputs. You won't want to re-calculate the data in each step... So! Just define them as dynamic variables when initializing or setting up a module by uploading a `withdraw data function` and a `data source`. It should also be applied to spatial datasets! Like selecting a raster data through some withdrawing function like `xarray.DataArray.sel(time=...)`.

## Decorator for Conditional Time-based Triggering

To elevate the precision and applicability of time controls, `ABSESpy` introduces a dedicated decorator [`time_condition`](../api/time.md#time_condition). This decorator can adorn any model component with custom methods. Even more impressive is that these methods only activate when specific time conditions are met. This ensures that certain actions or events only occur at the right moments in your simulation, mirroring real-world occurrences with higher fidelity.

> [!INFO]In Progress
> This document is a work in progress if you see any errors, or exclusions or have any problems, please [get in touch with us](https://github.com/absespy/ABSESpy/issues).
