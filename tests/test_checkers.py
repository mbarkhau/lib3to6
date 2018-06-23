import pytest

from three2six.common import CheckError
from three2six import utils


TEST_STRINGS = {
    "no_overridden_builtins,1": (
        """
        def map(x):
            pass
        """,
        "Prohibited override of builtin 'map'"
    ),
    "no_overridden_builtins,2": (
        """
        class filter(x):
            pass
        """,
        "Prohibited override of builtin 'filter'"
    ),
    "no_overridden_builtins,3": (
        """
        zip = "foobar"
        """,
        "Prohibited override of builtin 'zip'"
    ),
    "no_overridden_builtins,4": (
        """
        repr: str = "foobar"
        """,
        "Prohibited override of builtin 'repr'"
    ),
    "no_overridden_builtins,5": (
        """
        import foobar as iter
        """,
        "Prohibited override of builtin 'iter'"
    ),
    "no_overridden_builtins,6": (
        """
        import reversed
        """,
        "Prohibited override of builtin 'reversed'"
    ),
    "no_overridden_builtins,7": (
        """
        def foo(input):
            pass
        """,
        "Prohibited override of builtin 'input'"
    ),
    "no_overridden_builtins,8": (
        """
        def foo(min=None):
            pass
        """,
        "Prohibited override of builtin 'min'"
    ),
    "no_overridden_builtins,9": (
        """
        def foo(*, max=None):
            pass
        """,
        "Prohibited override of builtin 'max'"
    ),
    "no_overridden_builtins,10": (
        """
        class foo:
            dict = None
        """,
        "Prohibited override of builtin 'dict'"
    ),
    "no_overridden_builtins,11": (
        """
        class foo:
            list:  None
        """,
        "Prohibited override of builtin 'list'"
    ),
    "no_overridden_builtins,12": (
        """
        def foo(x: int = None):
            pass
        """,
        None
    ),
}


@pytest.mark.parametrize("test_desc, fixture", list(TEST_STRINGS.items()))
def test_checkers(test_desc, fixture):
    checker_names = [
        name
        for name in test_desc.split(",")
        if not name.isdigit()
    ]
    cfg = {"checkers": ",".join(checker_names)}

    in_str, expected_error_msg = fixture
    try:
        utils.transpile_and_dump(in_str, cfg)
        assert expected_error_msg is None
    except CheckError as result_error:
        assert expected_error_msg and expected_error_msg in str(result_error)
