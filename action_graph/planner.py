#! /usr/bin/env python3

import sys
from collections import defaultdict
from typing import Any, Dict, List, Tuple

from action_graph.action import Action, State, ActionImpossible


class Planner():
    """Uses available actions and the current state of the system to 
    generate a plan of execution that satifies a desired goal state"""

    def __init__(self, actions: List[Action]) -> None:
        self.update_actions(actions)

    def update_actions(self, actions: List[Action]) -> None:
        """
        The refereshes/reloads the list of actions available to the planner.

        :param actions:List[Action]: List of actions (instances of Action class)
        :return: None
        """

        self._action_lookup: defaultdict = self.__create_action_lookup(actions)

    def generate_plan(self, target_state: State, start_state: State) -> List[Action]:
        """
        Find an optimal sequence of actions that will lead from the
        start state to the target state and return a list of actions (the plan).

        :param target_state:State: Desired goal (target) state
        :param start_state:State: Current/start state of the system
        :return:List[Action]: List of actions updated with their expected outcomes (effects)
        """

        gk, gv = list(target_state.items())[0]
        # in case target_state is reference to another state variable
        gv = self.__check_references(gv, start_state)
        # check if the target state is already satisfied
        if (gk, gv) in list(start_state.items()):
            return []   # goal already met, move on

        # find action(s) that satisfy the state current effect-item
        probable_actions: List[Action] = self._action_lookup[(gk, gv)]
        # if no actions are found, try with services
        if not probable_actions:
            probable_actions = self._action_lookup[(gk, Ellipsis)]
            if not probable_actions:
                return [ActionImpossible()]

        chosen_path: List[Action] = []
        # assuming more than one probable action is available to explore;
        for action in probable_actions:
            #             
            if action.effects[gk] is Ellipsis:
                action.effects[gk] = gv
            # explore each one ...
            action_path: List[Action] = []
            for pk, pv in action.preconditions.items():
                # for each pre-condition choose the shortest feasible path
                pv = self.__check_references(pv, action.effects)
                _path: List[Action] = self.generate_plan({pk: pv}, start_state)
                # merge the actions by removing duplicates and keeping the order intact
                action_path += _path
            # update the state with the current action's effects and
            action_path += [action]

            # choose the shortest feasible path
            if not chosen_path:
                chosen_path = action_path
            else:
                chosen_path_cost = sum(a.cost for a in chosen_path)
                action_path_cost = sum(a.cost for a in action_path)
                if action_path_cost < chosen_path_cost:
                    chosen_path = action_path

        # return the path, state, and cost at the end of this action
        if sum(a.cost for a in chosen_path) > sys.float_info.max:
            raise Exception(f'No action available to satisfy goal: {target_state}')
        return self.__unique(chosen_path)

    def __unique(self, path):
        unique = set()
        return [x for x in path if x not in unique and not unique.add(x)]

    def __create_action_lookup(self, actions: List[Action]) -> Dict[Tuple[Any, Any], Action]:
        lookup_actions: Dict[Tuple[Any, Any], Action] = defaultdict(list)
        for action in actions:
            for k, v in action.effects.items():
                lookup_actions[(k, v)].append(action)
        return lookup_actions

    def __check_references(self, ref: Any, state: State) -> Any:
        try:
            if isinstance(ref, str) and ref[0] == '$':
                if ref[1:] in state:
                    ref = state[ref[1:]]
        except:
            raise Exception(f'Error accessing referred state: {ref}!!')
        #
        return ref
