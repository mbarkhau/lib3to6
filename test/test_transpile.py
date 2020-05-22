from lib3to6 import transpile
from lib3to6.utils import clean_whitespace


def test_parse_header_simple():
    source = clean_whitespace(
        """
        # coding: ascii
        # Header line
        expr = 1 + 1
        """
    )
    coding, header = transpile.parse_module_header(source, "2.7")
    assert coding == "ascii"
    assert header == "# coding: ascii\n# Header line\n"


def test_parse_header_coding():
    source = clean_whitespace(
        """
    # coding: shift_jis
    # 今日は
    expr = 1 + 1
    """
    )
    coding, header = transpile.parse_module_header(source, "2.7")
    assert coding == "shift_jis"
    assert header == "# coding: shift_jis\n# 今日は\n"

    source_data = source.encode("shift_jis")
    coding, header = transpile.parse_module_header(source_data, "2.7")
    assert coding == "shift_jis"
    assert header == "# coding: shift_jis\n# 今日は\n"
