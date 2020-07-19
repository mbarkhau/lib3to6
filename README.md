# [lib3to6][repo_ref]

Compile Python 3.6+ code to Python 2.7+ compatible code. The idea is
quite similar to Babel https://babeljs.io/. Develop using the newest
interpreter and use (most) new language features without sacrificing
backward compatibility.

Project/Repo:

[![MIT License][license_img]][license_ref]
[![Supported Python Versions][pyversions_img]][pyversions_ref]
[![PyCalVer v202006.1041][version_img]][version_ref]
[![PyPI Version][pypi_img]][pypi_ref]
[![PyPI Downloads][downloads_img]][downloads_ref]

Code Quality/CI:

[![Build Status][build_img]][build_ref]
[![Type Checked with mypy][mypy_img]][mypy_ref]
[![Code Coverage][codecov_img]][codecov_ref]
[![Code Style: sjfmt][style_img]][style_ref]


|               Name                  |    role           |  since  | until |
|-------------------------------------|-------------------|---------|-------|
| Manuel Barkhau (mbarkhau@gmail.com) | author/maintainer | 2018-09 | -     |


<!--
  To update the TOC:
  $ pip install md-toc
  $ md_toc -i gitlab README.md -l 2
-->


[](TOC)

- [Project Status (as of 2020-05-29): Beta](#project-status-as-of-2020-05-29-beta)
- [Python Versions and Compatibility](#python-versions-and-compatibility)
- [Automatic Conversions](#automatic-conversions)
- [Projects that use lib3to6](#projects-that-use-lib3to6)
- [Motivation](#motivation)
- [How it works](#how-it-works)
- [Contributing](#contributing)
- [Future Work](#future-work)
- [Alternatives](#alternatives)
- [FAQ](#faq)


[](TOC)


## Project Status (as of 2020-05-29): Beta

I've been using this library for over a year on a few projects
without much incident. An example of such a project is
[PyCalVer](https://pypi.org/project/pycalver/). I have tested with
Python 3.8 and made some fixes and updates.

The library serves my purposes and I don't anticipate major updates,
but I will refrain from calling it stable until there has been more
adoption by projects other than my own.

Please give it a try and send your feedback.


## Python Versions and Compatibility

The library itself is tested with Python 3.6 and 3.8. The output of
the library is tested with Python 2.7, 3.5, 3.6, 3.7 and 3.8. No
testing has been done with Python 2.6 or earlier or with Python 3.0
to Python 3.4.

Lib3to6 does not add any runtime dependencies. It may inject code,
such as imports or temporary variables, but any such changes will
only add an `O(1)` overhead.

Since lib3to6 only works at the ast level at the time you build a
package, it is very easy violate some assumptions that lib3to6 makes
about your code. You could for example have your own `itertools`
module (which is one of the imports that lib3to6 may add to your
code) and the output of lib3to6 may not work as expected, because it
was assuming the import would be for the `itertools` module from the
standard library.


## Automatic Conversions

Not all new language features have a semantic equivalent in older
versions. To the extent these can be detected, an error will be
reported when these features are used.

Note that a fix is not applied if the lowest version of python that
you are targeting already supports the newer syntax. The conversions
are ordered by when the feature was introduced.


### PEP 572: Assignment Expressions (aka. the walrus operator)

```python
# Since 3.8
if match1 := pattern1.match(data):
    result = match1.group(1)

# From 2.7 to 3.7
match1 = pattern1.match(data)
if match1:
    result = match1.group(1)
```

Some expressions nested expressions in a condition are not so easy,
in which case lib3to6 will bend over backwards.

```python
# Since 3.8
while (block := f.read(4096)) != '':
    process(block)

# From 2.7 to 3.7
__loop_condition = True
while __loop_condition:
    block = f.read(4096)
    __loop_condition = block != ''
    if __loop_condition:
        process(block)
```


### PEP 563: Postponed Evaluation of Annotations

```python
# Since 3.7
class SelfRef:
    def method(self) -> SelfRef:
        pass

# From 3.0 to 3.6
class SelfRef:
    def method(self) -> 'SelfRef':
        pass
```

Note that this is not a stupid conversion that is applied to all
annotations, it is only applied to annotations that are forward
references. Backward references are left as is.


```python
# Since 3.7
class BackRef:
    def method(self) -> ForwardRef:
        pass

class ForwardRef:
    def method(self) -> BackRef:
        pass


# From 3.0 to 3.6
class BackRef:
    def method(self) -> 'ForwardRef':
        pass

class ForwardRef:
    def method(self) -> BackRef:
        pass
```

If you're supporting python 2.7, the annotation will of course be elided.


### PEP 498: formatted string literals.

```python
# Since 3.6
who = "World"
print(f"Hello {who}!")

# From 2.7 to 3.5
who = "World"
print("Hello {0}!".format(who))
```

The fixer also converts the newer `{var=}` syntax, even if you use
lib3to6 on a Python version older than 3.8.

```python
# Since 3.6
who = "World"
print(f"Hello {who=}!")

# From 2.7 to 3.5
print("Hello who={0}!".format(who))
```


### Eliding of Annotations

```python
# Since 3.0
def foo(bar: int) -> str:
    pass

# In 2.7
def foo(bar):
    pass
```


### PEP 515: underscores in numeric literals

```python
# Since 3.6
num = 1_234_567

# From 2.7 to 3.5
num = 1234567
```


### Unpacking generalizations

For literals...

```python
# Since 3.4
x = [*[1, 2], 3]

# From 2.7 to 3.3
x = [1, 2, 3]
```

For varargs...

```python
# Since 3.4
foo(0, *a, *b)

# From 2.7 to 3.3
foo(*([0] + list(a) + list(b))
```

For kwargs...

```python
# Since 3.4
foo(**x, y=22, **z)

# From 2.7 to 3.3
import itertools
foo(**dict(itertools.chain(x.items(), {'y': 22}.items(), z.items())))
```

Note that the import will only be added to your module once.


### Keyword only arguments


```python
# Since 3.6
def kwonly_func(*, kwonly_arg=1):
    ...

# From 2.7 to 3.5
def kwonly_func(**kwargs):
    kwonly_arg = kwargs.get('kwonly_arg', 1)
    ...
```


### Convert class based typing.NamedTuple usage to assignments


```python
import typing

# Since 3.5
class Bar(typing.NamedTuple):
    x: int
    y: str

# From 2.7 to 3.4
Bar = typing.NamedTuple('Bar', [('x', int), ('y', str)])
```


### New Style Classes

```python
# Since 3.0
class Bar:
  pass

# Before 3.0
class Bar(object):
  pass
```


### Future Imports

All `__future__` imports applicable to your target version are
prepended to every file.

```python
# -*- coding: utf-8 -*-
# This file is part of the <X> project
# ...
"""A docstring."""

x = True
```

With `target-version=27` (the default).

```python
# -*- coding: utf-8 -*-
# This file is part of the <X> project
# ...
"""A docstring."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

x = True
```

With `target-version=3.7`

```python
# -*- coding: utf-8 -*-
# This file is part of the <X> project
# ...
"""A docstring."""
from __future__ import annotations

x = True
```

Note that lib3to6 works mostly at the ast level, but an exception is
made for any comments that appear at the top of the file. These are
preserved as is, so your shebang, file encoding and licensing headers
will be preserved.


### Not Supported Features

An (obviously non-exhaustive) list of features which are **not
supported**, either because they involve a semantic change, or
because there is no simple ast transformation to make them work
across different python versions:

 - PEP 492 - `async`/`await`
 - PEP 465 - `@`/`__matmul__` operator
 - PEP 380 - `yield from` syntax
 - PEP 584 - union operators for `dict`
 - ordered dictionary (since python 3.6)


### Modules with Backports

Some new modules have backports, which lib3to6 will point to:

 - typing
 - pathlib -> pathlib2
 - secrets -> python2-secrets
 - ipaddress -> py2-ipaddress
 - csv -> backports.csv
 - lzma -> backports.lzma
 - enum -> enum34

For a full list of modules for which these warnings and errors apply,
please review [`MAYBE_UNUSABLE_MODULES` in
src/lib3to6/checkers_backports.py](https://gitlab.com/mbarkhau/lib3to6/blob/master/src/lib3to6/checkers_backports.py)

For some modules, the backport uses the same module name as the original
module in the standard library. By default, lib3to6 will only warn about
usage of such modules, since it cannot detect if you're using the module
from the backported package (good) or from the standard library (bad if
not available in your target version). If you would like to opt-in to hard
error messages, you can whitelist modules for which you have the
backported package as a dependency.

A good approach to adding such backports as dependencies is to
qualify the requirement with a [dependency
specification](https://www.python.org/dev/peps/pep-0508/), so that
users with a newer interpreter use the builtin module and don't
install the backport package that they don't need.

These work as arguments for `install_requires` and also in
`requirements.txt` files.

```python
import setuptools

setuptools.setup(
    name="my-package",
    install_requires=['typing;python_version<"3.5"'],
    ...
)
```

For testing, you can also pass these as a space separated parameter
to the `lib3to6` cli command:

```shell
$ lib3to6 my_script.py > /dev/null
WARNING - my_script.py@1: Use of import 'enum'.
    This module is only available since Python 3.5,
    but you configured target_version=2.7.
WARNING - my_script.py@2: Use of import 'typing'.
    This module is only available since Python 3.5,
    but you configured target_version=2.7.

import enum
import typing
...

$ lib3to6 `--install-requires='typing'` my_script.py > /dev/null
Traceback (most recent call last):
  ...
  File "/home/user/.../lib3to6/src/lib3to6/checkers_backports.py", line 134, in __call__
    raise common.CheckError(errmsg, node)
lib3to6.common.CheckError: my_script.py@1 - Prohibited import 'enum'.
    This module is available since Python 3.4,
    but you configured target_version='2.7'.
    Use 'https://pypi.org/project/enum34' instead.

$ lib3to6 `--install-requires='typing enum34'` my_script.py
import enum
import typing
...
```


## Projects that use lib3to6

 - [pycalver](https://gitlab.com/mbarkhau/pycalver)
 - [markdown-katex](https://gitlab.com/mbarkhau/markdown-katex)
 - [markdown-svgbob](https://gitlab.com/mbarkhau/markdown-svgbob)
 - [markdown-aafigure](https://gitlab.com/mbarkhau/markdown_aafigure)
 - [backports.pampy](https://pypi.org/project/backports.pampy/)


## Motivation

The main motivation for this project is to be able to use `mypy`
without sacrificing compatibility to older versions of python.

```python
# my_module/__init__.py
def hello(who: str) -> None:
    import sys
    print(f"Hello {who} from {sys.version.split()[0]}!")


print(__file__)
hello("世界")
```


```bash
$ pip install lib3to6
$ python -m lib3to6 my_module/__init__.py
```


```python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


def hello(who):
    import sys
    print('Hello {0} from {1}!'.format(who, sys.version.split()[0]))


print(__file__)
hello('世界')
```


Fixes are applied to match the semantics of python3 code as
close as possible, even when running on a python2.7 interpreter.

Some fixes that have been applied in the above:

    - PEP263 magic comment to declare the coding of the python
      source file. This allows the string literal `"世界"` to
      be decoded correctly.
    - `__future__` imports have been added. This includes the well
      known print statement -> function change. The unicode_literals
    - Type annotations have been removed
    - `f""` string -> `"".format()` conversion


### Usage in your `setup.py`

The cli command `lib3to6` is nice for demo purposes,
but for your project it is better to use it in your
setup.py file.


```python
# setup.py

import sys
import setuptools

packages = setuptools.find_packages(".")
package_dir = {"": "."}

install_requires = ['typing;python_version<"3.5"']

if any(arg.startswith("bdist") for arg in sys.argv):
    import lib3to6
    package_dir = lib3to6.fix(
        package_dir,
        target_version="2.7",
        install_requires=install_requires,
    )

setuptools.setup(
    name="my-module",
    version="2020.1001",
    packages=packages,
    package_dir=package_dir,
    install_requires=install_requires,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        ...
    ],
)
```

When you build you package, the contends of the resulting distribution
will be the code that was converted by lib3to6.


```bash
~/my-module $ python setup.py bdist_wheel --python-tag=py2.py3
running bdist_wheel
...
~/my-module$ ls -1 dist/
my_module-201808.1-py2.py3-none-any.whl

~/my-module$ python3 -m pip install dist/my_module-201808.1-py2.py3-none-any.whl
Processing ./dist/my_module-201808.1-py2.py3-none-any.whl
Installing collected packages: my-module
Successfully installed my-module-201808.1

~/my-module$ python2 -m pip install dist/my_module-201808.1-py2.py3-none-any.whl
Processing ./dist/my_module-201808.1-py2.py3-none-any.whl
Installing collected packages: my-module
Successfully installed my-module-201808.1
```

When testing, make sure you're not importing `my_module` from your local
directory, which is probably the original source code. Instead you can
either manipulate your `PYTHONPATH`, or simply switch directories...

```bash
~/$ python3 -c "import my_module"
/home/user/my-module/my_module/__init__.py
Hello 世界 from 3.6.5!

~/my-module$ cd ..
~/$ python3 -c "import my_module"
/home/user/envs/py36/lib/python3.6/site-packages/my_module/__init__.py
Hello 世界 from 3.6.5!

~$ python2 -c "import my_module"
/home/user/envs/py27/lib/python2.7/site-packages/my_module/__init__.py
Hello 世界 from 2.7.15!
```

### On Testing your Project

Projects that use lib3to6 should have a test suite that is executed
with the oldest python version that you want to support, using the
converted output generated by lib3to6. While you can develop using a
newer version of python, you should not blindly trust lib3to6 as it is
very easy to introduce backward incompatible changes if you only test
on the most recent interpreter. The most obvious example is that
lib3to6 cannot do much to help you if a library produces `bytes` on
Python 2 but `str` on Python 3.

The easiest way I have found to test a project, is to create a
distribution using `python setup.py bdist_wheel` with the above
modifications to the `setup.py`, install it and run the test suite
against the installed modules.


## How it works

This project works at the level of the python abstract syntax
tree (AST). The AST is transformed so that is only uses
constructs that are also valid in older versions of python. For
example it will translate f-strings to normal strings using the
``str.format`` method.

```python
>>> import sys
>>> sys.version_info
'3.6.5'
>>> import lib3to6
>>> py3_source = 'f"Hello {1 + 1}!"'
>>> cfg = {"fixers": ["f_string_to_str_format"]}
>>> py2_source = lib3to6.transpile_module(cfg, py3_source)

>>> print(py3_source)
f"Hello {1 + 1}!"
>>> print(py2_source)
# -*- coding: utf-8 -*-
"Hello {0}!".format(1 + 1)
```

At a lower level, this translation is based on detection of the
`ast.JoinedStr` node, which is translated into and AST that can be
serialized back into python syntax that will also work on older
versions.

```python
>>> print(lib3to6.parsedump_ast(py3_source))
Module(body=[Expr(value=JoinedStr(values=[
    Str(s='Hello '),
    FormattedValue(
        value=BinOp(left=Num(n=1), op=Add(), right=Num(n=1)),
        conversion=-1,
        format_spec=None,
    ),
    Str(s='!'),
]))])
>>> print(lib3to6.parsedump_ast(py2_source))
Module(body=[Expr(value=Call(
    func=Attribute(
        value=Str(s='Hello {0}!'),
        attr='format',
        ctx=Load(),
    ),
    args=[BinOp(left=Num(n=1), op=Add(), right=Num(n=1))],
    keywords=[]
))])
```

### Checker Errors

Of course this does not cover every aspect of compatibility.
Changes in APIs cannot be translated automatically in this way.

An obvious example, is that there is no way to transpile code
which uses `async` and `await`. In this case, `lib3to6`
will simply raise a CheckError. This applies only to your source
code though, so if import use a library which uses `async` and
`await`, everything may look fine until you run your tests
on python 2.7.

A more subtle example is the change in semantics of the builtin
`open` function.

```bash
$ cat open_example.py
with open("myfile.txt", mode="w", encoding="utf-8") as fobj:
    fobj.write("Hello Wörld!")
$ python2 open_example.py
Traceback (most recent call last):
  File "<string>", line 1, in <module>
TypeError: 'encoding' is an invalid keyword argument for this function
```


Usually there are alternative ways to write equivalent code that
works on all versions of python. For these common
incompatibilities lib3to6 will raise an error and suggest an
alternative, such as in this case using `io.open` instead.

```bash
$ lib3to6 open_example.py
Traceback (Most recent call last):
11  lib3to6      <module>         --> sys.exit(main())
764 core.py      __call__         --> return self.main(*args, **kwargs)
717 core.py      main             --> rv = self.invoke(ctx)
956 core.py      invoke           --> return ctx.invoke(self.callback, **ctx.params)
555 core.py      invoke           --> return callback(*args, **kwargs)
55  __main__.py  main             --> fixed_source_text = transpile.transpile_module(cfg, source_text)
260 transpile.py transpile_module --> checker(cfg, module_tree)
158 checkers.py  __call__         --> raise common.CheckError(msg, node)
CheckError: Prohibited keyword argument 'encoding' to builtin.open. on line 1 of open_example.py
```


Here `lib3to6` you will give you a `CheckError`, however it
remains your responsibility to write your code so that this
syntactic translation is semantically equivalent in both python3
and python2.

`lib3to6` uses the python `ast` module to parse your code. This
means that you need a modern python interpreter to transpile from
modern python to legacy python interpreter. You cannot transpile
features which your interpreter cannot parse. The intended use is
for developers of libraries who use the most modern python
version, but want their libraries to work on older versions.


## Contributing

The most basic contribution you can make is to provide minimal,
reproducible examples of code that should either be converted or
which should raise an error.

The project is hosted at
[gitlab.com/mbarkhau/lib3to6](https://gitlab.com/mbarkhau/lib3to6),
mainly because that's where the CI/CD is configured. GitHub is only
used as a copy/backup (and because that seems to be where many people
look for things).

You can get started with local development in just a few commands.

```shell
user@host:~/ $ git clone https://gitlab.com/mbarkhau/lib3to6.git
user@host:~/ $ cd lib3to6/
user@host:~/lib3to6/ ⎇master $ make help
user@host:~/lib3to6/ ⎇master $ make install     # creates conda environments
...
user@host:~/lib3to6/ ⎇master $ ls ~/miniconda3/envs/
user@host:~/lib3to6_pypy35 lib3to6_py27 lib3to6_py36 lib3to6_py37 lib3to6_py38
```

The targets in the makefile are set up to use the virtual environments.

```shell
user@host:~/lib3to6/ ⎇master $ make fmt
All done! ✨ 🍰 ✨
21 files left unchanged.

user@host:~/lib3to6/ ⎇master $ make lint mypy devtest
isort ... ok
sjfmt ... ok
flake8 .. ok
mypy .... ok
...
```

For debugging you may wish to activate a virtual environment anyway.


```shell
user@host:~/lib3to6/ ⎇master $ source activate
user@host:~/lib3to6/ ⎇master (lib3to6_py38) $ ipython
Python 3.8.2 | packaged by conda-forge | (default, Apr 24 2020, 08:20:52)
Type 'copyright', 'credits' or 'license' for more information
IPython 7.14.0 -- An enhanced Interactive Python. Type '?' for help.

In [1]: import lib3to6

In [2]: lib3to6.__file__
Out[2]: '/home/user/lib3to6/src/lib3to6/__init__.py'
```


## Future Work

In an ideal world, the project would cover all cases documented on
http://python-future.org and either:

 1. Transpile to code that will work on any version
 2. Raise an error, ideally pointing to a page and section on
    python-future.org or other documentation describing
    alternative methods of writing backwards compatible code.

https://docs.python.org/3.X/whatsnew/ also contains much info on
API changes that might be checked for, but checks and fixers for
these will only be written if they are common enough, otherwise
it's just too much work (patches are welcome though).
## Alternatives

Since starting this project, I've learned of the
[py-backwards](https://github.com/nvbn/py-backwards) project, which is
very, very similar in its approach. I have not evaluated it yet, to
determine for what projects it might be a better choice.

Some features that might be implemented

- PEP 380 - `yield from gen` syntax might be supported in a basic form
  by expanding to a `for x in gen: yield x`. That is not semantically
  equivalent though and I don't know if it's worth
  [implementing it properly](https://www.python.org/dev/peps/pep-0380/#formal-semantics)
- PEP 465 - `@` operator could be done by replacing all cases
  where the operator is used with a `__matmul__` method call.


## FAQ

 - Q: Isn't the tagline "Compatibility Matters" ironic,
   considering that python 3.6+ is required to build a wheel?
 - A: The irony is not lost. The issue is, how to parse source
   code from a newer version of python than the python
   interpreter itself supports. You can install lib3to6 on
   older versions of python, but you'll be limited to the
   features supported by that version. For example, you won't be
   able to use f"" strings on python 3.5, but most annotations
   will work fine.

 - Q: Why keep python2.7 alive? Just let it die already!
 - A: Indeed, and lib3to6 can help with that. Put yourself in the
   shoes of somebody who is working on an old codebase. It's not
   realistic hold all other development efforts while the
   codebase is migrated and tested, while everything else waits.

   Instead an incremental approach is usually the only option.
   With lib3to6, individual modules of the codebase can be
   migrated to python3, leaving the rest of the codebase
   untouched. The project can still run in a python 2.7
   environment, while developers increasingly move to using
   python 3.

   Additionally, lib3to6 is not just for compatibility with
   python 2.7, it also allows you to use new features like f""
   strings and variable annotations, while still maintaining
   compatibility with older versions of python 3.

 - Q: Why not `lib3to2`?
 - A: I can't honestly say much about `lib3to2`. It seems to not
   be maintained and looking at the source I thought it would be
   easier to just write something new that worked on the AST level.
   The scope of `lib3to6` is more general than 3to2, as you can
   use it even if all you care about is converting from python 3.6
   to 3.5.


[repo_ref]: https://gitlab.com/mbarkhau/lib3to6

[build_img]: https://gitlab.com/mbarkhau/lib3to6/badges/master/pipeline.svg
[build_ref]: https://gitlab.com/mbarkhau/lib3to6/pipelines

[codecov_img]: https://gitlab.com/mbarkhau/lib3to6/badges/master/coverage.svg
[codecov_ref]: https://mbarkhau.gitlab.io/lib3to6/cov

[license_img]: https://img.shields.io/badge/License-MIT-blue.svg
[license_ref]: https://gitlab.com/mbarkhau/lib3to6/blob/master/LICENSE

[mypy_img]: https://img.shields.io/badge/mypy-checked-green.svg
[mypy_ref]: https://mbarkhau.gitlab.io/lib3to6/mypycov

[style_img]: https://img.shields.io/badge/code%20style-%20sjfmt-f71.svg
[style_ref]: https://gitlab.com/mbarkhau/straitjacket/

[pypi_img]: https://img.shields.io/badge/PyPI-wheels-green.svg
[pypi_ref]: https://pypi.org/project/lib3to6/#files

[downloads_img]: https://pepy.tech/badge/lib3to6/month
[downloads_ref]: https://pepy.tech/project/lib3to6

[version_img]: https://img.shields.io/static/v1.svg?label=PyCalVer&message=v202006.1041&color=blue
[version_ref]: https://pypi.org/project/pycalver/

[pyversions_img]: https://img.shields.io/pypi/pyversions/lib3to6.svg
[pyversions_ref]: https://pypi.python.org/pypi/lib3to6

