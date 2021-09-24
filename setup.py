# This file is part of the lib3to6 project
# https://github.com/mbarkhau/lib3to6
#
# Copyright (c) 2019-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

import os
import sys
import setuptools


def project_path(*sub_paths):
    project_dirpath = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(project_dirpath, *sub_paths)


def read(*sub_paths):
    with open(project_path(*sub_paths), mode="rb") as fobj:
        return fobj.read().decode("utf-8")


install_requires = [
    line.strip()
    for line in read("requirements", "pypi.txt").splitlines()
    if line.strip() and not line.startswith("#")
]


try:
    import lib3to6
    distclass = lib3to6.Distribution
except ImportError:
    distclass = setuptools.dist.Distribution


long_description = (read("README.md") + "\n\n" + read("CHANGELOG.md"))

setuptools.setup(
    name="lib3to6",
    license="MIT",
    author="Manuel Barkhau",
    author_email="mbarkhau@gmail.com",
    url="https://github.com/mbarkhau/lib3to6",
    version="202109.1049b0",
    keywords="six lib2to3 astor ast",
    description="Compile Python 3.6+ code to Python 2.7+",
    long_description=long_description,
    long_description_content_type="text/markdown",

    distclass=distclass,
    packages=setuptools.find_packages("src/"),
    package_dir={"": "src"},
    install_requires=install_requires,
    python_requires=">=3.6",
    zip_safe=True,

    entry_points={
        'console_scripts': ["lib3to6 = lib3to6.__main__:main"],
        # NOTE (mb 2021-08-20): Not sure how to prioritze these
        # 'distutils.commands': ["build_py = lib3to6:build_py"],
    },
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
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
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
