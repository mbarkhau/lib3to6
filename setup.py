# This file is part of the lib3to6 project
# https://github.com/mbarkhau/lib3to6
#
# (C) 2018 Manuel Barkhau (@mbarkhau)
# SPDX-License-Identifier: MIT

import os
import setuptools
import pkg_resources


def project_path(*sub_paths):
    project_dirpath = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(project_dirpath, *sub_paths)


def read(filename):
    with open(project_path(filename), mode="rb") as fh:
        return fh.read().decode("utf-8")


packages = setuptools.find_packages(project_path("src"))
package_dir = {
    package_name: project_path("src", package_name)
    for package_name in packages
}

print("!!!", package_dir)

packages = setuptools.find_packages(project_path("src"))
package_dir = {"": project_path("src")}

# print("!!!", package_dir)

# for path in package_dir.values():
#     for root, dirnames, filenames in os.walk(path):
#         for dirname in dirnames:
#             print("##11d", root, dirname)
#         for filename in filenames:
#             if filename.endswith(".py"):
#                 print("##11f", root, filename, end=" ")
#                 with open(root + "/" + filename, mode="r") as fh:
#                     print(fh.readlines()[:2])

print(">>>", package_dir)

try:
    import lib3to6
    package_dir = lib3to6.fix(package_dir)
except ImportError as ex:
    if "lib3to6" in str(ex):
        print("WARNING: 'lib3to6' not available, distribution will be python 3.6+ only")
    else:
        raise

print("<<<", package_dir)

# for path in package_dir.values():
#     for root, dirnames, filenames in os.walk(path):
#         for dirname in dirnames:
#             print("##22d", root, dirname)
#         for filename in filenames:
#             if filename.endswith(".py"):
#                 print("##22f", root, filename, end=" ")
#                 with open(root + "/" + filename, mode="r") as fh:
#                     print(fh.readlines()[:2])


__version__ = "v201808.0014"
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
    install_requires=["astor", "pathlib2", "click"],
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
