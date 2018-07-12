# This file is part of the three2six project
# https://github.com/mbarkhau/three2six
# (C) 2018 Manuel Barkhau <mbarkhau@gmail.com>
#
# SPDX-License-Identifier:    MIT
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


CACHE_DIR = pl.Path(tempfile.gettempdir()) / ".three2six_cache"


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


def normalize_package_dir(
    packages: typ.List[str],
    package_dir: common.PackageDir=None,
) -> common.PackageDir:
    if package_dir is not None:
        return {
            package: package_dir.get(
                package,
                str(pl.Path(package_dir[""], package)),
            )
            for package in packages
        }

    norm_package_dir: common.PackageDir = {}
    for path in sys.path:
        if path.startswith(ENV_PATH):
            continue
        for package in packages:
            module_path = pl.Path(path) / package / "__init__.py"
            if module_path.exists():
                existing_package_path = norm_package_dir.get(package)
                if existing_package_path is None:
                    norm_package_dir[package] = str(pl.Path(path) / package)
                else:
                    raise common.InvalidPackage((
                        "Ambiguous package structure. "
                        "Multiple paths for package '{}': {} {}"
                    ).format(package, module_path, existing_package_path))

    return norm_package_dir


def init_build_package_dir(norm_package_dir: common.PackageDir) -> common.PackageDir:
    tmp_prefix = "three2six_"
    tmp_build_dir = pl.Path(tempfile.mkdtemp(prefix=tmp_prefix))

    build_package_dir: common.PackageDir = {}
    for package, src_package_dir in norm_package_dir.items():
        tmp_build_package_dir = str(tmp_build_dir / package)

        shutil.copytree(src_package_dir, tmp_build_package_dir)
        build_package_dir[package] = tmp_build_package_dir
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


def repackage(
    packages: typ.List[str],
    package_dir: common.PackageDir=None,
) -> typ.Tuple[typ.List[str], common.PackageDir]:

    norm_package_dir = normalize_package_dir(packages, package_dir)
    build_package_dir = init_build_package_dir(norm_package_dir)
    build_cfg = eval_build_config()
    build_packages(build_cfg, build_package_dir)
    return packages, build_package_dir
