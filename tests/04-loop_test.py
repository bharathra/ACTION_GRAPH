#! /usr/bin/env python3

from action_graph.action import Action, State, ActionStatus
from action_graph.agent import Agent


class FibonacciIncrement(Action):
    effects = {"counter": ...}

    def apply_effects(self, state: State):
        # store the sum in the state
        state["fibonacci_sum"] = state["fibonacci_sum"] + state["counter"] + 1
        # now apply effects
        # dont apply the final effect(base class implementation);
        # instead increment by 1
        state["counter"] = state["counter"] + 1


def test():
    world_state = {"fibonacci_sum": 0, "counter": 0}
    goal_state = {"counter": 10}

    ai = Agent()
    actions = [a(ai) for a in Action.__subclasses__()]
    ai.load_actions(actions)
    ai.state = world_state
    for plan in ai.plan_and_execute(goal_state):
        pass

    assert ai.state["fibonacci_sum"] == 55, f'Looping feature broken!'
