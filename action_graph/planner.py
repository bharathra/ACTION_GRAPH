#! /usr/bin/env python3

import sys
from collections import defaultdict
from typing import Any, Dict, List, Tuple

from action_graph.action import Action, State, ImpossibleAction


class PlanningFailedException(Exception):
    pass


class Planner():
    """Search and determine a plan (sequence of actions) that satifies a desired goal state"""

    def __init__(self, actions: List[Action]) -> None:
        self.update_actions(actions)

    def update_actions(self, actions: List[Action]):
        """
        The refereshes/reloads the list of Actions available to the Planner.

        :param actions:List[Action]: List of actions (instances of Action class)
        """

        self._action_lookup: defaultdict = self.__create_action_lookup(actions)

    def generate_plan(self, target_state: State, start_state: State) -> List[Action]:
        """
        Find and return an optimal sequence of actions (the plan) that will 
        lead from the start state to the target state.

        :param target_state:State: Desired goal (target) state
        :param start_state:State: Current/start state of the system
        :return:List[Action]: List of actions updated with their expected outcomes (effects)
        """

        if len(target_state.items()) > 1:
            raise PlanningFailedException('target_state should have a single state variable')
        tk, tv = list(target_state.items())[0]
        # in case target state value is a reference to another state variable
        tv = self.__parse_references(tv, start_state)
        # check if the target state is already satisfied
        if (tk, tv) in list(start_state.items()):
            return []   # goal already met, move on
        #
        # find action(s) that satisfy the state current effect-item
        probable_actions: List[Action] = self._action_lookup[(tk, tv)]
        # if no actions are found, try with templated actions
        if not probable_actions:
            probable_actions = self._action_lookup[(tk, Ellipsis)]
            if not probable_actions:
                return [ImpossibleAction({tk: tv}).action]

        chosen_path: List[Action] = []
        for p_action in probable_actions:  # explore each available action...
            action = p_action.__copy__()
            if action.effects[tk] is Ellipsis:
                action.effects[tk] = tv  # apply variable effects
            #
            action_path: List[Action] = []
            for pk, pv in action.preconditions.items():
                try:
                    # for each pre-condition choose the shortest feasible path
                    pv = self.__parse_references(pv, action.effects)
                    action_path += self.generate_plan({pk: pv}, start_state)  # merge the actions
                except RecursionError:  # watch out for cyclic references
                    raise PlanningFailedException(f'Found cyclic references!')
            # include the current action;  remove duplicates; keep the order intact
            action_path = self.__make_unique(action_path + [action])
            #
            if not chosen_path:  # if no other path is available...
                chosen_path = action_path  # use the current path
                continue
            # if alternative paths exist, use the one with the lowest cost
            if sum(a.cost for a in action_path) < sum(a.cost for a in chosen_path):
                chosen_path = action_path

        # check if path is feasible; path cost should be < infinite cost
        impossible_actions = [a for a in chosen_path if a.cost > sys.float_info.max]
        for ia in impossible_actions:
            raise PlanningFailedException(f'No action available to satisfy: {ia.effects}')
        return chosen_path

    def __create_action_lookup(self, actions: List[Action]) -> Dict[Tuple[Any, Any], List[Action]]:
        action_lookup: Dict[Tuple[Any, Any], List[Action]] = defaultdict(list)
        for action in actions:
            for k, v in action.effects.items():
                action_lookup[(k, v)].append(action)
        return action_lookup

    def __parse_references(self, ref: Any, state: State) -> Any:
        if isinstance(ref, str) and ref[0] == '$':
            if ref[1:] in state:
                return state[ref[1:]]
        return ref

    def __make_unique(self, path):
        unique = set()
        return [x for x in path if x not in unique and not unique.add(x)]
