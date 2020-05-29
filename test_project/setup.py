# This file is part of the lib3to6 project
# https://github.com/mbarkhau/lib3to6
#
# (C) 2018 Manuel Barkhau (@mbarkhau)
# SPDX-License-Identifier: MIT

import sys
import setuptools
import pkg_resources


packages = ["test_module"]
package_dir = {"": "."}

install_requires = ['typing;python_version<"3.5"']

if any(arg.startswith("bdist") for arg in sys.argv):
    import lib3to6
    package_dir = lib3to6.fix(
        package_dir,
        target_version="2.7",
        install_requires=install_requires,
    )

__version__ = "v201808.1001"
__normalized_python_version__ = str(pkg_resources.parse_version(__version__))

setuptools.setup(
    name="test-module",
    version=__normalized_python_version__,
    description="A python3.7 module built with lib3to6",
    author="Manuel Barkhau",
    author_email="mbarkhau@gmail.com",
    packages=packages,
    package_dir=package_dir,
    install_requires=install_requires,
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production",
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
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
