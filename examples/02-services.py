#! /usr/bin/env python3

import sys
sys.path.append('/home/bharath/co.r/code/ext.ws/src/ACTION_GRAPH')

from action_graph.agent import Agent
from action_graph.action import Action, State


class Drive(Action):
    effects = {"driving": ...}
    preconditions = {"has_drivers_license": True, "has_car": "$driving", "tank_has_gas": True}

    def on_execute(self, outcome: State):
        print("Driving car>>>", outcome["driving"])
        return super().on_execute(outcome)


class FillGas(Action):
    effects = {"tank_has_gas": True}
    preconditions = {"has_car": "$has_car"}  # has the car that was requested

    def on_execute(self, outcome: State):
        print(f"Filling gas into>>>{self.agent.state['has_car']}")
        return super().on_execute(outcome)


class RentCar(Action):
    effects = {"has_car": ...}
    preconditions = {"rental_available": "$has_car"}

    def on_execute(self, outcome: State):
        return super().on_execute(outcome)

    def on_exit(self, expected_outcome: State = None):
        print("Renting car>>>", self.agent.state["has_car"])
        return super().on_exit(expected_outcome)


class BuyCar(Action):
    effects = {"has_car": ...}
    preconditions = {}
    cost = 40_000

    def on_execute(self, outcome: State):
        print(f"Buying car>>>{outcome['has_car']}")
        return super().on_execute(outcome)

    def on_exit(self, expected_outcome: State = None):
        print("Buying car>>>", self.agent.state["has_car"])
        return super().on_exit(expected_outcome)


if __name__ == "__main__":
    world_state = {"has_drivers_license": True}
    goal_state = {"driving": "Delorean"}

    ai = Agent()

    actions = [a(ai) for a in Action.__subclasses__()]
    ai.load_actions(actions)

    print("Initial State:", world_state)
    ai.update_state(world_state)

    print("Goal State:   ", goal_state)
    plan = ai.get_plan(goal_state)

    ai.execute_plan(plan)
