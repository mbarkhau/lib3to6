import pytest

from three2six.common import CheckError
from three2six import utils


TEST_STRINGS = {
    (
        "no_overridden_builtins",
        """
        def map(x):
            pass
        """,
        "Prohibited override of builtin 'map'"
    ),
    (
        "no_overridden_builtins",
        """
        class filter(x):
            pass
        """,
        "Prohibited override of builtin 'filter'"
    ),
    (
        "no_overridden_builtins",
        """
        zip = "foobar"
        """,
        "Prohibited override of builtin 'zip'"
    ),
    (
        "no_overridden_builtins",
        """
        repr: str = "foobar"
        """,
        "Prohibited override of builtin 'repr'"
    ),
    (
        "no_overridden_builtins",
        """
        import foobar as iter
        """,
        "Prohibited override of builtin 'iter'"
    ),
    (
        "no_overridden_builtins",
        """
        import reversed
        """,
        "Prohibited override of builtin 'reversed'"
    ),
    (
        "no_overridden_builtins",
        """
        def foo(input):
            pass
        """,
        "Prohibited override of builtin 'input'"
    ),
    (
        "no_overridden_builtins",
        """
        def foo(min=None):
            pass
        """,
        "Prohibited override of builtin 'min'"
    ),
    (
        "no_overridden_builtins",
        """
        def foo(*, max=None):
            pass
        """,
        "Prohibited override of builtin 'max'"
    ),
    (
        "no_overridden_builtins",
        """
        class foo:
            dict = None
        """,
        "Prohibited override of builtin 'dict'"
    ),
    (
        "no_overridden_builtins",
        """
        class foo:
            list:  None
        """,
        "Prohibited override of builtin 'list'"
    ),
    # (
    #     "no_overridden_builtins",
    #     """
    #     def foo(x: int = None):
    #         pass
    #     """,
    #     None
    # ),
    # (
    #     "no_open_with_encoding,0",
    #     """
    #     data = open(filepath, mode="rb").read()
    #     assert isinstance(data, bytes)
    #     """,
    #     None
    # ),
    # (
    #     "no_open_with_encoding,1",
    #     """
    #     with open(filepath, mode="wb") as fh:
    #         fh.write(b"test")
    #     """,
    #     None
    # ),
    # (
    #     "no_open_with_encoding",
    #     """
    #     with open(filepath, mode="w") as fh:
    #         fh.write("test")
    #     """,
    #     "Prohibited use of builtin open with encoding"
    # ),
    # (
    #     "no_open_with_encoding",
    #     """
    #     with open(filepath, mode="w", encoding="utf-8") as fh:
    #         fh.write("test")
    #     """,
    #     "Prohibited use of builtin open with encoding"
    # ),
}


@pytest.mark.parametrize("checker_names, in_str, expected_error_msg", TEST_STRINGS)
def test_checkers(checker_names, in_str, expected_error_msg):
    try:
        utils.transpile_and_dump(in_str, {"checkers": checker_names})
        assert expected_error_msg is None
    except CheckError as result_error:
        assert expected_error_msg and expected_error_msg in str(result_error)
