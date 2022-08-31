"""
Sometimes we want to define an action that provides a _service_ rather than
satisfies one particular state value. We can do this by providing ellipsis as the
effect.

When the procedural precondition is called, the action will be given the resolved
services dictionary, where it can succeed or fail on the values.

In this example, the `ChantIncantation` action will chant _anything_ it is asked to.
Here, the `Haunt` action is requesting `chant_incantation` service.
"""

import sys
sys.path.append('/home/bharath/co.r/code/ext.ws/src/ACTION_GRAPH')

from action_graph.action import Action
from action_graph.agent import Agent


class Haunt(Action):
    effects = {"is_spooky": True}
    preconditions = {"is_undead": True, "chant_incantation": "WOOO I'm a ghost"}


class BecomeUndead(Action):
    effects = {"is_undead": True}
    preconditions = {"is_undead": False}


class ChantIncantation(Action):
    effects = {"chant_incantation": ...}
    preconditions = {}


if __name__ == "__main__":
    world_state = {"is_spooky": False, "is_undead": False}
    goal_state = {"is_spooky": True}

    ai = Agent()

    actions = [a(ai) for a in Action.__subclasses__()]
    ai.load_actions(actions)

    print("Initial State:", world_state)
    ai.update_state(world_state)

    print("Goal State:   ", goal_state)
    ai.achieve_goal(goal_state)
