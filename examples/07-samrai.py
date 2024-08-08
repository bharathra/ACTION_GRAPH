#! /usr/bin/env python3

import os
import sys
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from action_graph.action import Action, ActionStatus, State
from action_graph.agent import Agent


class ApproachSeam(Action):
    effects = {"AT.SEAM.START": ...}
    preconditions = {"AT.PILOT.POSE": "$AT.SEAM.START"}

    cost = 100


class AutoSealProduct(Action):
    effects = {"SEAL": ...}
    preconditions = {"ROBOT.DO.SEAL": "$SEAL"}


class SealFilletA(Action):
    effects = {"SEAL_A": ...}
    preconditions = {"ROBOT.DO.SEAL": "$SEAL_A"}


class SealFilletW(Action):
    effects = {"SEAL_W": ...}
    preconditions = {"ROBOT.DO.SEAL": "$SEAL_W"}


class AwaitTaskCompletion(Action):
    effects = {"ROBOT.DO.SEAL": ...}
    preconditions = {"ROBOT.SEAL.TRIGGERED": "$ROBOT.DO.SEAL"}


class CheckSafety(Action):
    effects = {"CELL.IS.SAFE": True}
    preconditions = {"USER.APPROVED": True}


class DisposeNozzle(Action):
    effects = {"DISPOSE": ...}
    preconditions = {"ROBOT.ISAT.NOZL.CHANGE.STN": "$DISPOSE"}


class GetDirectionVector(Action):
    effects = {"AGENT.HAS.DIRECTION": ...}
    preconditions = {"SEAMTRACK.METAPLAN.OK": "$AGENT.HAS.DIRECTION"}


class ScanForNozzle(Action):
    effects = {"SCAN_N": ...}
    preconditions = {"ROBOT.ISAT.NOZZLEID.LOC": "$SCAN_N"}


class GetUserApproval(Action):
    effects = {"USER.APPROVED": True}


class GotoTaskPilotPose(Action):
    effects = {"AT.PILOT.POSE": ...}
    preconditions = {"NOZZLE.LOADED": "$AT.PILOT.POSE",
                     "CELL.IS.SAFE": True,
                     "ROBOT.IS.READY": True, }
    cost = 100


class GotoTaskStart(Action):
    effects = {"AT.SEAM.START": ...}
    preconditions = {"NOZZLE.LOADED": "$AT.SEAM.START",
                     "CELL.IS.SAFE": True,
                     "ROBOT.IS.READY": True, }
    cost = 10


class _LoadNozzleAuto(Action):
    effects = {"NOZZLE.LOADED": ...}
    preconditions = {"DISPOSE": "$NOZZLE.LOADED",
                     "ROBOT.ISAT.NOZZLE.LOC": "$NOZZLE.LOADED"}
    cost = 1000


class LoadNozzleManually(Action):
    effects = {"NOZZLE.LOADED": ...}
    preconditions = {"ROBOT.ISAT.NOZL.CHANGE.STN": "$NOZZLE.LOADED"}
    cost = 100


class LoadNozzleSemiAuto(Action):
    effects = {"NOZZLE.LOADED": ...}
    preconditions = {"SCAN_N": "$NOZZLE.LOADED"}
    cost = 10

    def on_execute(self, outcome: State):
        _timeout_ = 5
        t0 = time.time()
        while time.time() - t0 < _timeout_:
            print(f'Wating for nozzle change....')
            time.sleep(1)
            #
        self.status = ActionStatus.SUCCESS
        return


class LoadSealData(Action):
    effects = {"SEAL.DATA.LOADED": ...}


class _CachedMoveToTaskPilotPose(Action):
    effects = {"AT.PILOT.POSE": ...}
    preconditions = {"NOZZLE.LOADED": "$AT.PILOT.POSE",
                     "CELL.IS.SAFE": True,
                     "ROBOT.IS.READY": True, }

    def on_execute(self, outcome: State):
        # Simulate Failure: No cached js
        self.status = ActionStatus.FAILURE


