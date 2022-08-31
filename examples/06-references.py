#! /usr/bin/env python3

import sys
sys.path.append('/home/bharath/co.r/code/ext.ws/src/ACTION_GRAPH')

from action_graph.action import Action, State
from action_graph.agent import Agent


class Haunt(Action):
    effects = {"SPKY": True}
    preconditions = {"UNDD": True, "PRFMGK": "abracadabra"}

    def on_execute(self, desired_state: State):
        print('Haunting...')
        return super().on_execute(desired_state)


class BecomeUndead(Action):
    effects = {"UNDD": True}
    preconditions = {"UNDD": False, "PRFMGK": "abracadabra"}

    def on_execute(self, desired_state: State):
        print('Becoming Undead...')
        return super().on_execute(desired_state)


class BecomeUndead2(Action):
    effects = {"UNDD": True}
    preconditions = {"UNDD": False, "PRFMGK": "abracadabra"}
    cost = 1.1

    def on_execute(self, desired_state: State):
        print('Becoming Undead2...')
        return super().on_execute(desired_state)


class PerformMagic(Action):
    effects = {"PRFMGK": ...}
    preconditions = {
        "CHNTINC": "$PRFMGK",
        "CSTSPL": "$PRFMGK",
    }

    def on_execute(self, desired_state: State):
        print('Performing Magic...')
        return super().on_execute(desired_state)


class ChantIncantation(Action):
    effects = {"CHNTINC": ...}
    preconditions = {}

    def on_execute(self, desired_state: State):
        print('Chanting Incantation...')
        return super().on_execute(desired_state)


class CastSpell(Action):
    effects = {"CSTSPL": ...}
    preconditions = {}

    def on_execute(self, desired_state: State):
        print('Casting Spell...')
        return super().on_execute(desired_state)


if __name__ == "__main__":
    world_state = {"SPKY": False, "UNDD": False, "TEST": True}
    goal_state = {"SPKY": True}

    ai = Agent()

    actions = [a(ai) for a in Action.__subclasses__()]
    ai.load_actions(actions)

    print("Initial State:", world_state)
    ai.update_state(world_state)

    print("Goal State:   ", goal_state)
    ai.achieve_goal(goal_state)
