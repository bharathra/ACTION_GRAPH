#! /usr/bin/env python3

from action_graph.action import Action, ActionStatus, State
from action_graph.agent import Agent

name = 'action_graph'
__version__ = '1.0.0'
__all__ = [
    'Action',
    'ActionStatus',
    'Agent',
    'State',
    'Planner',
    'name'
    '__version__',
]

# logging setup
import logging

console = logging.StreamHandler()
console.setLevel(logging.INFO)
#
formatter = logging.Formatter('>>>%(levelname)s > %(message)s')
console.setFormatter(formatter)
#
logging.getLogger('').addHandler(console)
logger = logging.getLogger(__name__)
