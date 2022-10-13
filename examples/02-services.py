#! /usr/bin/env python3

import time

from action_graph.agent import Agent
from action_graph.action import Action, State


class Drive(Action):
    effects = {"driving": ...}
    preconditions = {"has_drivers_license": True, "has_car": "$driving", "tank_has_gas": True}

    def on_execute(self, outcome: State):
        print("Driving car>>>", outcome["driving"])
        return super().on_execute(outcome)


class ApplyForDriversLicense(Action):
    effects: State = {"has_drivers_license": True}
    # simulate async action
    allow_async: bool = True

    def on_execute(self, outcome: State):
        time.sleep(1)
        print("Drivers ed completed; Have license>>>", outcome["has_drivers_license"])
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
        print("Renting car>>>", self.agent.state["has_car"])
        return super().on_execute(outcome)

    def on_exit(self, expected_outcome: State = None):
        print("Rented car>>>", self.agent.state["has_car"])
        return super().on_exit(expected_outcome)


class BuyCar(Action):
    effects = {"has_car": ...}
    preconditions = {}
    cost = 40_000

    def on_execute(self, outcome: State):
        print(f"Buying car>>>{outcome['has_car']}")
        return super().on_execute(outcome)

    def on_exit(self, expected_outcome: State = None):
        print("Bought car>>>", self.agent.state["has_car"])
        return super().on_exit(expected_outcome)


if __name__ == "__main__":
    world_state = {"has_drivers_license": False}
    goal_state = {"driving": "Delorean"}

    ai = Agent()

    actions = [a(ai) for a in Action.__subclasses__()]
    ai.load_actions(actions)

    print("Initial State:", world_state)
    ai.update_state(world_state)

    print("Goal State:   ", goal_state)
    #
    # # option 1
    # plan = ai.get_plan(goal_state)
    # ai.execute_plan(plan)
    #
    # # option 2
    # ai.achieve_goal(goal_state, verbose=True)
    #
    # # option 3
    for plan in ai.achieve_goal_interactive(goal_state):
        ai.print_plan_to_console(plan)
