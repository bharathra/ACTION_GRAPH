#! /usr/bin/env python3

import sys
sys.path.append('/home/bharath/co.r/code/ext.ws/src/ACTION_GRAPH')

import pytest
from action_graph.action import Action, State
from action_graph.agent import Agent


class Action1(Action):
    effects = {"FIRST": True}
    preconditions = {}


class Action2A(Action):
    effects = {"SECOND": True}
    preconditions = {"FIRST": True}


class Action2B(Action):
    effects = {"SECOND": True}
    preconditions = {}
    cost = 1.5


class Action3(Action):
    effects = {"THIRD": True}
    preconditions = {"FIRST": True, "SECOND": True}


def test():
    world_state = {"FIRST": False, "SECOND": False, "THIRD": False}
    goal_state = {"THIRD": True}

    ai = Agent()

    actions = [a(ai) for a in Action.__subclasses__()]
    ai.load_actions(actions)

    print("Initial State:", world_state)
    ai.update_state(world_state)

    print("Goal State:   ", goal_state)
    plan = ai.get_plan(goal_state)

    expected_actions = ["Action1", "Action2B", "Action3"]
    expected_outcome = [{'FIRST': True}, {'SECOND': True}, {'THIRD': True}]

    for ax, eax, eoc in zip(plan, expected_actions, expected_outcome):
        assert ax.__class__.__name__ == eax, f'Incorrect Action!'
        assert ax.effects == eoc, f'Incorrect Action Outcome!'

