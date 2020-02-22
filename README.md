# [lib3to6][repo_ref]

Compile Python 3.6+ code to Python 2.7+ compatible code. The idea is quite
similar to Bable https://babeljs.io/. Develop using the newest interpreter and
use (most) new language features without sacrificing backward compatibility.

Project/Repo:

[![MIT License][license_img]][license_ref]
[![Supported Python Versions][pyversions_img]][pyversions_ref]
[![PyCalVer v202002.0032][version_img]][version_ref]
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
  $ md_toc -i gitlab README.md
-->


[](TOC)

  - [Project Status (as of 2020-02-21): Beta](#project-status-as-of-2020-02-21-beta)
  - [Getting started with Development](#getting-started-with-development)
  - [Motivation](#motivation)
  - [Feature Support](#feature-support)
  - [How it works](#how-it-works)
  - [FAQ](#faq)

[](TOC)


## Project Status (as of 2020-02-21): Beta

I've been using this library for a year on a few projects without much incident.
An example of such a project is [PyCalVer](https://pypi.org/project/pycalver/). I
have tested with Python 3.8 and made some fixes and updates. The library serves
my purposes and I don't anticipate major updates, but I will refrain from calling
it stable until there has been more adoption by projects other than my own.

Please give it a try and send your feedback.

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


## Getting started with Development


```shell
$ git clone https://gitlab.com/mbarkhau/lib3to6.git
$ cd lib3to6/
lib3to6 $ make install
...
lib3to6 $ make test
...
lib3to6 $ make help
```


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

Some fixes that have been applied:

    - PEP263 magic comment to declare the coding of the python
      source file. This allows the string literal `"世界"` to
      be decoded correctly.
    - `__future__` imports have been added. This includes the well
      known print statement -> function change. The unicode_literals
    - Type annotations have been removed
    - f string -> "".format  conversion


The cli command `lib3to6` is nice for demo purposes,
but for your project it is better to use it in your
setup.py file.


```python
# setup.py

import sys
import setuptools

packages = setuptools.find_packages(".")
package_dir = {"": "."}

if any(arg.startswith("bdist") for arg in sys.argv):
    import lib3to6
    package_dir = lib3to6.fix(package_dir)

setuptools.setup(
    name="my-module",
    version="201808.1",
    packages=packages,
    package_dir=package_dir,
)
```


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


To make sure we're importing my_module from the installation, as
opposed to from the local directory, we have to switch
directories.


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


## Feature Support

Not all new language features have a semantic equivalent in older
versions. To the extent these can be detected, an error will be
reported when these features are used.

An (obviously non exhaustive) list of features which are **not
supported**:

 - async/await
 - yield from
 - @/__matmul__ operator

Features which **are supported**:

 - PEP 498: formatted string literals.
 - Eliding of annotations
 - Unpacking generalizations
 - Keyword only arguments
 - PEP 515: underscores in numeric literals
 - map/zip/filter to itertools equivalents
 - Convert class based typing.NamedTuple usage to assignments

Some new libraries have backports, which warnings will point to:

 - typing
 - pathlib
 - secrets
 - ipaddress
 - csv -> backports.csv
 - lzma -> backports.lzma
 - enum -> flufl.enum


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

>>> print(lib3to6.parsedump_ast(py3_source))
Module(body=[Expr(value=JoinedStr(values=[
    Str(s='Hello '),
    FormattedValue(
        value=BinOp(
            left=Num(n=1),
            op=Add(),
            right=Num(n=1),
        ),
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
    args=[BinOp(
        left=Num(n=1),
        op=Add(),
        right=Num(n=1),
    )],
    keywords=[]
))])
```


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
with open("myfile.txt", mode="w", encoding="utf-8") as fh:
    fh.write("Hello Wörld!")
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

[version_img]: https://img.shields.io/static/v1.svg?label=PyCalVer&message=v202002.0032&color=blue
[version_ref]: https://pypi.org/project/pycalver/

[pyversions_img]: https://img.shields.io/pypi/pyversions/lib3to6.svg
[pyversions_ref]: https://pypi.python.org/pypi/lib3to6

