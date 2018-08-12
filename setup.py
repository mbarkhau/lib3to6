# This file is part of the three2six project
# https://github.com/mbarkhau/three2six
# (C) 2018 Manuel Barkhau <mbarkhau@gmail.com>
#
# SPDX-License-Identifier:    MIT

import os
import sys
import setuptools


def path(filename):
    dirpath = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(dirpath, filename)


def read(filename):
    with open(path(filename), mode="rb") as fh:
        return fh.read().decode("utf-8")


packages = setuptools.find_packages(path("src"))
package_dir = {"": path("src")}


if "bdist_wheel" in sys.argv:
    import three2six
    packages, package_dir = three2six.repackage(packages, package_dir)


setuptools.setup(
    name="three2six",
    version="0.2.7",
    description="Build py2.7+ wheels from py3.6+ source",
    long_description=read("README.rst"),
    long_description_content_type="text/x-rst",
    author="Manuel Barkhau",
    author_email="mbarkhau@gmail.com",
    packages=packages,
    package_dir=package_dir,
    zip_safe=True,
    url="https://github.com/mbarkhau/three2six",
    license="MIT",
    entry_points={
        "console_scripts": [
            "three2six=three2six.main:main"
        ],
    },
    install_requires=["astor", "pathlib2", "click"],
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
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
