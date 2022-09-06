# ACTION_GRAPH
AI agent for generating action plans based on preconditions and effects. Similar to GOAP in function, but this entirely different implementation.

The interfaces for this library are similar to https://github.com/agoose77/GOAP. The GOAP implementation has been replaced with a simple recursive Depth First Search for generating action plans.


## Usage:

```
from action_graph.action import Action
from action_graph.agent import Agent


class Action1(Action):
    effects = {"FIRST": True}
    preconditions = {}


class Action2(Action):
    effects = {"SECOND": True}
    preconditions = {"FIRST": True}


class Action3(Action):
    effects = {"THIRD": True}
    preconditions = {"FIRST": True, "SECOND": True}


class Action4(Action):
    effects = {"FOURTH": True}
    preconditions = {"FIRST": True, "THIRD": True}


def test():
    world_state = {} # unknown
    goal_state = {"FOURTH": True}

    ai = Agent()

    actions = [Action1, Action2, Action3, Action4]
    ai.load_actions(actions)

    print("Initial State:", world_state)
    ai.update_state(world_state)

    print("Goal State:   ", goal_state)
    plan = ai.get_plan(goal_state)
```


