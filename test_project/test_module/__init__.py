# This file is part of the lib3to6 project
# https://github.com/mbarkhau/lib3to6
#
# (C) 2018 Manuel Barkhau (@mbarkhau)
# SPDX-License-Identifier: MIT
"""A docstring."""

import typing

assert __doc__ == "A docstring."

x = [*[1, 2], 3]
(
    lambda l: l.extend([*[1, 2, *l, 4], 5])
)(x)
assert x == [1, 2, 3, 1, 2, 1, 2, 3, 4, 5]


class Foo:

    @classmethod
    def foo(f: 'Foo') -> 'Foo':
        pass


res = ""
x = 10
while (x := x - 1) > 0:
    res += str(x)
    assert len(res) < 10

assert res == "987654321"


def test_unpacking_generalization(*args, **kwargs):
    return args, kwargs


a: typing.List[int] = [1, 2, 3]
b = [4, 5, 6]
x = {"x": 11}
z = {"z": 33}


args, kwargs = test_unpacking_generalization(0, *a, *b, 7, 8, **x, y=22, **z)
assert args == (0, 1, 2, 3, 4, 5, 6, 7, 8)
assert kwargs == {"x": 11, "y": 22, "z": 33}


okfail = "ok"

print(f"all {okfail}")
