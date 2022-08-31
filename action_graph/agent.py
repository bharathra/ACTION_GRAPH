#! /usr/bin/env python3

import logging
from time import sleep
from enum import Enum, auto
from typing import List

from action_graph.action import Action, ActionStatus, State
from action_graph.planner import Planner, Plan


class ExecStatus(Enum):
    FAILURE = auto()
    SUCCESS = auto()
    RUNNING = auto()
    ABORTED = auto()


class Agent:
    """Autonomous agent to monitor system state, keep track of feasible actions, generate plans and achive desired goals"""

    __execution_status: ExecStatus = ExecStatus.SUCCESS
    __planner = Planner([])
    __abort = False

    def __init__(self, agent_name=None) -> None:
        if not agent_name:
            agent_name = self.__class__.__name__
        self.name = agent_name
        #
        self.state: State = {}

    def load_actions(self, actions: List[Action]):
        self.__planner.update_actions(actions)

    def update_state(self, state: State):
        """
        Updates the state of the robot. It takes in a State dictionary that contains 
        new information about the state and updates it to reflect this new information.        

        :param state:State: Update the state of the agent
        """

        self.state = {**self.state, **state}

    def abort(self):
        """
        The abort function is used to stop the agent from continuing with execution.
        It is called by the planner when it encounters an error, and can also be called by the user.        
        """

        self.__abort = True

    def reset(self):
        """
        Resets the abort status back to False in the event abort was triggered.
        """

        self.__abort = False

    def is_goal_met(self, goal: State) -> bool:
        """
        Compares the desired goal state against the system state to check if it is already met.

        :param goal:State: Desired goal state
        :return:bool: True if goal state and current system state is same; False otherwise
        """

        if not goal:
            return True
        #
        _goals_met = True
        for k, v in goal.items():
            if self.state[k] != v:
                _goals_met = False
        #
        return _goals_met

    def achieve_goal(self, goal: State, announce: bool = True):
        """
        Creates a plan to satisfy the goal state and executes it.

        :param goal:State: Desired goal state
        """

        # state might have changed since the last time we planned
        while not self.is_goal_met(goal):
            # (re)generate the plan
            plan_steps: Plan = self.__planner.find_plan(self.state, goal)
            if not plan_steps:
                self.__execution_status = ExecStatus.FAILURE
                logging.error(f"Execution Failed!")
                return
            # execute one plan step at a time
            if announce:
                self.__print_plan(plan_steps)
            self.__execute_plan_step(next(iter(plan_steps.items())))
            #
            # if the exec status is still RUNNING, something's gone wrong
            if self.__execution_status == ExecStatus.RUNNING:
                logging.error(f"Execution is Stuck! Aborting")
                self.abort()
                return
            # if the exec FAILURE; abort
            if self.__execution_status == ExecStatus.FAILURE:
                logging.error(f"Execution Failed!")
                return
            # if the exec ABORTED; abort
            if self.__execution_status == ExecStatus.ABORTED:
                logging.critical(f"Execution Aborted!")
                return
        #
        logging.info(f"Execution Succeded!")

    def __print_plan(self, plan: Plan):
        if plan:
            # print(f'PLAN: {list(plan.keys())}')
            # print(list(plan.values()))
            plan_str = '\nPLAN:\n'
            for ix, step in enumerate(plan):
                plan_str += "....."*(ix+1) + str(step) + ' --> ' + str(plan[step]) + '\n'
            print(plan_str)

    def __execute_plan_step(self, plan_step):
        # initialize
        action, services = plan_step
        self.__execution_status = ExecStatus.RUNNING

        if self.__abort:
            # logging.error(f'{action} : EXECUTION ABORTED BEFORE START !!')
            action.on_aborted(services)
            self.__execution_status = ExecStatus.ABORTED

        # Initialise plan step
        if not action.check_runtime_precondition(services):
            # Stop execution as action cannot be executed
            self.__execution_status = ExecStatus.FAILURE

        # Run any prerequisites just before staring the execution
        action.pre_execution(services)

        # Execute the plan step
        action.execute(services)

        # Wait until execution is complete
        # action.execute is an async process inside _execute,
        # monitor the status from outside
        while action.is_running():
            # Unless an abort was signalled
            if self.__abort:
                logging.critical(f'{action} : EXECUTION ABORTED!!')
                action.status = ActionStatus.ABORTED
                break
            if not action.status == ActionStatus.RUNNING:
                # thread is alive but the status has changed
                break  # so move on
            # throttle loop
            sleep(0.05)
            # logging.warning(f'{self.name} Action: {str(action)} is running...')

        # Execution completed but with RUNNING Status
        if action.status == ActionStatus.RUNNING:
            # the user forgot to set the status; or something bad happened;
            # let's treat this as FAILURE!
            action.status = ActionStatus.FAILURE
            logging.warning(f'[{action}] Action status UNKNOWN; Assuming action failed!')

        # Execution completed with SUCCESS Status
        if action.status == ActionStatus.SUCCESS:
            # Action executed withot errors; 
            # update the state with the predicted outcomes
            for k, v in services.items():
                self.state[k] = v
            #
            # logging.debug(f'[{action}] Action succeded.')
            action.on_success(services)
            self.__execution_status = ExecStatus.SUCCESS

        # Execution failed
        if action.status == ActionStatus.FAILURE:
            action.on_failure(services)
            # Stop execution as action failed
            logging.error(f'[{action}] ACTION FAILED!')
            self.__execution_status = ExecStatus.FAILURE

        # Execution aborted
        if action.status == ActionStatus.ABORTED:
            action.on_aborted(services)
            # Stop execution as action aborted
            logging.critical(f'[{action}] ACTION ABORTED!')
            self.__execution_status = ExecStatus.ABORTED

        # Any clean up needed after execution e.g. updating system states
        action.on_exit(services)