class CachedMoveToTaskStart(Action):
    effects = {"AT.SEAM.START": ...}
    preconditions = {"NOZZLE.LOADED": "$AT.SEAM.START",
                     "CELL.IS.SAFE": True,
                     "ROBOT.IS.READY": True, }

    cost = 1

    def on_execute(self, outcome: State):
        # Simulate Failure: No cached js
        self.status = ActionStatus.FAILURE


class PrepRobot(Action):
    effects = {"ROBOT.IS.READY": True}


class RobotGotoTask(Action):
    effects = {"ROBOT.ISAT": ...}
    preconditions = {"ROBOT.IS.READY": True,
                     "CELL.IS.SAFE": True,
                     }


class RobotGotoNozzleIDLoc(Action):
    effects = {"ROBOT.ISAT.NOZZLEID.LOC": ...}
    preconditions = {"ROBOT.IS.READY": True,
                     "CELL.IS.SAFE": True,
                     }


class _RobotGotoNozzleLoc(Action):
    effects = {"ROBOT.ISAT.NOZZLE.LOC": ...}
    preconditions = {"SCAN_N": "$ROBOT.ISAT.NOZZLE.LOC",
                     "ROBOT.IS.READY": True,
                     "CELL.IS.SAFE": True,
                     }


class RobotGoToManNozlChangeStn(Action):
    effects = {"ROBOT.ISAT.NOZL.CHANGE.STN": ...}
    preconditions = {"ROBOT.IS.READY": True,
                     "CELL.IS.SAFE": True,
                     }


class SeamTrackMetaPlan(Action):
    effects = {"SEAMTRACK.METAPLAN.OK": ...}
    preconditions = {"AT.SEAM.START": "$SEAMTRACK.METAPLAN.OK"}

    def on_execute(self, outcome: State):
        if self.agent.state['PLAN.ATTEMPT'] <= 0:
            print('RECONFIGURED')
            self.agent.state['PLAN.ATTEMPT'] = 1
            self.agent.state["AT.PILOT.POSE"] = ''
            self.agent.state["AT.SEAM.START"] = ''
            self.agent.state["SEAL.DATA.LOADED"] = ''
            self.status = ActionStatus.NEUTRAL
            return

        self.status = ActionStatus.SUCCESS


class TriggerTask(Action):
    effects = {"ROBOT.SEAL.TRIGGERED": ...}
    preconditions = {"SEAMTRACK.METAPLAN.OK": "$ROBOT.SEAL.TRIGGERED"}


class VerifyNozzleType(Action):
    effects = {"NOZZLE.LOADED": ...}
    preconditions = {"SEAL.DATA.LOADED": "$NOZZLE.LOADED"}

    def on_execute(self, outcome: State):
        # Simulate Failure: Assume the current EE is not the same as reqired EE
        self.status = ActionStatus.FAILURE


class RobotGoToZone(Action):
    effects = {"ROBOT.ISAT.ZONE": ...}
    preconditions = {"ROBOT.IS.READY": True,
                     "CELL.IS.SAFE": True,
                     }


class _AlignZone(Action):
    effects = {"ZONE.ALIGNED": ...}
    preconditions = {"ROBOT.ISAT.ZONE": "$ZONE.ALIGNED"}
    cost = 10

    def on_execute(self, outcome: State):
        # Scan
        # Register
        # Apply Calibration Transform
        # Set aligned state to True
        self.agent.state['LAST.ALIGNED.ZONE'] = 'Z3'
        self.status = ActionStatus.SUCCESS


class _CheckZoneAlignment(Action):
    effects = {"ZONE.ALIGNED": ...}
    preconditions = {"SEAL.DATA.LOADED": "$ZONE.ALIGNED"}
    cost = 1

    def on_execute(self, outcome: State):
        # Get the zone of the current TaskSegment
        active_zone = 'Z1'  # hardcoded
        # Check if it was aligned earlier
        if 'LAST.ALIGNED.ZONE' in self.agent.state and \
                active_zone == self.agent.state['LAST.ALIGNED.ZONE']:
            self.status = ActionStatus.SUCCESS
            return
        # Simulate Failure: Assume the Zone in not aligned
        self.status = ActionStatus.FAILURE


