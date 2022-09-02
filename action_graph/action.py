#! /usr/bin/env python3

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


class Action():

    effects: State = {}
    preconditions: State = {}

    cost: float = 1.0
    status: ActionStatus = ActionStatus.SUCCESS

    def __init__(self, agent=None) -> None:
        self.agent = agent
        self.__exec_thread: Thread = Thread(target=self.on_execute, args=())

    def check_runtime_precondition(self, expected_outcome: State) -> bool:
        return True

    def _execute(self, expected_outcome: State):
        self.status = ActionStatus.RUNNING
        self.__exec_thread = Thread(target=self.on_execute, args=(expected_outcome,))
        self.__exec_thread.start()

    def on_execute(self, expected_outcome: State):
        # NOTE: Any overrides of this method has to explicitly set
        # the status either one of SUCCESS, FAILURE, ABORTED;
        # otherwise, status will be treated as FAILURE
        self.status = ActionStatus.SUCCESS

    def is_running(self):
        return self.__exec_thread.is_alive()

    def on_success(self, expected_outcome: State = None):
        pass

    def on_failure(self, expected_outcome: State = None):
        pass

    def on_aborted(self, expected_outcome: State = None):
        pass

    def on_exit(self, expected_outcome: State = None):
        pass

    def __repr__(self) -> str:
        return self.__class__.__name__

    def __hash__(self):
        return hash(self.__class__.__name__)


class ImpossibleAction():

    action = Action()

    def __init__(self, effects: State) -> None:
        self.action.cost = float('inf')
        self.action.effects = effects
