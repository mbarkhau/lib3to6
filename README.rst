``three2six`` : Compatibility Matters
=====================================

Build py2.7+ wheels from py3.6 source. The idea is quite similar
to Bable https://babeljs.io/.

.. start-badges

.. list-table::
    :stub-columns: 1

    * - package
      - | |license| |version| |wheel| |pyversions|
    * - tests
      - | |travis| |mypy| |coverage|

.. |travis| image:: https://api.travis-ci.org/mbarkhau/three2six.svg?branch=master
    :target: https://travis-ci.org/mbarkhau/three2six
    :alt: Build Status

.. |mypy| image:: http://www.mypy-lang.org/static/mypy_badge.svg
    :target: http://mypy-lang.org/
    :alt: Checked with mypy

.. |coverage| image:: https://img.shields.io/badge/coverage-84%25-green.svg
    :target: https://travis-ci.org/mbarkhau/three2six
    :alt: Code Coverage

.. |license| image:: https://img.shields.io/pypi/l/three2six.svg
    :target: https://pypi.python.org/pypi/three2six
    :alt: MIT License

.. |version| image:: https://img.shields.io/pypi/v/three2six.svg
    :target: https://pypi.python.org/pypi/three2six
    :alt: Version Number

.. |wheel| image:: https://img.shields.io/pypi/wheel/three2six.svg
    :target: https://pypi.python.org/pypi/three2six
    :alt: PyPI Wheel

.. |pyversions| image:: https://img.shields.io/pypi/pyversions/three2six.svg
    :target: https://pypi.python.org/pypi/three2six
    :alt: Supported Python Versions


Motivation
----------

The main motivation for this project is to be able to use ``mypy``
without sacrificing compatability to older versions of python.

.. code-block:: python

    # my_module/__init__.py
    def hello(who: str) -> None:
        print(f"Hello {who}!")

    hello("World")


.. code-block:: bash

    $ pip install three2six
    $ three2six my_module/__init__.py
    # -*- coding: utf-8 -*-

    from __future__ import absolute_import
    from __future__ import division
    from __future__ import print_function
    from __future__ import unicode_literals

    def hello(who):
        print('Hello {0}!'.format(who))

    hello("World")


The cli command ``three2six`` is nice for demo purposes,
but for your project it is better to use it in your
setup.py file.

.. code-block:: python

    # setup.py

    packages = ["my_module"]

    if "bdist_wheel" in sys.argv:
        import three2six
        packages, package_dir = three2six.repackage(packages)

    setuptools.setup(
        name="my-module",
        version="0.1.0",
        packages=packages,
        package_dir=package_dir,
        ...
    )

.. code-block:: bash

    $ python setup.py bdist_wheel --python-tag=py2.py3
    running bdist_wheel
    running build
    running build_py
    copying /tmp/three2six_qu7ub0bk/my_module/__init__.py -> build/lib/my_module
    ...

    $ python3 build/lib/my_module/__init__.py
    Hello World!

    $ python2 build/lib/my_module/__init__.py
    Hello World!


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

..

    Some new libraries have backports, which warnings will point to:

     - typing
     - pathlib
     - secrets
     - ipaddress
     - csv -> backports.csv
     - lzma -> backports.lzma
     - enum -> flufl.enum


Project Status (as of 2018-07-12): Experimental
-----------------------------------------------

Only use this library if you intend to participate in testing or
development. This README serves partially as a TODO list, not
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
    >>> import three2six
    >>> py3_source = 'f"Hello {1 + 1}!"'
    >>> cfg = {"fixers": ["f_string_to_str_format"]}
    >>> py2_source = three2six.transpile_module(cfg, py3_source)

    >>> print(py3_source)
    f"Hello {1 + 1}!"
    >>> print(py2_source)
    # -*- coding: utf-8 -*-
    "Hello {0}!".format(1 + 1)

    >>> print(three2six.parsedump_ast(py3_source))
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
    >>> print(three2six.parsedump_ast(py2_source))
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
which uses ``async`` and ``await``. In this case, ``three2six``
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
incompatabilities three2six will raise an error and suggest an
alternative, such as in this case using ``io.open`` instead.

.. code-block:: bash

    $ three2six open_example.py
    TODO:

    $ three2six open_example.py --diff
    TODO:


Here ``three2six`` you will ge

however it remains your
responsibility to write your code so that this syntactic
translation is semantically equivalent in both python3 and
python2.

three2six uses the python ast module to parse your code. This
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
   interpreter itself supports. You can install three2six on
   older versions of python, but you'll be limited to the
   features supported by that version. For example, you won't be
   able to use f"" strings on python 3.5, but most annotations
   will work fine.

 - Q: Why keep python2.7 alive, just let it die already?
 - A: This is not just for python 2.7, it also allows you to use
   new features like f"" strings and variable annotations, and
   build wheels which work for python 3.5.