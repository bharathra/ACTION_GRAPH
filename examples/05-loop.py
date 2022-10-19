#! /usr/bin/env python3

from action_graph.action import Action, State, ActionStatus
from action_graph.agent import Agent


class FibonacciIncrement(Action):
    effects = {"value": ...}

    def apply_effects(self, outcome: State, state: State):
        next_num = state["last_num"] + 1
        state["value"] = state["value"] + next_num
        state["last_num"] = next_num


if __name__ == "__main__":
    world_state = {"value": 0, "last_num": 0}
    goal_state = {"last_num": 10}

    ai = Agent()

    actions = [a(ai) for a in Action.__subclasses__()]
    ai.load_actions(actions)

    print("Initial State:", world_state)
    ai.update_state(world_state)

    print("Goal State:   ", goal_state)
    #
    # # option 1
    # ai.achieve_goal(goal_state, verbose=True)
    #
    # # option 3
    for plan in ai.achieve_goal_interactive(goal_state):
        ai.print_plan_to_console(plan)
