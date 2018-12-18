# This file is part of the lib3to6 project
# https://gitlab.com/mbarkhau/lib3to6
#
# Copyright (c) 2018 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

import os
import sys
import setuptools


def project_path(*sub_paths):
    project_dirpath = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(project_dirpath, *sub_paths)


def read(*sub_paths):
    with open(project_path(*sub_paths), mode="rb") as fh:
        return fh.read().decode("utf-8")


install_requires = [
    line.strip()
    for line in read("requirements", "pypi.txt").splitlines()
    if line.strip() and not line.startswith("#")
]


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


long_description = (read("README.md") + "\n\n" + read("CHANGELOG.md"))


setuptools.setup(
    name="lib3to6",
    license="MIT",
    author="Manuel Barkhau",
    author_email="mbarkhau@gmail.com",
    url="https://gitlab.com/mbarkhau/lib3to6",
    version="201812.24b0",
    keywords="six lib2to3 astor ast",

    description="Build universal python from a substantial subset of Python 3.7.",
    long_description=long_description,
    long_description_content_type="text/markdown",

    packages=packages,
    package_dir=package_dir,
    python_requires=">=3.6",
    install_requires=install_requires,
    entry_points="""
        [console_scripts]
        lib3to6=lib3to6.__main__:main
    """,
    zip_safe=True,
    classifiers=[
        "Development Status :: 4 - Beta",
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
