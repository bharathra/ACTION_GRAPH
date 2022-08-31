#! /usr/bin/env python3

from enum import auto, Enum
from threading import Thread
from typing import ClassVar, Dict, Any


State = Dict[Any, Any]


class ActionStatus(Enum):
    FAILURE = auto()
    SUCCESS = auto()
    RUNNING = auto()
    ABORTED = auto()


class Action():
    effects: ClassVar[State] = {}
    preconditions: ClassVar[State] = {}

    cost: float = 1.0
    status: ActionStatus = ActionStatus.SUCCESS

    def __init__(self, agent=None) -> None:
        self.agent = agent
        self.__exec_thread: Thread = Thread(target=self.on_execute, args=())

    def check_plan_precondition(self, outcome: State) -> bool:
        return True

    def check_runtime_precondition(self, outcome: State) -> bool:
        return True

    def pre_execution(self, outcome: State = None):
        pass

    def execute(self, outcome: State):
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

    def on_exit(self, outcome: State = None):
        pass

    def __repr__(self) -> str:
        return self.__class__.__name__

    def __hash__(self):
        return hash(self.__class__.__name__)
