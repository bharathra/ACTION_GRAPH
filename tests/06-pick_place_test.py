#! /usr/bin/env python3

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if True:
    from action_graph.agent import Agent, Action, ActionStatus, State


class Move(Action):
    effects = {"robot_location": ...}
    preconditions = {"robot_ready": True}


class Pick(Action):
    effects = {"object_location": "gripper"}
    preconditions = {"robot_location": "@object_location"}


class Place(Action):
    effects = {"object_location": ...}
    preconditions = {"object_location": "gripper", "robot_location": "$object_location"}


def test():
    world_state = {"robot_ready": True, "object_location": "P1"}
    goal_state = {"object_location": "P2"}

    ai = Agent()
    actions = [a(ai) for a in Action.__subclasses__()]
    ai.load_actions(actions)
    ai.state = world_state
    plan = ai.get_plan(goal_state)

    expected_actions = ['Move', 'Pick', 'Move', 'Place']
    expected_outcome = [{'robot_location': 'P1'}, {'object_location': 'gripper'},
                        {'robot_location': 'P2'}, {'object_location': 'P2'}]

    for ax, eax, eoc in zip(plan, expected_actions, expected_outcome):
        assert ax.__class__.__name__ == eax, f'Incorrect Action!'
        assert ax.effects == eoc, f'Incorrect Action Outcome!'
