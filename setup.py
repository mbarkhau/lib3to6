# This file is part of the lib3to6 project
# https://github.com/mbarkhau/lib3to6
#
# (C) 2018 Manuel Barkhau (@mbarkhau)
# SPDX-License-Identifier: MIT

import os
import sys
import setuptools
import pkg_resources


def project_path(*sub_paths):
    project_dirpath = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(project_dirpath, *sub_paths)


def read(filename):
    with open(project_path(filename), mode="rb") as fh:
        return fh.read().decode("utf-8")


packages = setuptools.find_packages(project_path("src"))
package_dir = {"": "src"}


if any(arg.startswith("bdist") for arg in sys.argv):
    try:
        import lib3to6
        package_dir = lib3to6.fix(package_dir)
    except ImportError as ex:
        if "lib3to6" in str(ex):
            print("WARNING: 'lib3to6' missing, package will not be universal")
        else:
            raise


__version__ = "v201809.0016-alpha"
__normalized_python_version__ = str(pkg_resources.parse_version(__version__))

long_description = (
    read("README.rst") +
    "\n\n" +
    read("CHANGELOG.rst")
)

setuptools.setup(
    name="lib3to6",
    license="MIT",
    author="Manuel Barkhau",
    author_email="mbarkhau@gmail.com",
    url="https://github.com/mbarkhau/lib3to6",
    version=__normalized_python_version__,

    description="Build universal python from a substantial subset of Python 3.7 syntax.",
    long_description=long_description,
    long_description_content_type="text/x-rst",

    packages=packages,
    package_dir=package_dir,
    install_requires=["astor", "pathlib2", "click", "typing"],
    zip_safe=True,
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
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
