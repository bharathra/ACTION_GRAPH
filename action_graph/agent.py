#! /usr/bin/env python3

import time
from threading import Thread
from typing import Dict, Iterable, List, Tuple

from action_graph.action import (Action, ActionStatus, State)
from action_graph.planner import Planner, PlanningFailedException


class Agent:
    """Autonomous agent to monitor system state, keep track of feasible actions, 
    generate plans and achive desired goals"""

    __planner: Planner = Planner()
    __abort: bool = False

    def __init__(self, agent_name=None) -> None:
        if not agent_name:
            agent_name = self.__class__.__name__
        self.name = agent_name
        #
        self.state: State = {}
        self.__actions: List[Action] = []
        self.__completed_actions_stack: List[Action] = []
        self.__async_action_threads: Dict[str, Tuple[Thread, Action]] = {}

    def load_actions(self, actions: List[Action]):
        """
        Load actions list; refresh in case of any changes to the actions data.

        :param actions:List[Action]: List of actions.
        """

        self.__actions = actions
        self.__planner.update_actions(actions)

    def undo_completed_actions(self):
        """
        Undo previous executions (if possible).
        """

        while self.__completed_actions_stack:
            self.__completed_actions_stack.pop().undo()

    def reset(self):
        """
        Resets the abort/revoke status back to False in the event abort was triggered.
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

        for k, v in goal.items():
            if k not in self.state or self.state[k] != v:
                return False

        return True

    def get_plan(self, goal: State,
                 start_state: State = None,
                 actions: List[Action] = None) -> List[Action]:
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
            print(f"[Agent] Planning failed! {pfx}")
            return []

    def execute_plan(self, plan: List[Action]):
        """
        Execute a plan of actions.

        :param plan:List[Action]: List of actions to be executed.
        """

        for action in plan:
            self.execute_action(action)

    def plan_and_execute(self, goal: State, verbose: bool = False) -> Iterable:
        """
        Creates a plan to satisfy the goal state; executes it action-by-action; re-evaluates the plan at each step;

        :param goal:State: Desired goal state
        :param verbose:bool: if True, prints formatted plan to console at each step
        """

        blocked_actions: List[str] = []

        # state might have changed since the last step was executed
        while not self.is_goal_met(goal):

            try:
                # (re)generate the plan
                plan: List[Action] = self.__planner.generate_plan(goal, self.state, blocked_actions)
                # print formatted plan to console
                if verbose:
                    self.print_plan_to_console(plan)

                yield plan  # yields plan before execution

                # execute one plan step at a time
                first_action = plan[0]
                action_status = self.execute_action(first_action)
                #
                # if the latest executed action has the same effect as any of the blocked actions,
                # then it is prudent(?) to remove such a blocked action
                ba: List[Action] = [a for a in self.__actions if str(a) in blocked_actions]
                for action in ba:
                    if set(first_action.effects.keys()) <= set(action.effects.keys()):
                        blocked_actions.remove(str(action))

                if action_status == ActionStatus.FAILURE:
                    print(f"[Agent] Action failed! Attempting alternative plan.")
                    if str(first_action) not in blocked_actions:
                        blocked_actions.append(str(first_action))
                    continue

                self.__completed_actions_stack.append(first_action)

            except PlanningFailedException as pfx:
                print(f"[Agent] Planning failed! {pfx}")
                print(f"[Agent] Will attempt to undo previous actions")
                self.undo_actions(self.__completed_actions_stack)
                return

            except Exception as _ex:
                print(f"[Agent] Execution failed! {_ex}")
                raise

        # for those actions that require auto-reset,
        # reset their effects to the prior state
        for action in self.__completed_actions_stack:
            if action.auto_reset:
                action.reset_effects(self.state)

        self.__completed_actions_stack.clear()
        print(f"[Agent] Execution succeeded!")

    def print_plan_to_console(self, plan: List[Action]):
        """
        Print the plan to console in a formatted manner.

        :param plan:List[Action]: List of actions in the plan
        """

        if plan:
            plan_str = '\nPLAN:\n'
            for ix, action in enumerate(plan):
                plan_str += str(ix+1).zfill(2) + ' ' + \
                    str(action) + (25-len(str(action)))*'.' + \
                    str(action.effects) + '\n'
            print(plan_str)

    def execute_action(self, action: Action) -> ActionStatus:
        """
        Execute an action and monitor its status.

        :param action:Action: Action to be executed
        :return:ActionStatus: Status of the action execution
        """

        # if this action is dependent on another action that is still running,
        # then wait for the dependent action to complete
        for k in action.preconditions.keys():
            if k not in self.__async_action_threads.keys():
                continue
            # wait for the dependent action to complete
            self.__async_action_threads[k][0].join()
            predecessor_action = self.__async_action_threads[k][1]
            if predecessor_action.status == ActionStatus.FAILURE:
                # raise PlanningFailedException(f'[Agent] Action: {action} : Dependency ({predecessor_action}) failed!')
                predecessor_action.reset_effects(self.state)
                if predecessor_action in self.__actions:
                    # print(f"Removing effects of {predecessor_action}")
                    predecessor_action.reset_effects(self.state)
                    self.__actions.remove(predecessor_action)
                    self.__planner.update_actions(self.__actions)
                return ActionStatus.NEUTRAL
            self.__async_action_threads.pop(k)

        # execute the action in a separate thread irrespective of the async_exec flag
        _exec_thread = Thread(target=action._execute)
        _exec_thread.start()

        # if the action is set to execute asynchronously
        if action.async_exec:
            for k in action.effects.keys():
                self.__async_action_threads[k] = (_exec_thread, action)
                # print(f'[Agent] Action: {action} / Executing asynchronously...')
                action.apply_effects(self.state)
            return ActionStatus.NEUTRAL

        # monitor the status; wait until execution is complete
        time0 = time.time()
        while _exec_thread.is_alive():
            if self.__abort:
                action.abort()
                # print(f'[Agent] Action: {action} / Execution aborted!!')
                action.status = ActionStatus.FAILURE
                break
            if time.time()-time0 > action.timeout:
                raise Exception(f'[Agent] Action: {action} : Timed out!')
                #
            time.sleep(0.01)  # throttle loop
            # print(f'[Agent] Action: {str(action)} is running...')

        return action.status

    def undo_actions(self, completed_actions: List[Action]):
        """
        Undo the effects of an action.
        """

        for action in completed_actions[::-1]:
            action.undo()
