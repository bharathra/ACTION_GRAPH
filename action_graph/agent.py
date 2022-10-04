#! /usr/bin/env python3

import logging
from time import sleep, time
from typing import List

from action_graph.action import (Action, ActionStatus, State,
                                 ActionTimedOutException, ActionAbortedException, ActionFailedException)
from action_graph.planner import Planner, PlanningFailedException


class Agent:
    """Autonomous agent to monitor system state, keep track of feasible actions, generate plans and achive desired goals"""

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
        Updates system state with the incoming state.        

        :param state:State: New state
        """

        self.state.update(state)

    def abort(self):
        """
        Abort execution.
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

    def get_plan(self, goal: State, start_state: State = None, actions: List[Action] = None, verbose=False) -> List[Action]:
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

        try:
            plan: List[Action] = self.__planner.generate_plan(goal, start_state)
            if verbose:
                self._print_plan(plan)
            return plan
            #
        except PlanningFailedException as pfx:
            logging.error(f"PLANNING FAILED! {pfx}")
            return []

    def execute_plan(self, plan: List[Action]):
        """
        Execute a previously generated plan.

        :param plan:List[Action]: Dictionary of actions and their expected outcomes (State)
        """

        if not plan:
            logging.error(f"NO PLAN AVAILABLE! ABORTING EXECUTION.")
            return

        try:
            for action in plan:
                self.execute_action(action)
            #
        except ActionFailedException:
            logging.error(f"EXECUTION FAILED!")
            return

        except ActionAbortedException:
            logging.critical(f"EXECUTION ABORTED!")
            return

        except ActionTimedOutException:
            logging.error(f"EXECUTION TIMED OUT! ABORTING.")
            self.abort()
            return
        #
        logging.info(f"EXECUTION SUCCEDED!")

    def achieve_goal(self, goal: State, verbose: bool = False):
        """
        Creates a plan to satisfy the goal state; executes it action-by-action; re-evaluates the plan at each step;

        :param goal:State: Desired goal state
        """

        # state might have changed since the last step was executed
        while not self.is_goal_met(goal):

            try:
                # (re)generate the plan
                plan: List[Action] = self.__planner.generate_plan(goal, self.state)
                if verbose:
                    self._print_plan(plan)
                # execute one plan step at a time
                self.execute_action(plan[0])

            except PlanningFailedException:
                logging.error(f"PLANNING FAILED!")
                return

            except ActionFailedException:
                logging.error(f"EXECUTION FAILED!")
                return

            except ActionAbortedException:
                logging.critical(f"EXECUTION ABORTED!")
                return

            except ActionTimedOutException:
                logging.error(f"EXECUTION TIMED OUT! ABORTING.")
                self.abort()
                return
        #
        logging.info(f"EXECUTION SUCCEDED!")

    def _print_plan(self, plan: List[Action]):
        if plan:
            plan_str = '\nPLAN:\n'
            for ix, action in enumerate(plan):
                plan_str += "....."*(ix+1) + str(action) + ' --> ' + str(action.effects) + '\n'
            print(plan_str)

    def execute_action(self, action: Action):
        # Check for abort status
        if self.__abort:
            # logging.error(f'{action} : EXECUTION ABORTED BEFORE START !!')
            action.on_aborted(action.effects)
            raise ActionAbortedException(f'[{action}] FAILED. ABORTED STATE IS ACTIVE!!')

        # Check runtime precondition
        if not action.check_runtime_precondition(action.effects):
            raise ActionFailedException(f'[{action}] RUNTIME PRECONDITION CHECK FAILED!!.')

        # Execute the plan step
        action._execute(action.effects)
        # action.execute is an async process inside _execute,
        # monitor the status from outside

        # Wait until execution is complete
        time0 = time()
        while action.is_running():
            if self.__abort:
                # if an abort was signalled
                logging.critical(f'[{action}] : EXECUTION ABORTED!!')
                action.status = ActionStatus.ABORTED
                break
            if time()-time0 > action.timeout:
                # Action timeout exceeded
                raise ActionTimedOutException(f'[{action}] : ACTION TIMED OUT!!')
            if not action.status == ActionStatus.RUNNING:
                # thread is alive but the status has changed
                break  # so move on
            sleep(0.05)  # throttle loop
            # logging.debug(f'Action: {str(action)} is running...')

        # Execution completed but with RUNNING Status
        if action.status == ActionStatus.RUNNING:
            # the user forgot to set the status; or something bad happened;
            # let's treat this as FAILURE!
            action.status = ActionStatus.FAILURE
            logging.warning(f'[{action}] ACTION STATUS UNKNOWN; ASSUMING FAILURE!!')

        # Execution completed with SUCCESS Status
        if action.status == ActionStatus.SUCCESS:
            # Action executed without errors;
            # update the state with the predicted outcomes
            for k, v in action.effects.items():
                self.state[k] = v
            # logging.debug(f'[{action}] Action succeded.')
            action.on_success(action.effects)

        # Execution failed
        if action.status == ActionStatus.FAILURE:
            action.on_failure(action.effects)
            # Stop execution as action failed
            raise ActionFailedException(f'[{action}] ACTION FAILED!')

        # Execution aborted
        if action.status == ActionStatus.ABORTED:
            action.on_aborted(action.effects)
            # Stop execution as action aborted
            raise ActionAbortedException(f'[{action}] ACTION ABORTED!')

        # Any clean up needed after execution e.g. updating system states
        action.on_exit(action.effects)
