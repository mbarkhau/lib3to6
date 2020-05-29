import ast

from . import common


class CheckerBase:

    # no info -> always apply
    version_info: common.VersionInfo = common.VersionInfo()

    def __call__(self, ctx: common.BuildContext, tree: ast.Module) -> None:
        raise NotImplementedError()
