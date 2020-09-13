# Changelog for https://gitlab.com/mbarkhau/lib3to6

## v202009.1042

 - New #6: per-file opt-in/opt-out using `# lib3to6: disabled`/`# lib3to6: enabled`


## v202006.1041

 - New: Lots more documentation.
 - New #5: Add detection of invalid imports and point to available backports. Use `install_requires` option to whitelist installed backports.
 - New: Checkers produce better error messages.
 - New: Colouring of diffs when using `lib3to6` cli command.
 - New: Checker for `yield from` syntax on target version doesn't support it
 - New: Checker for `@` operator when target version doesn't support it
 - Fix #3: `--target-version` argument is ignored [gitlab../issues/3](https://gitlab.com/mbarkhau/lib3to6/-/issues/3)
 - Fix #4: Remove `from __future__ import X` when the target version doesn't support it.
 - Fix #4: Convert Forward Reference Annotations to strings [gitlab../issues/4](https://gitlab.com/mbarkhau/lib3to6/-/issues/4) Thank you [Faidon Liambotis](https://gitlab.com/paravoid) for your help with testing and helping to debug ❤️.
 - Fix: Don't apply keyword only args fixer for `--target-version=3.0` or above.


## v202002.0031

 - Compatibility fixes for Python 3.8
 - Add support for f-string `=` specifier
 - Add support for `:=` walrus operator (except inside comprehensions)


## v201902.0030

 - Fix python 2 builtins were not always overridden correctly.
 - Fix pypy compatibility testing
 - Better mypy coverage


## v201812.0021-beta

 - Recursively apply some fixers.


## v201812.0020-alpha

 - Move to gitlab.com
 - Use bootstrapit
 - Fix bugs based on use with pycalver


## v201809.0019-alpha

 - CheckErrors include log line numbers
 - Transpile errors now include filenames
 - Added fixers for renamed modules, e.g.
    .. code-block:: diff

        - import queue
        + try:
        +     import queue
        + except ImportError:
        +     import Queue as queue


## v201808.0014-alpha

 - Better handling of package_dir
 - Change to `CalVer Versioning <https://calver.org/>`_
 - Remove console script in favour of simple ``python -m lib3to6``
 - Rename from ``three2six`` -> ``lib3to6``
