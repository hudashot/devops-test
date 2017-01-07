#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='beacon',
      version='1.0.0',
      scripts=['bin/summarize-beacon'],
      packages=find_packages(),
      description="Get data from NIST Randomness Beacon",
      install_requires=["dateparser", "requests_toolbelt"],
      )
