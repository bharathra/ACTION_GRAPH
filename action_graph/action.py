#! /usr/bin/env python3

from copy import deepcopy
from enum import auto, Enum
from threading import Thread


class State(dict):

    def __hash__(self):
        return hash(tuple(frozenset(sorted(self.items()))))


class ActionStatus(Enum):
    NEUTRAL = auto()
    RUNNING = auto()
    SUCCESS = auto()
    FAILURE = auto()


class Action():

    prior_state: State = {}
    effects: State = {}
    preconditions: State = {}

    cost: float = 1.0
    status: ActionStatus = ActionStatus.NEUTRAL
    timeout: float = 86_400.0  # 24 hours
    async_exec: bool = False
    auto_reset: bool = False

    def __init__(self, agent=None) -> None:
        self.agent = agent
        self._exec_thread: Thread = Thread(target=self.execute, args=())

    def check_runtime_precondition(self) -> bool:
        return True

    def _execute(self):
        self.status = ActionStatus.RUNNING
        self._exec_thread = Thread(target=self.execute)
        self._exec_thread.start()

    def execute(self):
        # NOTE: Any overrides of this method has to explicitly set
        # the status either one of SUCCESS, FAILURE, ABORTED;
        # otherwise, status will be treated as FAILURE
        self.status = ActionStatus.SUCCESS

    def is_running(self):
        return self._exec_thread.is_alive()

    def on_neutral(self):
        pass

    def on_success(self):
        pass

    def on_failure(self):
        pass

    def undo(self):
        pass

    def abort(self):
        pass

    def reset_effects(self, state: State):
        # restore the state to the prior state
        for k, v in self.prior_state.items():
            state[k] = v

    def on_exit(self):
        pass

    def apply_effects(self, state: State):
        # update the state with the effects of the action
        for k, v in self.effects.items():
            # backup the prior state
            self.prior_state[k] = state.get(k, Ellipsis)
            state[k] = v

    def __repr__(self) -> str:
        return self.__class__.__name__

    def __hash__(self):
        return hash(self.__class__.__name__)

    def __eq__(self, __o: object) -> bool:
        if self.__class__.__name__ == __o.__class__.__name__ and \
                self.cost == __o.cost and \
                self.__check_eq__(self.effects, __o.effects) and \
                self.preconditions == __o.preconditions:
            return True
        return False

    def __check_eq__(self, e1, e2):
        for k in e1.keys():
            if k not in e2.keys():
                return False
            if e1[k] != e2[k]:
                if Ellipsis not in [e1[k], e2[k]]:
                    return False
            #
        return True

    def __copy__(self):
        # instantiate an object of Action (or its sub-class) type
        a_copy = type(self)(self.agent)
        # shallow copy
        a_copy.cost = self.cost
        a_copy.status = self.status
        a_copy.timeout = self.timeout
        # deep copy
        memo = {id(self): a_copy}
        a_copy.effects = deepcopy(self.effects, memo)
        a_copy.preconditions = deepcopy(self.preconditions, memo)
        return a_copy


class ImpossibleAction(Action):
    cost = float('inf')

    def __init__(self, agent=None, effects=None) -> None:
        super().__init__(agent)
        if effects:
            self.effects = effects

    def execute(self):
        self.status = ActionStatus.FAILURE
