#! /usr/bin/env python3

import sys
sys.path.append('/home/bharath/co.r/code/ext.ws/src/ACTION_GRAPH')

from action_graph.action import Action
from action_graph.agent import Agent


class Haunt(Action):
    effects = {"is_spooky": True}
    preconditions = {"is_undead": True, "performs_magic": "abracadabra"}


class BecomeUndead(Action):
    effects = {"is_undead": True}
    preconditions = {"is_undead": False}


class PerformMagic(Action):
    effects = {"performs_magic": ...}
    preconditions = {
        "chant_incantation": "$performs_magic",
        "cast_spell": "$performs_magic",
    }


class ChantIncantation(Action):
    effects = {"chant_incantation": ...}
    preconditions = {}


class CastSpell(Action):
    effects = {"cast_spell": ...}
    preconditions = {}


if __name__ == "__main__":
    world_state = {"is_spooky": False, "is_undead": False}
    goal_state = {"is_spooky": True}

    ai = Agent()

    actions = [a(ai) for a in Action.__subclasses__()]
    ai.load_actions(actions)

    print("Initial State:", world_state)
    ai.update_state(world_state)

    print("Goal State:   ", goal_state)
    ai.achieve_goal(goal_state)
