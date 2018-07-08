``three2six``
=============

``three2six`` is a library to transpile modern python (3.6+) code
to equivalent legacy python (2.7+) code. The idea is quite
similar to Bable https://babeljs.io/.

Any new language feature which has an equivalent translation
will be translated, if you try to use a new language feature
which cannot be translated, you will get a warning.

Supported features include:

 - PEP 498: formatted string literals.
 - Eliding of annotations
 - Unpacking generalizations
 - Keyword only arguments
 - Warnings for code that cannot be transpile
 - PEP 515: underscores in numeric literals
 - map/zip/filter to itertools equivalents

An (obviously non exhaustive) list of features not supported:

 - async/await
 - yield from
 - @/__matmul__ operator

Some new libraries have backports, which warnings will point to:

 - typing
 - pathlib
 - secrets
 - ipaddress
 - csv -> backports.csv
 - lzma -> backports.lzma
 - enum -> flufl.enum


Project Status (as of 2018-07-08): Experimental
-----------------------------------------------

Only use this library if you intend to participate in testing or
development. This README serves partially as a TODO list, not
everything advertised is implemented yet.

The goal is to go through all of http://python-future.org and
either:

 1. Transpile to code that will work on any version
 2. Raise an error, pointing to a page and section on
    python-future.org

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


Testing
-------

The ``three2six`` command is only intended for testing and
validation. In particular, you should never be working directly
with the output transpiled output. With that out of the way,
let's have a look at what three2six does.

.. code-block:: bash

    $ python3 --version
    Python 3.6.5 :: Anaconda, Inc.
    $ python2 --version
    Python 2.7.15 :: Anaconda, Inc.

    $ cat hello_world_three.py
    who = "World"
    print(f"Hello {who}!")

    $ python3 hello_world_three.py
    Hello World!

    $ python2 hello_world_three.py
      File "my_module/__init__.py", line 2
        print(f"Hello {who}!")
                            ^
    SyntaxError: invalid syntax

    $ pip3 install three2six
    $ three2six hello_world_three.py
    # -*- coding: utf-8 -*-
    from __future__ import unicode_literals
    from __future__ import print_function
    from __future__ import division
    from __future__ import absolute_import
    who = "World"
    print("Hello {0}!".format(who))

    $ three2six hello_world_three.py > hello_world_six.py
    $ python2 hello_world_six.py
    Hello World!


Project Setup
-------------

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


.. code-block:: python

    # my_module/__init__.py
    who = "World"
    print(f"Hello {who}!")


.. code-block:: bash

    $ python3 setup.py bdist_wheel
    running bdist_wheel
    running build
    running build_py
    copying /tmp/three2six_qu7ub0bk/my_module/__init__.py -> build/lib/my_module
    ...

    $ cat build/lib/my_module/__init__.py
    # -*- coding: utf-8 -*-
    from __future__ import unicode_literals
    from __future__ import print_function
    from __future__ import division
    from __future__ import absolute_import
    who = "World"
    print("Hello {0}!".format(who))

    $ python3 build/lib/my_module/__init__.py
    Hello World!

    $ python2 build/lib/my_module/__init__.py
    Hello World!
