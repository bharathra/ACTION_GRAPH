#! /usr/bin/env python3

from action_graph.action import Action, ActionStatus, State
from action_graph.agent import Agent


class GoBackToTheFuture(Action):
    effects = {"year": "1985"}
    preconditions = {"year": "1955", "has_time_machine": True, "critical_speed": "88mph"}

    def on_execute(self, desired_state: State):
        print('Going Back to the future...')
        return super().on_execute(desired_state)

    def on_exit(self, outcome: State = None):
        print('>>>Arrived in the year:', self.agent.state["year"])
        return super().on_exit(outcome)


class MakeTimeMachine(Action):
    effects = {"has_time_machine": True}
    preconditions = {"has_car": "Delorean"}

    def on_execute(self, desired_state: State):
        print('Making Time Machine...')
        return super().on_execute(desired_state)


class DoNuclearFission(Action):
    effects = {"has_power": ...}
    preconditions: State = {"have_fuel": "plutonium"}
    cost: float = 10000

    def on_execute(self, outcome: State):
        print('Nuclear fission FAILED!!!...')
        self.status = ActionStatus.FAILURE


class WaitForThunderStorm(Action):
    effects = {"has_power": ...}
    preconditions: State = {"predict_lightening_strike": True}
    cost: float = 1000000

    def on_execute(self, desired_state: State):
        print('Waiting for thunderstorm...')
        self.status = ActionStatus.SUCCESS  # Ensure the action status is set

    def on_success(self, outcome: State = None):
        print(f">>>{outcome['has_power']} available...")
        return super().on_success(outcome)


class AccelerateToCriticalSpeed(Action):
    effects: State = {"critical_speed": ...}
    preconditions: State = {"has_power": "@required_power"}

    def on_execute(self, desired_state: State):
        print(f"Accelerating {self.agent.state['has_car']} to {self.effects['critical_speed']}...")
        self.status = ActionStatus.SUCCESS  # Ensure the action status is set


class GetCar(Action):
    effects: State = {"has_car": ...}
    preconditions: State = {"year": "1955", "car_at_doc_browns_lab": "$has_car"}

    def on_execute(self, desired_state: State):
        print(f"Getting Car: {desired_state['has_car']} ...")
        return super().on_execute(desired_state)


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
    ai.update_state(world_state)

    print("Goal State:   ", goal_state)
    #
    # # option 1
    # plan = ai.get_plan(goal_state)
    # ai.execute_plan(plan)
    #
    # # option 2
    for plan in ai.plan_and_execute(goal_state, verbose=True):
        input()
