#! /usr/bin/env python3

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
