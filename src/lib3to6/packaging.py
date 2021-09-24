# This file is part of the lib3to6 project
# https://github.com/mbarkhau/lib3to6
#
# Copyright (c) 2019-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

import os
import re
import sys
import shutil
import typing as typ
import hashlib
import tempfile
import warnings

import pathlib2 as pl
import setuptools.dist
import setuptools.command.build_py as _build_py

from . import common
from . import transpile

ENV_PATH = str(pl.Path(sys.executable).parent.parent)


PYTHON_TAG_PREFIXES = {
    'py': "Generic Python",
    'cp': "CPython",
    'ip': "IronPython",
    'pp': "PyPy",
    'jy': "Jython",
}


CACHE_DIR = pl.Path(tempfile.gettempdir()) / ".lib3to6_cache"


def eval_build_config(**kwargs) -> common.BuildConfig:
    target_version    = kwargs.get('target_version', transpile.DEFAULT_TARGET_VERSION)
    _install_requires = kwargs.get('install_requires', None)
    cache_enabled     = kwargs.get('cache_enabled', True)
    default_mode      = kwargs.get('default_mode', 'enabled')

    install_requires: common.InstallRequires
    if _install_requires is None:
        install_requires = None
    elif isinstance(_install_requires, str):
        install_requires = set(_install_requires.split())
    elif isinstance(_install_requires, list):
        install_requires = set(_install_requires)
    else:
        raise TypeError(f"Invalid argument for install_requires: {type(_install_requires)}")

    if install_requires:
        # Remove version specs. We only handle the bare requirement
        # and assume the maintainer knows what they're doing wrt.
        # the appropriate versions.
        install_requires = {re.split(r"[\^\~<>=;]", req.strip())[0] for req in install_requires}

    return common.BuildConfig(
        target_version=target_version,
        cache_enabled=cache_enabled,
        default_mode=default_mode,
        fixers="",
        checkers="",
        install_requires=install_requires,
    )


def _ignore_tmp_files(src: str, names: typ.List[str]) -> typ.List[str]:
    if isinstance(src, str):
        src_str = src
    else:
        # https://bugs.python.org/issue39390
        if isinstance(src, os.DirEntry):
            src_str = src.path
        else:
            src_str = str(src)

    if src_str.startswith("build") or src_str.startswith("./build"):
        return names
    if src_str.endswith(".egg-info"):
        return names
    if src_str.endswith("dist"):
        return names
    if src_str.endswith("__pycache__"):
        return names

    return [name for name in names if name.endswith(".pyc")]


def init_build_package_dir(local_package_dir: common.PackageDir) -> common.PackageDir:
    output_dir = pl.Path("build") / "lib3to6_out"
    output_dir.mkdir(parents=True, exist_ok=True)

    build_package_dir: common.PackageDir = {}

    for package, src_package_dir in local_package_dir.items():
        is_abs_path = pl.Path(src_package_dir) == pl.Path(src_package_dir).absolute()
        if is_abs_path:
            raise Exception(f"package_dir must use relative paths, got '{src_package_dir}'")

        build_package_subdir = output_dir / src_package_dir

        # TODO (mb 2018-08-25): As an optimization, we could
        #   restrict deletion to files that we manipulate, in
        #   other words, to *.py files.
        if build_package_subdir.exists():
            shutil.rmtree(build_package_subdir)

        shutil.copytree(src_package_dir, str(build_package_subdir), ignore=_ignore_tmp_files)
        build_package_dir[package] = str(build_package_subdir)

    return build_package_dir


def transpile_path(cfg: common.BuildConfig, filepath: pl.Path) -> pl.Path:
    with open(filepath, mode="rb") as fobj:
        module_source_data = fobj.read()

    filehash = hashlib.sha1()
    filehash.update(str(cfg).encode("utf-8"))
    filehash.update(module_source_data)

    cache_path = CACHE_DIR / (filehash.hexdigest() + ".py")

    if cfg.cache_enabled and cache_path.exists():
        return cache_path

    # NOTE (mb 2020-09-01): not cache_enabled -> always update cache
    ctx = common.BuildContext(cfg, str(filepath))
    try:
        fixed_module_source_data = transpile.transpile_module_data(ctx, module_source_data)
    except common.CheckError as err:
        loc = str(filepath)
        if err.lineno >= 0:
            loc += "@" + str(err.lineno)

        err.args = (loc + " - " + err.args[0],) + err.args[1:]
        raise

    with open(cache_path, mode="wb") as fobj:
        fobj.write(fixed_module_source_data)

    return cache_path


