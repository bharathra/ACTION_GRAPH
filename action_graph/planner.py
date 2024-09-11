#! /usr/bin/env python3

import sys
from collections import defaultdict
from typing import Any, Dict, List, Tuple

from action_graph.action import Action, State, ImpossibleAction


class PlanningFailedException(Exception):
    pass


class Planner():
    """Search and determine a plan (sequence of actions) that satifies a desired goal state"""

    def update_actions(self, actions: List[Action]):
        """
        The refereshes/reloads the list of Actions available to the Planner.

        :param actions:List[Action]: List of actions (instances of Action class)
        """

        self._action_lookup: defaultdict = self.__create_action_lookup(actions)

    def generate_plan(self, target_state: State, start_state: State, avoid_actions: List[Action] = None) -> List[Action]:
        """
        Generate a plan to achieve the desired goal state.

        :param target_state:State: Desired goal state
        :param start_state:State: Current system state
        :param avoid_actions:List[Action]: List of actions to avoid
        :return:List[Action]: List of actions to achieve the desired goal state
        """

        if len(target_state.items()) > 1:
            raise PlanningFailedException(f'target_state [{target_state}] should be a single state')
        tk, tv = list(target_state.items())[0]
        # in case target state value is a reference to another state variable
        tv = self.__parse_references(tv, start_state, '@')
        # check if the target state is already satisfied
        if (tk, tv) in list(start_state.items()):
            return []   # goal already met, move on
        #
        # find action(s) that satisfy the state current effect-item
        probable_actions: List[Action] = self._action_lookup[(tk, tv)]
        if not probable_actions:  # if no actions are found, try with templated actions
            probable_actions = self._action_lookup[(tk, Ellipsis)]
        if avoid_actions:  # actions we do not want to consider for planning
            probable_actions = [a for a in probable_actions if str(a) not in avoid_actions]
        if not probable_actions:
            return [ImpossibleAction(effects={tk: tv})]

        chosen_path: List[Action] = []
        for p_action in probable_actions:  # explore each available action...
            action = p_action.__copy__()
            if action.effects[tk] is Ellipsis:
                action.effects[tk] = tv  # apply variable effects
            #
            action_path: List[Action] = []
            for pk, pv in action.preconditions.items():  # for each pre-condition ...
                try:  # choose the shortest feasible path
                    pv = self.__parse_references(pv, action.effects, '$')
                    action_path.extend(self.generate_plan({pk: pv}, start_state, avoid_actions))  # merge the actions
                except RecursionError:  # watch out for cyclic references
                    raise PlanningFailedException(f'Found cyclic references! {pk}:{pv}')
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
        impossible_actions = [a for a in chosen_path if a.cost >= sys.float_info.max]
        for ia in impossible_actions:
            raise PlanningFailedException(f'No action available to satisfy: {ia.effects}')

        return chosen_path

    def __create_action_lookup(self, actions: List[Action]) -> Dict[Tuple[Any, Any], List[Action]]:
        action_lookup: Dict[Tuple[Any, Any], List[Action]] = defaultdict(list)
        for action in actions:
            for k, v in action.effects.items():
                action_lookup[(k, v)].append(action)
        return action_lookup

    def __parse_references(self, ref: Any, state: State, prefix: str) -> Any:
        if isinstance(ref, str) and '/' in ref:
            return '/'.join([self.__parse_references(r, state, prefix) for r in ref.split('/')])
        while ref and isinstance(ref, str) and ref[0] == prefix and ref[1:] in state:
            ref = state[ref[1:]]
        return ref

    def __make_unique(self, path):
        unique = set()
        return [x for x in path if x not in unique and not unique.add(x)]
