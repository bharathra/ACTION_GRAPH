#! /usr/bin/env python3

from action_graph.action import Action
from action_graph.agent import Agent


class ActionA(Action):
    effects = {"FIRST": True}
    preconditions = {}


class ActionB1(Action):
    effects = {"SECOND": True}
    preconditions = {"FIRST": True}


class ActionB2(Action):
    effects = {"SECOND": True}
    preconditions = {}
    cost = 1.5


class ActionC(Action):
    effects = {"THIRD": True}
    preconditions = {"FIRST": True, "SECOND": True}


def test():
    world_state = {"FIRST": False, "SECOND": False, "THIRD": False}
    goal_state = {"THIRD": True}

    ai = Agent()

    actions = [a(ai) for a in Action.__subclasses__()]
    ai.load_actions(actions)
    ai.update_state(world_state)
    plan = ai.get_plan(goal_state)

    expected_actions = ["ActionA", "ActionB2", "ActionC"]
    expected_outcome = [{'FIRST': True}, {'SECOND': True}, {'THIRD': True}]

    for ax, eax, eoc in zip(plan, expected_actions, expected_outcome):
        assert ax.__class__.__name__ == eax, f'Incorrect Action!'
        assert ax.effects == eoc, f'Incorrect Action Outcome!'