def build_package(cfg: common.BuildConfig, package: str, build_dir: str) -> None:
    # pylint:disable=unused-argument ; `package` is part of the public api now
    for root, _dirs, files in os.walk(build_dir):
        for filename in files:
            filepath = pl.Path(root) / filename
            if filepath.suffix == ".py":
                transpiled_path = transpile_path(cfg, filepath)
                # overwrite original with transpiled
                shutil.copy(transpiled_path, filepath)


def build_packages(cfg: common.BuildConfig, build_package_dir: common.PackageDir) -> None:
    CACHE_DIR.mkdir(exist_ok=True)

    for package, build_dir in build_package_dir.items():
        build_package(cfg, package, build_dir)


def fix(
    package_dir     : common.PackageDir = None,
    target_version  : str = transpile.DEFAULT_TARGET_VERSION,
    install_requires: typ.List[str] = None,
    default_mode    : str = 'enabled',
) -> common.PackageDir:
    msg = "Depricated: lib3to6.fix(). See https://github.com/mbarkhau/lib3to6#Deprications"
    warnings.warn(msg, DeprecationWarning)

    if package_dir is None:
        package_dir = {"": "."}

    build_package_dir = init_build_package_dir(package_dir)
    build_cfg         = eval_build_config(
        target_version=target_version,
        install_requires=install_requires,
        default_mode=default_mode,
    )
    build_packages(build_cfg, build_package_dir)
    return build_package_dir


class build_py(_build_py.build_py):
    # pylint: disable=invalid-name      ; following the convention of setuptools

    def run_3to6(self) -> None:
        outputs = _build_py.orig.build_py.get_outputs(self, include_bytecode=0)
        dist    = self.distribution
        pyreq   = dist.python_requires

        preq_match = isinstance(pyreq, str) and re.match(r">=([0-9]+\.[0-9]+)", pyreq)
        if preq_match:
            target_version = preq_match.group(1)
        else:
            raise ValueError('lib3to6: missing python_requires=">=X.Y" in setup.py')

        # pylint: disable=protected-access
        install_requires = sorted(dist._lib3to6_install_requires)
        build_cfg        = eval_build_config(
            target_version=target_version,
            install_requires=install_requires,
            default_mode=getattr(dist, 'lib3to6_default_mode', 'enabled'),
        )

        CACHE_DIR.mkdir(exist_ok=True)
        for output in outputs:
            if output.endswith(".py"):
                transpiled_path = transpile_path(build_cfg, pl.Path(output))
                shutil.copy(transpiled_path, output)

    def run(self) -> None:
        """Build modules, packages, and copy data files to build directory"""
        if not self.py_modules and not self.packages:
            return

        if self.py_modules:
            self.build_modules()

        if self.packages:
            self.build_packages()
            self.build_package_data()

        if hasattr(self, 'run_2to3'):
            self.run_2to3(self.__updated_files, False)
            self.run_2to3(self.__updated_files, True)
            self.run_2to3(self.__doctests_2to3, True)

        self.run_3to6()

        # Only compile actual .py files, using our base class' idea of what our
        # output files are.
        self.byte_compile(_build_py.orig.build_py.get_outputs(self, include_bytecode=0))


class Distribution(setuptools.dist.Distribution):
    def __init__(self, attrs=None):
        # NOTE (mb 2021-08-20): Distutils removes all requirements
        #   that are not needed for the current python version. We
        #   need the original requirements for validation, so we
        #   capture them here.
        self._lib3to6_install_requires = attrs.get('install_requires')
        super().__init__(attrs)

    def get_command_class(self, command):
        if command in self.cmdclass:
            return self.cmdclass[command]
        elif command == 'build_py':
            self.cmdclass[command] = build_py
            return build_py
        else:
            return super().get_command_class(command)
