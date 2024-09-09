#! /usr/bin/env python3

from action_graph.action import Action
from action_graph.agent import Agent


class ActionA(Action):
    effects = {"FIRST": True}
    preconditions = {}


class ActionB1(Action):
    effects = {"B": True}
    preconditions = {"A": True}


class ActionB2(Action):
    effects = {"B": True}
    preconditions = {}
    cost = 1.5


class ActionC(Action):
    effects = {"C": True}
    preconditions = {"A": True, "B": True}


def test():
    world_state = {"A": False, "B": False, "C": False}
    goal_state = {"C": True}

    ai = Agent()

    actions = [a(ai) for a in Action.__subclasses__()]
    ai.load_actions(actions)
    ai.state = world_state
    plan = ai.get_plan(goal_state)

    expected_actions = ["ActionA", "ActionB2", "ActionC"]
    expected_outcome = [{'A': True}, {'B': True}, {'C': True}]

    for ax, eax, eoc in zip(plan, expected_actions, expected_outcome):
        assert ax.__class__.__name__ == eax, f'Incorrect Action!'
        assert ax.effects == eoc, f'Incorrect Action Outcome!'
