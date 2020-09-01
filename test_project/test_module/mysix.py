# -*- coding: utf-8 -*-
# lib3to6: disabled

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys

try:
    import builtins
    # NOTE (mb 2017-11-03): the 'future' package creates
    #   this module but we don't want it.
    assert getattr(builtins, '__future_module__', None) is None
except (ImportError, AssertionError):
    import __builtin__ as builtins


PY3 = sys.version_info[0] == 3

if PY3:
    str_types = (builtins.bytes, builtins.str)
    str = builtins.str
    integer_types = int,
else:
    integer_types = (int, long)
    str_types = (builtins.str, builtins.unicode)
    str = builtins.unicode
