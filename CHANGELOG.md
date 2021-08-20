# Changelog for https://github.com/mbarkhau/lib3to6


## Next

 - Add fixer for type hinting generics `'x: list[int]` -> `x: typing.List[int]`
 - Add fixer for Union Operator `'x: A | B` -> `x: typing.Union[A, B]`


## v202108.1048

 - Add new default integration method: [`lib3to6.Distribution`][href_readme_integration]
 - Deprecate old integration method (had issues with package data).
 - Fix invalid parsing of install_requires.
 - Fix cache invalidation when build config changes.
 - Fix type annotations with constants (e.g. `Optional['MyClass']`)


[href_readme_integration]: https://github.com/mbarkhau/lib3to6#integration-with-setuppy


## v202107.1047

 - Fix type annotations with list arguments


## v202107.1046

 - Fix type annotations with attribute access


## v202101.1045

 - Fixes for Python 3.9 and mypy 0.800


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
