three2six
=========

Transpile from a modern python 3 codebase to legacy python 2. Use
some of your favourite features of modern python, without
compromising compatability to older versions.

This project works at a syntax level Your code is translated to
syntactically valid python2.7, however it remains your
responsibility to write your code so that this syntactic
translation is semantically equivalent in both python3 and
python2.

three2six uses the python ast module to parse your code. This
means that you cannot transpile from modern python to legacy
python using a legacy python interpreter. The intended use is for
developers of libraries who use the most modern python version,
but want their libraries to work on older versions.


Project Status (as of 2018-06-09): Experimental
-----------------------------------------------

At this point, you should only consider using this  if you intend
to participate in development.


Testing
-------

While this is not the intended usage, it is the quickest way to
demonstrate what three2six does. The intended usage method is
demonstrated in the Project Setup.

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
    print(f"Hello {0}!".format(who))

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
    print(f"Hello {0}!".format(who))

    $ python3 build/lib/my_module/__init__.py
    Hello World!

    $ python2 build/lib/my_module/__init__.py
    Hello World!
