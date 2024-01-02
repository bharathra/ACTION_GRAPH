#! /usr/bin/env python3

from time import sleep, time
from typing import Iterable, List

from action_graph.action import (Action, ActionStatus, State)
from action_graph.planner import Planner, PlanningFailedException


class Agent:
    """Autonomous agent to monitor system state, keep track of feasible actions, 
    generate plans and achive desired goals"""

    __planner: Planner = Planner([])
    __abort: bool = False

    def __init__(self, agent_name=None) -> None:
        if not agent_name:
            agent_name = self.__class__.__name__
        self.name = agent_name
        #
        self.state: State = {}
        self.__actions: List[Action] = []
        self.__completed_actions_stack: List[Action] = []

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

            except Exception as _ex:
                print(f"[Agent] Execution failed! {_ex}")
                raise

        self.__completed_actions_stack.clear()
        print(f"[Agent] Execution succeeded!")

    def print_plan_to_console(self, plan: List[Action]):
        if plan:
            plan_str = '\nPLAN:\n'
            for ix, action in enumerate(plan):
                plan_str += str(ix+1).zfill(2) + ' ' + \
                    str(action) + (25-len(str(action)))*'.' + \
                    str(action.effects) + '\n'
            print(plan_str)

    def execute_action(self, action: Action) -> ActionStatus:

        # Check runtime precondition
        if not action.check_runtime_precondition():
            print(f'[Agent] Action: {action} / Runtime pre-condition check failed!')
            return ActionStatus.FAILURE

        # Execute the plan step
        action._execute()
        # action.execute is an async process inside _execute,

        if action.allow_async:
            # if this is an async action; just apply the effects and return
            action.apply_effects(self.state)
            return

        # monitor the status; wait until execution is complete
        time0 = time()
        while action.is_running():
            if self.__abort:
                # if an abort was signalled
                action.abort()
                # print(f'[Agent] Action: {action} / Execution aborted!!')
                action.status = ActionStatus.FAILURE
                break
            if time()-time0 > action.timeout:
                # Action timeout exceeded
                raise Exception(f'[Agent] Action: {action} : Timed out!')
            if not action.status == ActionStatus.RUNNING:
                # thread is alive but the status has changed
                break  # so move on
            sleep(0.05)  # throttle loop
            # print(f'[Agent] Action: {str(action)} is running...')

        # Execution completed but with RUNNING Status
        if action.status == ActionStatus.RUNNING:
            # the user forgot to set the status; or something bad happened;
            # let's treat this as FAILURE!
            action.status = ActionStatus.FAILURE
            print(f'[Agent] Action: {action} / Status unknown; Assuming failure!')

        # Execution completed with NEUTRAL Status
        if action.status == ActionStatus.NEUTRAL:
            # this is when action completes with no change to the state
            # print(f'[Agent] Action: {action} / Action completed with neutral state.')
            action.on_neutral()  # ignore effects

        # Execution completed with SUCCESS Status
        if action.status == ActionStatus.SUCCESS:
            # Action executed without errors;
            action.apply_effects(self.state)
            # print(f'[Agent] Action: {action} / Action succeded.')
            action.on_success()

        # Execution failed
        if action.status == ActionStatus.FAILURE:
            action.on_failure()
            self.undo_completed_actions()

        # Any clean up needed after execution e.g. updating system states
        action.on_exit()

        return action.status
