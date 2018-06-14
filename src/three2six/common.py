# This file is part of the three2six project
# https://github.com/mbarkhau/three2six
# (C) 2018 Manuel Barkhau <mbarkhau@gmail.com>
#
# SPDX-License-Identifier:    MIT

import typing as typ

PackageDir = typ.Dict[str, str]
BuildConfig = typ.Dict[str, str]


class InvalidPackage(Exception):
    pass


class CheckError(Exception):
    pass
