
import sys
sys.path.append('/home/bharath/co.r/code/ext.ws/src/ACTION_GRAPH')

from action_graph.action import Action
from action_graph.agent import Agent


class Haunt(Action):
    effects = {"is_spooky": True}
    preconditions = {"is_undead": True}


class BecomeUndead(Action):
    effects = {"is_undead": True}
    preconditions = {"is_undead": False}


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
