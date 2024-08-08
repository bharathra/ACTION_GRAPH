#! /usr/bin/env python3

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from action_graph.action import Action, ActionStatus, State
from action_graph.agent import Agent


class GoBackToTheFuture(Action):
    effects = {"year": "1985"}
    preconditions = {"year": "1955", "has_time_machine": True, "critical_speed": "88mph"}

    def execute(self):
        print('Going Back to the future...')
        return super().execute()

    def on_exit(self):
        print('>>>Arrived in the year:', self.agent.state["year"])
        return super().on_exit()


class MakeTimeMachine(Action):
    effects = {"has_time_machine": True}
    preconditions = {"has_car": "Delorean"}

    def execute(self):
        print('Making Time Machine...')
        return super().execute()


class DoNuclearFission(Action):
    effects = {"has_power": ...}
    preconditions: State = {"have_fuel": "plutonium"}
    cost: float = 10000

    def execute(self):
        print('Nuclear fission FAILED!!!...')
        self.status = ActionStatus.FAILURE


class WaitForThunderStorm(Action):
    effects = {"has_power": ...}
    preconditions: State = {"predict_lightening_strike": True}
    cost: float = 1000000

    def execute(self):
        print('Waiting for thunderstorm...')
        self.status = ActionStatus.SUCCESS  # Ensure the action status is set

    def on_success(self):
        print(f">>>{self.effects['has_power']} available...")
        return super().on_success()


class AccelerateToCriticalSpeed(Action):
    effects: State = {"critical_speed": ...}
    preconditions: State = {"has_power": "@required_power"}

    def execute(self):
        print(f"Accelerating {self.agent.state['has_car']} to {self.effects['critical_speed']}...")
        self.status = ActionStatus.SUCCESS  # Ensure the action status is set


class GetCar(Action):
    effects: State = {"has_car": ...}
    preconditions: State = {"year": "1955", "car_at_doc_browns_lab": "$has_car"}

    def execute(self):
        print(f"Getting Car: {['has_car']} ...")
        return super().execute()


if __name__ == "__main__":
    world_state = {"year": "1955",
                   "car_at_doc_browns_lab": "Delorean",
                   "predict_lightening_strike": True,
                   "have_fuel": "plutonium",
                   "required_power": "1.21_gigawatts"}

    goal_state = {"year": "1985"}

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