class SealFastener(Action):
    effects = {'SEAL_F': ...}
    preconditions = {"ROBOT.DO.SEAL": "$SEAL_F"}


class SealBrushA(Action):
    effects = {'SEAL_B_A': ...}
    preconditions = {"ROBOT.DO.SEAL": "$SEAL_B_A"}


class SealBrushW(Action):
    effects = {'SEAL_B_W': ...}
    preconditions = {"ROBOT.DO.SEAL": "$SEAL_B_W"}


class CalibrateZividCamera(Action):
    effects = {'SCAN_Z.CAL_Z': ...}
    preconditions = {"GRID.SCANNED": '$SCAN_Z.CAL_Z'}


class ScanCalibrationGrid(Action):
    effects = {"GRID.SCANNED": ...}
    preconditions = {"ROBOT.ISAT.TASK": "$GRID.SCANNED"}

    def on_execute(self, outcome: State):
        if self.agent.state['SCAN.TARGET'] > 3:
            self.status = ActionStatus.SUCCESS
            return
        self.agent.state['SCAN.TARGET'] += 1
        self.agent.state["ROBOT.ISAT.TASK"] = ''
        self.agent.state["TASK.DATA.LOADED"] = ''
        self.status = ActionStatus.NEUTRAL
        return


class RobotGotoTask(Action):
    effects = {"ROBOT.ISAT.TASK": ...}
    preconditions = {"ROBOT.IS.READY": True,
                     "CELL.IS.SAFE": True,
                     "TASK.DATA.LOADED": "$ROBOT.ISAT.TASK",
                     }


class LoadTaskData(Action):
    effects = {"TASK.DATA.LOADED": ...}


class CalibrateStation(Action):
    effects = {'CALIBRATE.STATION': ...}
    preconditions = {"PRODUCT.SCANNED": '$CALIBRATE.STATION'}


class ScanProduct(Action):
    effects = {"PRODUCT.SCANNED": ...}
    preconditions = {"ROBOT.ISAT.TASK": "$PRODUCT.SCANNED"}

    def on_execute(self, outcome: State):
        if self.agent.state['SCAN.TARGET'] > 3:
            self.status = ActionStatus.SUCCESS
            return
        self.agent.state['SCAN.TARGET'] += 1
        self.agent.state["ROBOT.ISAT.TASK"] = ''
        self.agent.state["TASK.DATA.LOADED"] = ''
        self.status = ActionStatus.NEUTRAL
        return


if __name__ == "__main__":

    ai = Agent()
    ai.state = {"SEAL.DATA.LOADED": '',
                "TASK.DATA.LOADED": '',
                "CELL.IS.SAFE": '',
                "ROBOT.DO.SEAL": '',
                "ROBOT.IS.READY": False,
                "ROBOT.SEAL.TRIGGERED": '',
                "PLAN.ATTEMPT": 0,
                "SAFE.MODE": True,
                "USER.APPROVED": False,
                "SCAN.TARGET": 0,
                }
    # print("Initial State:", ai.state)

    actions = [a(ai) for a in Action.__subclasses__()]
    ai.load_actions(actions)

    # goal_state = {"SEAL_A": "P123|A123"}
    goal_state = {"SEAL_W": "P123|W123"}
    # goal_state = {"SEAL_F": "P123|F123"}
    # goal_state = {'SCAN_Z.CAL_Z': "GRID|AUTO"}
    # goal_state = {'PRODUCT.SCANNED': "P123|AUTO"}
    # goal_state = {"DISPOSE": "P123|D123"}
    # print("Goal State:   ", goal_state)

    # plan = ai.get_plan(goal_state)
    # ai.print_plan_to_console(plan)
    # ai.execute_plan(plan)

    for plan in ai.plan_and_execute(goal_state, verbose=True):
        input()

