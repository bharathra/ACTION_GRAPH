#! /usr/bin/env python3

import sys
sys.path.append('/home/bharath/co.r/code/ext.ws/src/ACTION_GRAPH')

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


if __name__ == "__main__":
    world_state = {"FIRST": False, "SECOND": False, "THIRD": False, "FOURTH": False}
    goal_state = {"FOURTH": True}

    ai = Agent()

    actions = [a(ai) for a in Action.__subclasses__()]
    ai.load_actions(actions)

    print("Initial State:", world_state)
    ai.update_state(world_state)

    print("Goal State:   ", goal_state)
    ai.achieve_goal(goal_state)
