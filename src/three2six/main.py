#!/usr/bin/env python
# This file is part of the three2six project
# https://github.com/mbarkhau/three2six
# (C) 2018 Manuel Barkhau <mbarkhau@gmail.com>
#
# SPDX-License-Identifier:    MIT

import sys


def main(argv=sys.argv[1:]):
    print(argv)
    print("TODO (mb 2018-06-07): allow conversion of individual files")
    print("TODO (mb 2018-06-07): option --in-place")


if __name__ == '__main__':
    sys.exit(main())
