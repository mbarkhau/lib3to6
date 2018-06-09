#!/usr/bin/env python
# This file is part of the three2six project
# https://github.com/mbarkhau/three2six
# (C) 2018 Manuel Barkhau <mbarkhau@gmail.com>
#
# SPDX-License-Identifier:    MIT

import sys
import setuptools


packages = ["test_module"]


if "bdist_wheel" in sys.argv:
    import three2six
    packages, package_dir = three2six.repackage(packages)


setuptools.setup(
    name="test-module",
    version="0.1.0",
    description="A python3.6 module built with three2six",
    author="Manuel Barkhau",
    author_email="mbarkhau@gmail.com",
    packages=packages,
    package_dir=package_dir,
    license="MIT",
    install_requires=["six", "pathlib2"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
