#! /usr/bin/env python3

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from action_graph.action import Action, State, ActionStatus
from action_graph.agent import Agent


class FibonacciIncrement(Action):
    effects = {"counter": ...}

    def apply_effects(self, outcome: State, state: State):
        # store the sum in the state
        state["fibonacci_sum"] = state["fibonacci_sum"] + state["counter"] + 1
        # now apply effects
        # dont apply the final effect(base class implementation);
        # instead increment by 1
        state["counter"] = state["counter"] + 1


if __name__ == "__main__":
    world_state = {"fibonacci_sum": 0, "counter": 0}
    goal_state = {"counter": 10}

    ai = Agent()

    actions = [a(ai) for a in Action.__subclasses__()]
    ai.load_actions(actions)

    print("Initial State:", world_state)
    ai.update_state(world_state)

    print("Goal State:   ", goal_state)
    #
    # # option 2
    for plan in ai.plan_and_execute(goal_state, verbose=True):
        pass  # input()

    print(ai.state['fibonacci_sum'])
