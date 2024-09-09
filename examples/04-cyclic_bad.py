#! /usr/bin/env python3

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if True:
    from action_graph.agent import Agent, Action, ActionStatus, State


class Action1(Action):
    effects = {"FIRST": True}
    preconditions = {"SECOND": True}  # <- cyclic reference !!!


class Action2(Action):
    effects = {"SECOND": True}
    preconditions = {"FIRST": True}  # <- cyclic reference !!!


class Action3(Action):
    effects = {"THIRD": True}
    preconditions = {"FIRST": True, "SECOND": True}


if __name__ == "__main__":
    world_state = {"FIRST": False, "SECOND": False, "THIRD": False}
    goal_state = {"THIRD": True}

    ai = Agent()

    actions = [a(ai) for a in Action.__subclasses__()]
    ai.load_actions(actions)

    print("Initial State:", world_state)
    ai.state = world_state

    print("Goal State:   ", goal_state)
    plan = ai.get_plan(goal_state)
    #
    # plan = ai.get_plan(goal_state)
    # ai.print_plan_to_console(plan)
    for plan in ai.plan_and_execute(goal_state):
        ai.print_plan_to_console(plan)
