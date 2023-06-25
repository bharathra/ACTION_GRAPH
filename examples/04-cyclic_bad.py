#! /usr/bin/env python3

from action_graph.action import Action
from action_graph.agent import Agent


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
    ai.update_state(world_state)

    print("Goal State:   ", goal_state)
    plan = ai.get_plan(goal_state)
    #
    # # option 1
    plan = ai.get_plan(goal_state)
    ai.execute_plan(plan)
    #
    # # option 2
    for plan in ai.plan_and_execute(goal_state, verbose=True):
        pass  # input()
