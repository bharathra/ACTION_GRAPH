#! /usr/bin/env python3

import logging
from time import sleep, time
from typing import Iterable, List

from action_graph.action import (Action, ActionStatus, State,
                                 ActionTimedOutException, ActionAbortedException, 
                                 ActionFailedException, ActionPreemptedException)
from action_graph.planner import Planner, PlanningFailedException


class Agent:
    """Autonomous agent to monitor system state, keep track of feasible actions, generate plans and achive desired goals"""

    __planner: Planner = Planner([])
    __abort: bool = False
    __preempted: bool = False

    def __init__(self, agent_name=None) -> None:
        if not agent_name:
            agent_name = self.__class__.__name__
        self.name = agent_name
        #
        self.state: State = {}
        self.__actions: List[Action] = []

    def load_actions(self, actions: List[Action]):
        """
        Load actions list; refresh in case of any changes to the actions data.

        :param actions:List[Action]: List of actions.
        """

        self.__actions = actions
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

    def preempt(self):
        """
        Preempt execution.
        """

        self.__preempted = True

    def reset(self):
        """
        Resets the abort/preempt status back to False in the event abort was triggered.
        """

        self.__abort = False
        self.__preempted = False

    def is_goal_met(self, goal: State) -> bool:
        """
        Compares the desired goal state against the system state to check if it is already met.

        :param goal:State: Desired goal state
        :return:bool: True if goal state and current system state is same; False otherwise
        """

        if not goal:
            return True

        for k, v in goal.items():
            if k not in self.state or self.state[k] != v:
                return False

        return True

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

        try:
            return self.__planner.generate_plan(goal, start_state)
            #
        except PlanningFailedException as pfx:
            logging.error(f"PLANNING FAILED! {pfx}")
            return []

    def execute_plan(self, plan: List[Action]):
        """
        Execute a previously generated plan.

        :param plan:List[Action]: Dictionary of actions and their expected outcomes (State)
        """

        for action in plan:
            try:
                self.execute_action(action)

            except Exception as _ex:
                logging.error(f"{_ex}")
                raise

        logging.info(f"EXECUTION SUCCEDED!")

    def achieve_goal(self, goal: State, verbose: bool = False):
        """
        Creates a plan to satisfy the goal state; executes it action-by-action; re-evaluates the plan at each step;

        :param goal:State: Desired goal state
        :param verbose:bool: Print plan to console at each step, if True
        """

        blacklisted_actions: List[str] = []

        # state might have changed since the last step was executed
        while not self.is_goal_met(goal):

            try:
                # (re)generate the plan
                plan: List[Action] = self.__planner.generate_plan(goal, self.state, blacklisted_actions)
                if verbose:
                    self.print_plan_to_console(plan)
                # execute one plan step at a time
                first_action = plan[0]
                self.execute_action(first_action)

                # if the latest executed action has the same effect as any of the blacklisted actions,
                # then it is prudent(?) to remove such a blacklisted action
                ba: List[Action] = [a for a in self.__actions if str(a) in blacklisted_actions]
                for action in ba:
                    if set(first_action.effects.keys()) <= set(action.effects.keys()):
                        blacklisted_actions.remove(str(action))

            except ActionFailedException as ex_fail:
                logging.error(f"{ex_fail} / ATTEMPTING ALTERNATIVE PLAN")
                __action_name = str(first_action)
                if __action_name not in blacklisted_actions:
                    blacklisted_actions.append(__action_name)
                continue

            except Exception as _ex:
                logging.error(f"{_ex}")
                raise

        logging.info(f"EXECUTION SUCCEDED!")

    def plan_and_execute(self, goal: State, verbose: bool = False) -> Iterable:
        """
        Creates a plan to satisfy the goal state; executes it action-by-action; re-evaluates the plan at each step;

        :param goal:State: Desired goal state
        :param verbose:bool: if True, prints formatted plan to console at each step
        """

        blacklisted_actions: List[str] = []

        # state might have changed since the last step was executed
        while not self.is_goal_met(goal):

            try:
                # (re)generate the plan
                plan: List[Action] = self.__planner.generate_plan(goal, self.state, blacklisted_actions)
                # print formatted plan to console
                if verbose:
                    self.print_plan_to_console(plan)

                yield plan  # yields plan before execution

                # execute one plan step at a time
                first_action = plan[0]
                self.execute_action(first_action)
                #
                # if the latest executed action has the same effect as any of the blacklisted actions,
                # then it is prudent(?) to remove such a blacklisted action
                ba: List[Action] = [a for a in self.__actions if str(a) in blacklisted_actions]
                for action in ba:
                    if set(first_action.effects.keys()) <= set(action.effects.keys()):
                        blacklisted_actions.remove(str(action))

            except ActionFailedException as ex_fail:
                logging.error(f"{ex_fail} / ATTEMPTING ALTERNATIVE PLAN")
                if str(first_action) not in blacklisted_actions:
                    blacklisted_actions.append(str(first_action))
                continue

            except ActionPreemptedException as _ex_preempted:
                # logging.info(f"{ex_preempted}")
                self.__preempted = False  # reset preempted status
                break

            except Exception as _ex:
                logging.error(f"{_ex}")
                raise

        logging.info(f"EXECUTION SUCCEDED!")

    def print_plan_to_console(self, plan: List[Action]):
        if plan:
            plan_str = '\nPLAN:\n'
            for ix, action in enumerate(plan):
                plan_str += "----- "*(ix+1) + str(action) + ' -- ' + str(action.effects) + '\n'
            print(plan_str)

    def execute_action(self, action: Action):
        # Check for abort status
        if self.__abort:
            # logging.error(f'ACTION: {action} : EXECUTION ABORTED BEFORE START !!')
            action.on_aborted(action.effects)
            raise ActionAbortedException(f'ACTION: {action} FAILED. ABORTED STATE IS ACTIVE!!')

        # Check for preempt status
        if self.__preempted:
            # logging.error(f'ACTION: {action} : EXECUTION PREEMPTED BEFORE START !!')
            action.on_preempted(action.effects)
            raise ActionPreemptedException(f'EXECUTION PREEMPTED WHILE AT ACTION: {action}')

        # Check runtime precondition
        if not action.check_runtime_precondition(action.effects):
            raise ActionFailedException(f'ACTION: {action} RUNTIME PRECONDITION CHECK FAILED!!.')

        # Execute the plan step
        action._execute(action.effects)
        # action.execute is an async process inside _execute,

        if action.allow_async:
            # if this is an async action; just apply the effects and return
            action.apply_effects(action.effects, self.state)
            return

        # monitor the status; wait until execution is complete
        time0 = time()
        while action.is_running():
            if self.__abort:
                # if an abort was signalled
                logging.critical(f'ACTION: {action} : EXECUTION ABORTED!!')
                action.status = ActionStatus.ABORTED
                break
            if time()-time0 > action.timeout:
                # Action timeout exceeded
                raise ActionTimedOutException(f'ACTION: {action} : TIMED OUT!!')
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
            logging.warning(f'ACTION: {action} STATUS UNKNOWN; ASSUMING FAILURE!!')

        # Execution completed with NEUTRAL Status
        if action.status == ActionStatus.NEUTRAL:
            # this is when action completes with no change to the state
            # logging.debug(f'ACTION: {action} Action completed with neutral state.')
            action.on_neutral(action.effects)  # ignore effects

        # Execution completed with SUCCESS Status
        if action.status == ActionStatus.SUCCESS:
            # Action executed without errors;
            action.apply_effects(action.effects, self.state)
            # logging.debug(f'ACTION: {action} Action succeded.')
            action.on_success(action.effects)

        # Execution failed
        if action.status == ActionStatus.FAILURE:
            action.on_failure(action.effects)
            # Stop execution as action failed
            raise ActionFailedException(f'ACTION: {action} FAILED!')

        # Execution aborted
        if action.status == ActionStatus.ABORTED:
            action.on_aborted(action.effects)
            # Stop execution as action aborted
            raise ActionAbortedException(f'ACTION: {action} ABORTED!')

        # Any clean up needed after execution e.g. updating system states
        action.on_exit(action.effects)
