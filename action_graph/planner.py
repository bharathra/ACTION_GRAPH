#! /usr/bin/env python3

import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional, OrderedDict, Tuple

from action_graph.action import Action, State

Plan = OrderedDict[Action, State]


class Planner():
    """Uses available actions and the current state of the system to 
    generate a plan of execution that satifies a desired goal state"""

    def __init__(self, actions: List[Action]) -> None:
        self._action_lookup: defaultdict = self.__create_action_lookup(actions)
        self.__plan: Plan = {}
        self.__step_state: State = {}
        self.__services: State = {}

    def update_actions(self, actions: List[Action]) -> None:
        """
        The refereshes/reloads the list of actions available to the planner.

        :param actions:List[Action]: List of actions (instances of Action class)
        :return: None
        """

        self._action_lookup: defaultdict = self.__create_action_lookup(actions)

    def find_plan(self, start_state: State, target_state: State) -> Plan:
        """
        Find an optimal sequence of actions that will lead from the 
        start state to the target state and return a list of actions (the plan).

        :param start_state:State: Current/start state of the system
        :param target_state:State: Desired goal (target) state 
        :return:Plan: Ordered dictionary of actions and their predicted outcomes
        """

        self.__plan.clear()
        self.__step_state = start_state.copy()
        #
        try:
            self.__explore_actions(target_state)
            return self.__plan
        except Exception as _ex:
            logging.error(_ex)

    def __explore_actions(self, target_state: State):
        # DFS
        for gk, gv in target_state.items():
            if (gk, gv) in list(self.__step_state.items()):
                continue  # goal already met, move on
            #
            action: Action = self._action_lookup[(gk, gv)]
            if not action:
                action = self._action_lookup[(gk, Ellipsis)]
                if not action:
                    raise Exception(f'No action available to satisfy goal: {target_state}')
                self.__services[gk] = gv
            #
            for pk, pv in action.preconditions.items():
                pv = self.__check_references(pv)
                self.__explore_actions({pk: pv})
            #
            if action not in self.__plan:
                self.__plan[action] = {}
            self.__plan[action][gk] = gv
            self.__step_state[gk] = gv

    def __create_action_lookup(self, actions: List[Action]) -> Optional[Dict[Tuple[Any, Any], Action]]:
        lookup_actions: Dict[Tuple[Any, Any], Action] = defaultdict(list)
        for action in actions:
            for k, v in action.effects.items():
                if (k, v) in lookup_actions:
                    if action.cost > lookup_actions[(k, v)].cost:
                        continue
                lookup_actions[(k, v)] = action
            #
        return lookup_actions

    def __check_references(self, ref: Any) -> Any:
        try:
            if isinstance(ref, str):
                # while ref[1:] in self.__services:
                #     ref = self.__services[ref[1:]]
                # return ref
                if ref[1:] in self.__services:
                    return self.__services[ref[1:]]
                if ref[1:] in self.__step_state:
                    return self.__step_state[ref[1:]]
        except:
            raise Exception(f'Error accessing referred state: {ref}!!')
        #
        return ref
