#! /usr/bin/env python3

import sys
sys.path.append('/home/bharath/co.r/code/ext.ws/src/ACTION_GRAPH')

import pytest
from action_graph.action import Action
from action_graph.agent import Agent


class Action5(Action):
    effects = {"FINAL": True}
    preconditions = {"FIRST": True, "FOURTH": "TESTSTATE"}


class Action1(Action):
    effects = {"FIRST": True}
    preconditions = {"FIRST": False}


class Action4(Action):
    effects = {"FOURTH": ...}
    preconditions = {
        "SECOND": "$FOURTH",
        "THIRD": "$FOURTH",
    }


class Action2(Action):
    effects = {"SECOND": ...}
    preconditions = {}


class Action3(Action):
    effects = {"THIRD": ...}
    preconditions = {}


def test():
    world_state = {"FINAL": False, "FIRST": False}
    goal_state = {"FINAL": True}

    ai = Agent()

    actions = [a(ai) for a in Action.__subclasses__()]
    ai.load_actions(actions)

    print("Initial State:", world_state)
    ai.update_state(world_state)

    print("Goal State:   ", goal_state)
    plan = ai.get_plan(goal_state)
    
    expected_actions = ["Action1", "Action2", "Action3", "Action4", "Action5"]
    expected_outcome = [{'FIRST': True}, {'SECOND': 'TESTSTATE'}, {'THIRD': 'TESTSTATE'}, {'FOURTH': 'TESTSTATE'}, {'FINAL': True}]

    for ax, eax, eoc in zip(plan, expected_actions, expected_outcome):
        assert ax.__class__.__name__ == eax, f'Incorrect Action!'
        assert ax.effects == eoc, f'Incorrect Action Outcome!'
