# This file is part of the lib3to6 project
# https://github.com/mbarkhau/lib3to6
#
# (C) 2018 Manuel Barkhau (@mbarkhau)
# SPDX-License-Identifier: MIT

import os
import sys
import shutil
import tempfile
import typing as typ
import hashlib as hl
import pathlib2 as pl

from . import transpile
from . import common


ENV_PATH = str(pl.Path(sys.executable).parent.parent)


PYTHON_TAG_PREFIXES = {
    "py": "Generic Python",
    "cp": "CPython",
    "ip": "IronPython",
    "pp": "PyPy",
    "jy": "Jython",
}


CACHE_DIR = pl.Path(tempfile.gettempdir()) / ".lib3to6_cache"


def eval_build_config() -> common.BuildConfig:
    # TODO (mb 2018-06-07): Get options from setup.cfg
    # python_tags = "py2.py3"
    # for argi, arg in enumerate(sys.argv):
    #     if "--python-tag" in arg:
    #         if "=" in arg:
    #             python_tags = arg.split("=", 1)[-1]
    #         else:
    #             python_tags = sys.argv[argi + 1]

    return {
        "target_version"  : "2.7",
        "force_transpile" : "1",
        "fixers"          : "",
        "checkers"        : "",
    }


def _ingore_package_files(src: str, names: typ.List[str]) -> typ.List[str]:
    if src.endswith("__pycache__"):
        return names
    return [name for name in names if name.endswith(".pyc")]


def init_build_package_dir(
    packages: typ.List[str],
    local_package_dir: common.PackageDir
) -> common.PackageDir:
    tmp_prefix = "lib3to6_"
    tmp_build_dir = pl.Path(tempfile.mkdtemp(prefix=tmp_prefix))
    if "" in local_package_dir:
        root = local_package_dir[""]
    else:
        root = None

    build_package_dir: common.PackageDir = {}
    for package in packages:
        if package in local_package_dir:
            src_package_dir = local_package_dir[package]
        elif root:
            src_package_dir = pl.Path(root) / package
        else:
            raise Exception(f"Could not resolve source path of '{package}'")

    for package, src_package_dir in local_package_dir.items():
        tmp_build_package_dir = str(tmp_build_dir / package)

        shutil.copytree(
            src_package_dir,
            tmp_build_package_dir,
            ignore=_ingore_package_files,
        )

        build_package_dir[package] = tmp_build_package_dir

    # TODO (mb 2018-07-12): cleanup after build
    return build_package_dir


def build_package(cfg: common.BuildConfig, package: str, build_dir: str) -> None:
    for root, dirs, files in os.walk(build_dir):
        for filename in files:
            filepath = pl.Path(root) / filename
            if filepath.suffix != ".py":
                continue

            with open(filepath, mode="rb") as fh:
                module_source_data = fh.read()

            filehash = hl.sha1(module_source_data).hexdigest()
            cache_path = CACHE_DIR / (filehash + ".py")

            if int(cfg["force_transpile"]) or not cache_path.exists():
                fixed_module_source_data = transpile.transpile_module_data(cfg, module_source_data)
                with open(cache_path, mode="wb") as fh:
                    fh.write(fixed_module_source_data)

            shutil.copy(cache_path, filepath)


def build_packages(cfg: common.BuildConfig, build_package_dir: common.PackageDir) -> None:
    CACHE_DIR.mkdir(exist_ok=True)

    for package, build_dir in build_package_dir.items():
        build_package(cfg, package, build_dir)


def fix(package_dir: common.PackageDir) -> common.PackageDir:
    build_package_dir = init_build_package_dir(package_dir)
    build_cfg = eval_build_config()
    build_packages(build_cfg, build_package_dir)
    return build_package_dir
