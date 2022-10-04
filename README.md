# ACTION_GRAPH
A symbolic AI agent for generating action plans based on preconditions and effects. Similar to Goal Oriented Action Plan in concept, but this implementation treats individual state variables as nodes and uses Dijikstra's (A* but without the heuristic cost estimate) to generate a feasible, lowest cost plan.


## Usage:

```

from action_graph.agent import Agent
from action_graph.action import Action


class Drive(Action):
    effects = {"driving": True}
    preconditions = {"has_drivers_license": True, "tank_has_gas": True}


class FillGas(Action):
    effects = {"tank_has_gas": True}
    preconditions = {"has_car": True}


class RentCar(Action):
    effects = {"has_car": True}

    cost = 100  # dollars


class BuyCar(Action):
    effects = {"has_car": True}
    preconditions = {}

    cost = 10_000  # dollars


if __name__ == "__main__":
    world_state = {"has_car": False, "has_drivers_license": True}
    goal_state = {"driving": True}

    ai = Agent()

    actions = [a(ai) for a in Action.__subclasses__()]
    ai.load_actions(actions)

    print("Initial State:", world_state)
    ai.update_state(world_state)

    print("Goal State:   ", goal_state)
    plan = ai.get_plan(goal_state)

    # ai.execute_plan(plan)

```

The interfaces for this library are similar to https://github.com/agoose77/GOAP.
For more information on GOAP refer to http://alumni.media.mit.edu/~jorkin/goap.html

