#! /usr/bin/env python3

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if True:
    from action_graph.agent import Agent, Action, ActionStatus, State


class AwaitSealCompletion(Action):
    effects = {"SEAL": ...}
    preconditions = {"OFFLOADED": "$SEAL"}


class OffloadTask(Action):
    effects = {"OFFLOADED": ...}
    preconditions = {"NOZZLE.READY": "$OFFLOADED",
                     "SEAMTRACK.METAPLAN": "$OFFLOADED"}


class CheckNozzle(Action):
    effects = {"NOZZLE.READY": ...}

    def execute(self):
        nozzle_ready = True
        # nozzle_ready = False  # uncomment to fail
        if not nozzle_ready:
            self.status = ActionStatus.FAILURE
            return
        self.status = ActionStatus.SUCCESS


class SeamTrackMetaPlan(Action):
    effects = {"SEAMTRACK.METAPLAN": ...}
    preconditions = {"ROBOT.LOCATION": "$SEAMTRACK.METAPLAN/SEAM.START"}


class RobotGoTo(Action):
    effects = {"ROBOT.LOCATION": ...}
    preconditions = {"POSE.INFO.LOADED": "$ROBOT.LOCATION"}


class GetPoseInfo(Action):
    effects = {"POSE.INFO.LOADED": ...}

    def execute(self):
        task_spec = self.effects["POSE.INFO.LOADED"]
        task, spec = self.get_pose_info(task_spec)
        # pose_info = ""  # uncomment to fail
        print(f"Getting pose info for {task} {spec}")
        if not spec:
            self.status = ActionStatus.FAILURE
            return
        self.status = ActionStatus.SUCCESS

    def get_pose_info(self, task_spec):
        task, spec = task_spec.split("/")
        return task, spec


if __name__ == "__main__":

    ai = Agent()
    actions = [a(ai) for a in Action.__subclasses__()]
    ai.load_actions(actions)
    ai.state = {}

    goal_state = {"SEAL": "P1|W1"}
    ai.state.update({"GOAL": list(goal_state.items())[0]})
    for plan in ai.plan_and_execute(goal_state, verbose=True):
        print(ai.state)
        input()
