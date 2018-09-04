Changelog for lib3to6
=====================

v201809.0018-alpha
------------------

 - CheckErrors include log line numbers
 - Transpile errors now include filenames
 - Added fixers for renamed modules, e.g.

    .. code-block:: diff

        - import queue
        + try:
        +     import queue
        + except ImportError:
        +     import Queue as queue


v201808.0014-alpha
------------------

 - Better handling of package_dir
 - Change to `CalVer Versioning <https://calver.org/>`_
 - Remove console script in favour of simple ``python -m lib3to6``
 - Rename from ``three2six`` -> ``lib3to6``
