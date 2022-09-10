# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from action_graph import name, __version__ as version

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name=name,
    version=version,
    packages=find_packages(),
    test_suite='tests',
    url='https://github.com/bharathra/action_graph',
    project_urls={
        "Bug Tracker": "https://github.com/bharathra/action_graph/issues",
    },
    license='MIT',
    author='Bharath Rao Achyutha',
    author_email='bharath.rao@hotmail.com',
    description='Autonomous agent for task/action planning and execution',
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires='>=3.7',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
)
