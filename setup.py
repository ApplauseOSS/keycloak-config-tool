#!/usr/bin/env python3

from distutils.core import setup
from keycloak_config import __program_name__
from keycloak_config import __version__
from setuptools import find_packages

import os

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, "README.md")).read()

install_requires = [
    "click==6.7",
    "requests==2.11.1",
    "kms-encryption-toolbox>=0.0.13"
]

setup(
    name=__program_name__,
    version=__version__,
    description="This package allows for configuration based updates to Keycloak.",
    long_description=README,
    long_description_content_type='text/markdown',
    classifiers=[
        # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Utilities",
        "Topic :: System :: Shells"
    ],
    keywords="keycloak",
    author="Applause Team",
    author_email="eng@applause.com",
    url="",
    license="MIT",
    packages=find_packages(),
    zip_safe=True,
    install_requires=install_requires,
    entry_points={
        "console_scripts":
            ["keycloak-config-tool=keycloak_config.__main__:main"]
    }
)
