import ast


# https://gist.github.com/marsam/d2a5af1563d129bb9482
def dump_ast(node, annotate_fields=True, include_attributes=False, indent="  "):
    """
    Return a formatted dump of the tree in *node*.  This is mainly useful for
    debugging purposes.  The returned string will show the names and the values
    for fields.  This makes the code impossible to evaluate, so if evaluation is
    wanted *annotate_fields* must be set to False.  Attributes such as line
    numbers and column offsets are not dumped by default.  If this is wanted,
    *include_attributes* can be set to True.
    """
    def _format(node, level=0):
        if isinstance(node, ast.AST):
            fields = [(a, _format(b, level)) for a, b in ast.iter_fields(node)]
            if include_attributes and node._attributes:
                fields.extend([
                    (a, _format(getattr(node, a), level))
                    for a in node._attributes
                ])

            if annotate_fields:
                field_parts = ("%s=%s" % field for field in fields)
            else:
                field_parts = (b for a, b in fields)

            fields_str = ", ".join(field_parts)
            node_name = node.__class__.__name__
            return node_name + "(" + fields_str + ")"
        elif isinstance(node, list):
            lines = ["["]
            lines.extend((
                indent * (level + 2) + _format(x, level + 2) + ","
                for x in node
            ))
            if len(lines) > 1:
                lines.append(indent * (level + 1) + "]")
            else:
                lines[-1] += "]"
            return "\n".join(lines)
        return repr(node)

    if not isinstance(node, (ast.AST, list)):
        raise TypeError("expected AST, got %r" % node.__class__.__name__)
    return _format(node)


def parsedump_ast(code, mode="exec", **kwargs):
    """Parse some code from a string and pretty-print it."""
    node = ast.parse(code, mode=mode)   # An ode to the code
    return dump_ast(node, **kwargs)


def _clean_whitespace(fixture_str):
    if fixture_str.strip().count("\n") == 0:
        return fixture_str.strip()

    fixture_str = fixture_str.lstrip()
    fixture_lines = fixture_str.splitlines()
    indent = min(
        len(line) - len(line.lstrip())
        for line in fixture_lines
        if len(line) > len(line.lstrip())
    )
    indent_str = " " * indent
    cleaned_lines = []
    for line in fixture_lines:
        if line.startswith(indent_str):
            cleaned_lines.append(line[indent:])
        else:
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines)
