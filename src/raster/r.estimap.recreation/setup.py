#!/usr/bin/env python
import os
import sys

from setuptools import setup, find_packages

os.chdir(os.path.dirname(sys.argv[0]) or ".")

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="r.estimap.recreation",
    version="3",
    description="Implementation of ESTIMAP recreation as a GRASS GIS add-on",
    long_description=long_description,
    url="https://gitlab.com/natcapes/r.estimap.recreation",
    author="Nikos Alexandris",
    author_email="nik@nikosalexandris.net",
    # list of valid classifiers
    # https://pypi.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 3 - Beta",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "License :: EUPL v 1.2 :: GNU General Public License v3 or later (GPLv3+)",
    ],
    packages=find_packages(),
)
