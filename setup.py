#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import setuptools
from setuptools import setup, find_packages
from src import release

packagename = "runtime-container"

# consider the path of `setup.py` as root directory:
PROJECTROOT = os.path.dirname(sys.argv[0]) or "."
#release_path = os.path.join(PROJECTROOT, "src", "runtime-main", "release.py")
#with open(release_path, encoding="utf8") as release_file:
#    __version__ = release_file.read().split('__version__ = "', 1)[1].split('"', 1)[0]


with open("requirements.txt") as requirements_file:
    requirements = requirements_file.read()

setup(
    name=packagename,
    version=release.__version__,
    author=release.__author__,
    author_email=release.__author__,
    packages=find_packages("src"),
    package_dir={"": "src"},
    # url="https://codeberg.org/username/reponame",
    license=release.__license__,
    description=release.__description__,
    long_description="""
    ...
    """,
    install_requires=requirements,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: BSD 3-Clause License",
        "Programming Language :: Python :: 3",
    ],
    #entry_points={"console_scripts": [f"{packagename}={packagename}.script:main"]},
)
