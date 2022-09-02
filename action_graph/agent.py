#! /usr/bin/env python3

import logging
from time import sleep
from enum import Enum, auto
from typing import ClassVar, List

from action_graph.action import Action, ActionStatus, State
from action_graph.planner import Planner, Plan


class ExecStatus(Enum):
    FAILURE = auto()
    SUCCESS = auto()
    RUNNING = auto()
    ABORTED = auto()


class Agent:
    """Autonomous agent to monitor system state, keep track of feasible actions, generate plans and achive desired goals"""

    __execution_status: ClassVar[ExecStatus] = ExecStatus.SUCCESS
    __planner: ClassVar[Planner] = Planner([])
    __abort: ClassVar[bool] = False

    def __init__(self, agent_name=None) -> None:
        if not agent_name:
            agent_name = self.__class__.__name__
        self.name = agent_name
        #
        self.state: State = {}

    def load_actions(self, actions: List[Action]):
        """
        Load actions list; refresh in case of any changes to the actions data.

        :param actions:List[Action]: List of actions.
        """

        self.__planner.update_actions(actions)

    def update_state(self, state: State):
        """
        Updates the state of the robot. It takes in a State dictionary that contains 
        new information about the state and updates it to reflect this new information.        

        :param state:State: Update the state of the agent
        """

        self.state.update(state)

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

    def find_plan(self, goal: State, start_state: State = None, actions: List[Action] = None):
        """
        Generate an action plan for the specified goal state.
        If no start_state is provided, the current state of the system is used. 

        :param goal:State: Specify the goal state.
        :param start_state:State=None: Specify a start state that is not the current state.
        :param actions:List[Action]=None: List of actions that the planner can use; 
                                          If this is not specified, the planner will use the 
                                          previously loaded actions to plan.
        :return:Plan: The plan - dictionary of actions and their expected outcomes. 
        """

        if not start_state:
            start_state = self.state

        if actions:
            self.__planner.update_actions(actions)

        plan: Plan = self.__planner.find_plan(self.state, goal)
        if not plan:
            logging.error(f"Planning Failed!")
            return

        self.__print_plan(plan)
        return plan

    def execute_plan(self, plan: Plan):
        """
        Execute a previously generated plan.

        :param plan:Plan: Dictionary of actions and their expected outcomes (State)
        """
        
        if not plan:
            raise Exception('No plan to execute!')
        
        print('EXECUTING:')
        for plan_step in plan.items():
            #
            self.__execute_plan_step(plan_step)
            # if the exec status is still RUNNING, something's gone wrong
            if self.__execution_status == ExecStatus.RUNNING:
                logging.error(f"Execution is stuck! Aborting.")
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

        logging.info(f"Execution Succeded!")

    def achieve_goal(self, goal: State, verbose: bool = False):
        """
        Creates a plan to satisfy the goal state; executes it action-by-action; re-evaluates the plan at each step;

        :param goal:State: Desired goal state
        """

        # state might have changed since the last step was executed
        while not self.is_goal_met(goal):
            # (re)generate the plan
            plan: Plan = self.__planner.find_plan(self.state, goal)
            if not plan:
                self.__execution_status = ExecStatus.FAILURE
                logging.error(f"Planning Failed!")
                return
            # execute one plan step at a time
            if verbose:
                self.__print_plan(plan)
            self.__execute_plan_step(next(iter(plan.items())))
            #
            # if the exec status is still RUNNING, something's gone wrong
            if self.__execution_status == ExecStatus.RUNNING:
                logging.error(f"Execution is stuck! Aborting.")
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
        action, expected_outcome = plan_step
        self.__execution_status = ExecStatus.RUNNING

        if self.__abort:
            # logging.error(f'{action} : EXECUTION ABORTED BEFORE START !!')
            action.on_aborted(expected_outcome)
            self.__execution_status = ExecStatus.ABORTED

        # Initialise plan step
        if not action.check_runtime_precondition(expected_outcome):
            # Stop execution as action cannot be executed
            self.__execution_status = ExecStatus.FAILURE

        # Execute the plan step
        action._execute(expected_outcome)

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
            # logging.debug(f'Action: {str(action)} is running...')

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
            for k, v in expected_outcome.items():
                self.state[k] = v
            #
            # logging.debug(f'[{action}] Action succeded.')
            action.on_success(expected_outcome)
            self.__execution_status = ExecStatus.SUCCESS

        # Execution failed
        if action.status == ActionStatus.FAILURE:
            action.on_failure(expected_outcome)
            # Stop execution as action failed
            logging.error(f'[{action}] ACTION FAILED!')
            self.__execution_status = ExecStatus.FAILURE

        # Execution aborted
        if action.status == ActionStatus.ABORTED:
            action.on_aborted(expected_outcome)
            # Stop execution as action aborted
            logging.critical(f'[{action}] ACTION ABORTED!')
            self.__execution_status = ExecStatus.ABORTED

        # Any clean up needed after execution e.g. updating system states
        action.on_exit(expected_outcome)
