#! /usr/bin/env python3

import logging
from time import sleep
from enum import Enum, auto
from typing import List

from action_graph.action import Action, ActionStatus, State
from action_graph.planner import Planner


class ExecStatus(Enum):
    FAILURE = auto()
    SUCCESS = auto()
    RUNNING = auto()
    ABORTED = auto()


class Agent:
    """Autonomous agent to monitor system state, keep track of feasible actions, generate plans and achive desired goals"""

    __execution_status: ExecStatus = ExecStatus.SUCCESS
    __planner: Planner = Planner([])
    __abort: bool = False

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

    def get_plan(self, goal: State, start_state: State = None, actions: List[Action] = None) -> List[Action]:
        """
        Generate an action plan for the specified goal state.
        If no start_state is provided, the current state of the system is used. 

        :param goal:State: Specify the goal state.
        :param start_state:State=None: Specify a start state that is not the current state.
        :param actions:List[Action]=None: List of actions that the planner can use; 
                                          If this is not specified, the planner will use the 
                                          previously loaded actions to plan.
        :return:List[Action]: The plan - dictionary of actions and their expected outcomes. 
        """

        if not start_state:
            start_state = self.state

        if actions:
            self.__planner.update_actions(actions)

        plan: List[Action] = self.__planner.generate_plan(goal, self.state)
        if not plan:
            logging.error(f"Planning Failed!")
            return []

        self.__print_plan(plan)
        return plan

    def execute_plan(self, plan: List[Action]):
        """
        Execute a previously generated plan.

        :param plan:List[Action]: Dictionary of actions and their expected outcomes (State)
        """
        
        if not plan:
            raise Exception('No plan to execute!')
        
        print('EXECUTING:')
        for action in plan:
            #
            self.__execute_action(action)
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
            plan: List[Action] = self.__planner.generate_plan(goal, self.state)
            if not plan:
                self.__execution_status = ExecStatus.FAILURE
                logging.error(f"Planning Failed!")
                return []
            # execute one plan step at a time
            if verbose:
                self.__print_plan(plan)
            self.__execute_action(plan[0])
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

    def __print_plan(self, plan: List[Action]):
        if plan:
            plan_str = '\nPLAN:\n'
            for ix, action in enumerate(plan):
                plan_str += "....."*(ix+1) + str(action) + ' --> ' + str(action.effects) + '\n'
            print(plan_str)

    def __execute_action(self, action):
        # initialize
        self.__execution_status = ExecStatus.RUNNING

        if self.__abort:
            # logging.error(f'{action} : EXECUTION ABORTED BEFORE START !!')
            action.on_aborted(action.effects)
            self.__execution_status = ExecStatus.ABORTED

        # Initialise plan step
        if not action.check_runtime_precondition(action.effects):
            # Stop execution as action cannot be executed
            self.__execution_status = ExecStatus.FAILURE

        # Execute the plan step
        action._execute(action.effects)

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
            for k, v in action.effects.items():
                self.state[k] = v
            #
            # logging.debug(f'[{action}] Action succeded.')
            action.on_success(action.effects)
            self.__execution_status = ExecStatus.SUCCESS

        # Execution failed
        if action.status == ActionStatus.FAILURE:
            action.on_failure(action.effects)
            # Stop execution as action failed
            logging.error(f'[{action}] ACTION FAILED!')
            self.__execution_status = ExecStatus.FAILURE

        # Execution aborted
        if action.status == ActionStatus.ABORTED:
            action.on_aborted(action.effects)
            # Stop execution as action aborted
            logging.critical(f'[{action}] ACTION ABORTED!')
            self.__execution_status = ExecStatus.ABORTED

        # Any clean up needed after execution e.g. updating system states
        action.on_exit(action.effects)
