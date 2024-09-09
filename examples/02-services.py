#! /usr/bin/env python3

import os
import sys
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if True:
    from action_graph.agent import Agent, Action, ActionStatus, State


class Drive(Action):
    effects = {"driving": ...}
    preconditions = {"has_drivers_license": True, "has_car": "$driving", "tank_has_gas": True}

    def execute(self):
        print("Driving car>>>", self.effects["driving"])
        return super().execute()


class ApplyForDriversLicense(Action):
    effects: State = {"has_drivers_license": True}
    # simulate async action
    async_exec: bool = True

    def execute(self):
        time.sleep(1)
        print("Drivers ed completed; Have license>>>", self.effects["has_drivers_license"])
        return super().execute()


class FillGas(Action):
    effects = {"tank_has_gas": True}
    # preconditions = {"has_car": "@has_car"}  # has the car that was requested

    def execute(self):
        print(f"Filling gas into>>>{self.agent.state['has_car']}")
        return super().execute()


class RentCar(Action):
    effects = {"has_car": ...}
    preconditions = {"rental_available": "$has_car"}

    def execute(self):
        print("Renting car>>>", self.agent.state["has_car"])
        return super().execute()

    def on_exit(self):
        print("Rented car>>>", self.agent.state["has_car"])
        return super().on_exit()


class BuyCar(Action):
    effects = {"has_car": ...}
    preconditions = {}
    cost = 40_000

    def execute(self):
        print(f"Buying car>>>{self.effects['has_car']}")
        return super().execute()

    def on_exit(self):
        print("Bought car>>>", self.agent.state["has_car"])
        return super().on_exit()


if __name__ == "__main__":
    world_state = {"has_drivers_license": False}
    goal_state = {"driving": "Delorean"}

    ai = Agent()

    actions = [a(ai) for a in Action.__subclasses__()]
    ai.load_actions(actions)

    print("Initial State:", world_state)
    ai.state = world_state

    print("Goal State:   ", goal_state)
    #
    # plan = ai.get_plan(goal_state)
    # ai.print_plan_to_console(plan)
    for plan in ai.plan_and_execute(goal_state):
        ai.print_plan_to_console(plan)
