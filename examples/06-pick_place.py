#! /usr/bin/env python3

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from action_graph.action import Action
from action_graph.agent import Agent


class Move(Action):
    effects = {"robot_location": ...}
    preconditions = {"robot_ready": True}


class Pick(Action):
    effects = {"object_location": "gripper"}
    preconditions = {"robot_location": "@object_location"}


class Place(Action):
    effects = {"object_location": ...}
    preconditions = {"object_location": "gripper", "robot_location": "$object_location"}


if __name__ == "__main__":
    world_state = {"robot_ready": True, "object_location": "P1"}
    goal_state = {"object_location": "P2"}
    # goal_state = {"object1": "nudged"}

    ai = Agent()

    actions = [a(ai) for a in Action.__subclasses__()]
    ai.load_actions(actions)

    print("Initial State:", world_state)
    ai.update_state(world_state)

    print("Goal State:   ", goal_state)
    # plan = ai.get_plan(goal_state)
    # ai.print_plan_to_console(plan)

    for plan in ai.plan_and_execute(goal_state):
        ai.print_plan_to_console(plan)

    ai.execute_plan(plan)
