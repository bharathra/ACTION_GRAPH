#! /usr/bin/env python3

import time
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if True:
    from action_graph.agent import Agent, Action, ActionStatus, State


class AwaitTaskCompletion(Action):
    effects = {"TASK": ...}
    preconditions = {"OFFLOADED": "$TASK"}
    auto_reset = True

    def execute(self):
        print("Awaiting task completion...")
        self.status = ActionStatus.SUCCESS

    def on_success(self):
        print("Task completed.")


class OffloadTask(Action):
    effects = {"OFFLOADED": ...}
    preconditions = {"TASK.METAPLAN.OKAY": "$OFFLOADED",
                     "EE.READY": "$OFFLOADED",
                     "ROBOT.LOCATION": "$OFFLOADED/TASK.INIT.POSE"}
    auto_reset = True

    def execute(self):
        print("Offloading task...")
        self.status = ActionStatus.SUCCESS


class CheckEE(Action):
    effects = {"EE.READY": ...}
    auto_reset = True

    def execute(self):
        ee_ready = True
        # ee_ready = False  # uncomment to fail
        if not ee_ready:
            self.status = ActionStatus.FAILURE
            return
        self.status = ActionStatus.SUCCESS


class TaskMetaPlan(Action):
    effects = {"TASK.METAPLAN.OKAY": ...}
    preconditions = {"ROBOT.LOCATION": "$TASK.METAPLAN.OKAY/TASK.INIT.POSE"}
    async_exec = True
    auto_reset = True

    def execute(self):
        t0 = time.time()
        while time.time() - t0 < 0.5:
            print("TaskMetaPlan running...")
            time.sleep(0.1)
        self.status = ActionStatus.SUCCESS
        # self.status = ActionStatus.FAILURE  # uncomment to fail


class RobotGoTo(Action):
    effects = {"ROBOT.LOCATION": ...}
    preconditions = {"TASK.INFO.LOADED": "$ROBOT.LOCATION"}
    auto_reset = True

    def execute(self):
        location = self.agent.state['LOC']
        print(f"Moving robot to {location}")
        self.status = ActionStatus.SUCCESS


class GetTaskInfo(Action):
    effects = {"TASK.INFO.LOADED": ...}
    auto_reset = True

    def execute(self):
        task = self.effects["TASK.INFO.LOADED"]
        self.agent.state["LOC"] = task

        selected_tasks = self.agent.state.get("SEL.TASKS", [])
        print(f"Selected tasks: {selected_tasks}")
        if selected_tasks and "NEXT" in task:
            nexttask = selected_tasks.pop(0)
            self.agent.state["LOC"] = nexttask

        print(f"Task info loaded: {self.agent.state['LOC']}")
        self.status = ActionStatus.SUCCESS


if __name__ == "__main__":

    ai = Agent()
    actions = [a(ai) for a in Action.__subclasses__()]
    ai.load_actions(actions)
    ai.state = {"SEL.TASKS": ["T1", "T2", "T3", "T4", "T5"]}

    # # simpler approach (assuming we know the optimal order of tasks)
    # for t in ai.state["SEL.TASKS"]:
    #     goal_state = {"TASK": t}
    #     for plan in ai.plan_and_execute(goal_state, verbose=True):
    #         input()

    # more complex approach (the optimal order is decided at runtime)
    while ai.state["SEL.TASKS"]:
        goal_state = {"TASK": "NEXT"}
        for plan in ai.plan_and_execute(goal_state, verbose=True):
            pass

    ai.state["TASK"] = ""
