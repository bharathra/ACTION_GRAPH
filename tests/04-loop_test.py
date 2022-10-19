#! /usr/bin/env python3

from action_graph.action import Action, State, ActionStatus
from action_graph.agent import Agent


class FibonacciIncrement(Action):
    effects = {"last_num": ...}

    def apply_effects(self, outcome: State, state: State):
        next_num = state["last_num"] + 1
        state["value"] = state["value"] + next_num
        state["last_num"] = next_num


def test():
    world_state = {"value": 0, "last_num": 0}
    goal_state = {"last_num": 10}

    ai = Agent()
    actions = [a(ai) for a in Action.__subclasses__()]
    ai.load_actions(actions)
    ai.update_state(world_state)
    for plan in ai.achieve_goal_interactive(goal_state):
        pass

    assert ai.state["value"] == 55, f'Looping feature broken!'
