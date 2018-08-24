lib3to6: compatibility matters
==============================

Build universal python from a substantial subset of Python 3.7
syntax. (Python 3.7 -> Python 2.7+ and 3.4+). The idea is quite
similar to Bable https://babeljs.io/.

.. start-badges

.. list-table::
    :stub-columns: 1

    * - package
      - | |license| |pypi| |version| |wheel| |pyversions|
    * - tests
      - | |travis| |mypy| |coverage|

.. |travis| image:: https://api.travis-ci.org/mbarkhau/lib3to6.svg?branch=master
    :target: https://travis-ci.org/mbarkhau/lib3to6
    :alt: Build Status

.. |mypy| image:: http://www.mypy-lang.org/static/mypy_badge.svg
    :target: http://mypy-lang.org/
    :alt: Checked with mypy

.. |coverage| image:: https://img.shields.io/badge/coverage-86%25-green.svg
    :target: https://travis-ci.org/mbarkhau/lib3to6
    :alt: Code Coverage

.. |license| image:: https://img.shields.io/pypi/l/lib3to6.svg
    :target: https://pypi.python.org/pypi/lib3to6
    :alt: MIT License

.. |pypi| image:: https://img.shields.io/pypi/v/lib3to6.svg
    :target: https://pypi.python.org/pypi/lib3to6
    :alt: PyPI Version

.. |version| image:: https://img.shields.io/badge/CalVer-v201808.0014-blue.svg
    :target: https://calver.org/
    :alt: CalVer v201808.0014

.. |wheel| image:: https://img.shields.io/pypi/wheel/lib3to6.svg
    :target: https://pypi.python.org/pypi/lib3to6
    :alt: PyPI Wheel

.. |pyversions| image:: https://img.shields.io/pypi/pyversions/lib3to6.svg
    :target: https://pypi.python.org/pypi/lib3to6
    :alt: Supported Python Versions


Motivation
----------

The main motivation for this project is to be able to use ``mypy``
without sacrificing compatability to older versions of python.


.. code-block:: python

    # my_module/__init__.py
    def hello(who: str) -> None:
        print(f"Hello {who}!")

    hello("世界")


.. code-block:: bash

    $ pip install lib3to6
    $ python -m lib3to6 my_module/__init__.py


.. code-block:: python

    # -*- coding: utf-8 -*-
    from __future__ import absolute_import
    from __future__ import division
    from __future__ import print_function
    from __future__ import unicode_literals

    def hello(who):
        print('Hello {0}!'.format(who))

    hello("世界")


Fixes are applied to match the semantics of python3 code as
close as possible, even when running on a python2.7 interpreter.

Some fixes that have been applied:

    - PEP263 magic comment to declare the coding of the python
      source file. This allows the string literal ``"世界"`` to
      be decoded correctly.
    - ``__future__`` imports have been added. This includes the well
      known print statement -> function change. The unicode_literals
    - Type annotations have been removed
    - f string -> "".format  conversion


The cli command ``lib3to6`` is nice for demo purposes,
but for your project it is better to use it in your
setup.py file.

.. code-block:: python

    # setup.py

    import sys
    import setuptools

    packages = setuptools.find_packages(".")
    package_dir = {"": "."}

    if "sdist" in sys.argv or "bdist_wheel" in sys.argv:
        import lib3to6
        package_dir = lib3to6.fix_package_dir()

    setuptools.setup(
        name="my-module",
        version="0.1.0",
        packages=packages,
        package_dir=package_dir,
        ...
    )

.. code-block:: bash

    $ python setup.py sdist bdist_wheel --python-tag=py2.py3
    running sdist
    running egg_info
    ...
    running bdist_wheel
    running build
    running build_py
    copying /tmp/lib3to6_qu7ub0bk/my_module/__init__.py -> build/lib/my_module
    ...

    $ python3 build/lib/my_module/__init__.py
    Hello 世界!

    $ python2 build/lib/my_module/__init__.py
    Hello 世界!


Feature Support
---------------

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


Project Status (as of 2018-08-18): Experimental
-----------------------------------------------

Only use this library if you intend to participate in testing or
development. I'm using it on personal projects and am still
finding bugs. This README serves partially as a TODO list, not
everything advertised is implemented yet.

The goal is to go through all of http://python-future.org and
either:

 1. Transpile to code that will work on any version
 2. Raise an error, ideally pointing to a page and section on
    python-future.org or other documentation describing
    alternative methods of writing backwards compatible code.

https://docs.python.org/3.X/whatsnew/ also contains much info on
api changes that might be checked for, but checks and fixers for
these will only be written if they are common enough, otherwise
it's just too much work (patches are welcome though).


How it works
------------

This project works at the level of the python abstract syntax
tree (AST). The AST is transformed so that is only uses
constructs that are also valid in older versions of python. For
example it will translate f-strings to normal strings using the
``str.format`` method.

.. code-block:: python

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


Of course this does not cover every aspect of compatability.
Changes in APIs cannot be translated automatically in this way.

An obvious example, is that there is no way to transpile code
which uses ``async`` and ``await``. In this case, ``lib3to6``
will simply raise a CheckError. This applies only to your source
code though, so if import use a library which uses ``async`` and
``await``, everything may look fine until you run your tests
on python 2.7.

A more subtle example is the change in semantics of the builtin
``open`` function.

.. code-block:: bash

    $ cat open_example.py
    with open("myfile.txt", mode="w", encoding="utf-8") as fh:
        fh.write("Hello Wörld!")
    $ python2 open_example.py
    Traceback (most recent call last):
      File "<string>", line 1, in <module>
    TypeError: 'encoding' is an invalid keyword argument for this function


Usually there are alternative ways to write equivalent code that
works on all versions of python. For these common
incompatabilities lib3to6 will raise an error and suggest an
alternative, such as in this case using ``io.open`` instead.

.. code-block:: bash

    $ lib3to6 open_example.py
    TODO:

    $ lib3to6 open_example.py --diff
    TODO:


Here ``lib3to6`` you will ge

however it remains your
responsibility to write your code so that this syntactic
translation is semantically equivalent in both python3 and
python2.

lib3to6 uses the python ast module to parse your code. This
means that you need a modern python interpreter to transpile from
modern python to legacy python interpreter. You cannot transpile
features which your interpreter cannot parse. The intended use is
for developers of libraries who use the most modern python
version, but want their libraries to work on older versions.


FAQ
---

 - Q: Isn't the tagline "Compatibility Matters" ironic,
   considering that python 3.6+ is required to build a wheel?
 - A: The irony is not lost. The issue is, how to parse source
   code from a newer version of python than the python
   interpreter itself supports. You can install lib3to6 on
   older versions of python, but you'll be limited to the
   features supported by that version. For example, you won't be
   able to use f"" strings on python 3.5, but most annotations
   will work fine.

 - Q: Why keep python2.7 alive, just let it die already?
 - A: This is not just for python 2.7, it also allows you to use
   new features like f"" strings and variable annotations, and
   build wheels which work for python 3.5.

 - Q: Why not ``lib3to2``?
 - A: I can't honestly say much about ``lib3to2``. It seems to not
   be maintained and looking at the source I thought it would be
   easier to just write something new that worked on the AST level.
   The scope of ``lib3to6`` is more general than 3to2, as you can
   use it even if all you care about is converting from python 3.6
   to 3.5.
