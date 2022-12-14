#! /usr/bin/env python3

from copy import deepcopy
from enum import auto, Enum
from threading import Thread


class State(dict):

    def __hash__(self):
        return hash(tuple(frozenset(sorted(self.items()))))


class ActionStatus(Enum):
    FAILURE = auto()
    SUCCESS = auto()
    RUNNING = auto()
    ABORTED = auto()
    NEUTRAL = auto()


class Action():

    effects: State = {}
    preconditions: State = {}

    cost: float = 1.0
    status: ActionStatus = ActionStatus.SUCCESS
    timeout: float = 86_400.0  # 24 hours
    allow_async: bool = False

    def __init__(self, agent=None) -> None:
        self.agent = agent
        self.__exec_thread: Thread = Thread(target=self.on_execute, args=())

    def check_runtime_precondition(self, outcome: State) -> bool:
        return True

    def _execute(self, outcome: State):
        self.status = ActionStatus.RUNNING
        self.__exec_thread = Thread(target=self.on_execute, args=(outcome,))
        self.__exec_thread.start()

    def on_execute(self, outcome: State):
        # NOTE: Any overrides of this method has to explicitly set
        # the status either one of SUCCESS, FAILURE, ABORTED;
        # otherwise, status will be treated as FAILURE
        self.status = ActionStatus.SUCCESS

    def is_running(self):
        return self.__exec_thread.is_alive()

    def on_success(self, outcome: State = None):
        pass

    def on_failure(self, outcome: State = None):
        pass

    def on_aborted(self, outcome: State = None):
        pass

    def on_neutral(self, outcome: State = None):
        pass

    def on_exit(self, outcome: State = None):
        pass

    def apply_effects(self, outcome: State, state: State):
        # update the state with the predicted outcomes
        for k, v in self.effects.items():
            state[k] = v

    def __repr__(self) -> str:
        return self.__class__.__name__

    def __hash__(self):
        return hash(self.__class__.__name__)

    def __eq__(self, __o: object) -> bool:
        if self.__class__.__name__ == __o.__class__.__name__ and \
                self.cost == __o.cost and \
                self.effects == __o.effects and \
                self.preconditions == __o.preconditions:
            return True
        return False

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

    def on_execute(self, outcome: State):
        self.status = ActionStatus.ABORTED


class ActionFailedException(Exception):
    pass


class ActionAbortedException(Exception):
    pass


class ActionTimedOutException(Exception):
    pass
