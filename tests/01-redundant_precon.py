#! /usr/bin/env python3

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

    actions = [a(ai) for a in Action.__subclasses__()]
    ai.load_actions(actions)

    print("Initial State:", world_state)
    ai.update_state(world_state)

    print("Goal State:   ", goal_state)
    plan = ai.get_plan(goal_state)

    expected_actions = ["Action1", "Action2", "Action3", "Action4"]
    expected_outcome = [{'FIRST': True}, {'SECOND': True}, {'THIRD': True}, {'FOURTH': True}]

    for ax, eax, eoc in zip(plan, expected_actions, expected_outcome):
        assert ax.__class__.__name__ == eax, f'Incorrect Action!'
        assert ax.effects == eoc, f'Incorrect Action Outcome!'
