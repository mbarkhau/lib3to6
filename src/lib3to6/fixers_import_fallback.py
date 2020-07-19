# This file is part of the lib3to6 project
# https://gitlab.com/mbarkhau/lib3to6
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

import ast

from . import common
from . import fixer_base as fb


def _try_fallback(node: ast.stmt, fallback_node: ast.stmt) -> ast.Try:
    return ast.Try(
        body=[node],
        handlers=[
            ast.ExceptHandler(
                type=ast.Name(id="ImportError", ctx=ast.Load()), name=None, body=[fallback_node]
            )
        ],
        orelse=[],
        finalbody=[],
    )


class ModuleImportFallbackFixerBase(fb.TransformerFixerBase):

    new_name: str
    old_name: str

    def visit_Import(self, node: ast.Import) -> ast.stmt:
        if len(node.names) != 1:
            return node

        alias = node.names[0]
        if alias.name != self.new_name:
            return node

        if alias.asname:
            asname = alias.asname
        elif "." in self.new_name:
            asname = self.new_name.replace(".", "_")
            msg    = (
                f"Prohibited use of 'import {self.new_name}', "
                f"use 'import {self.new_name} as {asname}' instead."
            )
            raise common.CheckError(msg, node)
        else:
            asname = self.new_name

        return _try_fallback(node, ast.Import(names=[ast.alias(name=self.old_name, asname=asname)]))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.stmt:
        if node.module != self.new_name:
            return node

        return _try_fallback(
            node, ast.ImportFrom(module=self.old_name, names=node.names, level=node.level)
        )


class ConfigParserImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "configparser"
    old_name     = "ConfigParser"


class SocketServerImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "socketserver"
    old_name     = "SocketServer"


class BuiltinsImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "builtins"
    old_name     = "__builtin__"


class QueueImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "queue"
    old_name     = "Queue"


class CopyRegImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "copyreg"
    old_name     = "copy_reg"


class WinRegImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "winreg"
    old_name     = "_winreg"


class ReprLibImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "reprlib"
    old_name     = "repr"


class ThreadImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "_thread"
    old_name     = "thread"


class DummyThreadImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "_dummy_thread"
    old_name     = "dummy_thread"


# NOTE (mb 2018-09-01): Up to here are the simple cases. Below
#   here, the fixes only work when using ast.FromImport, or when
#   using asname. For everything else, we raise a CheckError. The
#   only other option would be to scan whole tree and rewrite
#   reverences


class HttpCookiejarImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "http.cookiejar"
    old_name     = "cookielib"


class UrllibParseImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "urllib.parse"
    old_name     = "urlparse"


class UrllibRequestImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "urllib.request"
    old_name     = "urllib2"


class UrllibErrorImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "urllib.error"
    old_name     = "urllib2"


class UrllibRobotParserImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "urllib.robotparser"
    old_name     = "robotparser"


class XMLRPCClientImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "xmlrpc.client"
    old_name     = "xmlrpclib"


class XmlrpcServerImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "xmlrpc.server"
    old_name     = "SimpleXMLRPCServer"


class HtmlParserImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "html.parser"
    old_name     = "HTMLParser"


class HttpClientImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "http.client"
    old_name     = "httplib"


class HttpCookiesImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "http.cookies"
    old_name     = "Cookie"


class PickleImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "pickle"
    old_name     = "cPickle"


class DbmGnuImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "dbm.gnu"
    old_name     = "gdbm"


class EmailMimeBaseImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "email.mime.base"
    old_name     = "email.MIMEBase"


class EmailMimeImageImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "email.mime.image"
    old_name     = "email.MIMEImage"


class EmailMimeMultipartImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "email.mime.multipart"
    old_name     = "email.MIMEMultipart"


class EmailMimeNonmultipartImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "email.mime.nonmultipart"
    old_name     = "email.MIMENonMultipart"


class EmailMimeTextImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "email.mime.text"
    old_name     = "email.MIMEText"


class TkinterImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "tkinter"
    old_name     = "Tkinter"


class TkinterDialogImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "tkinter.dialog"
    old_name     = "Dialog"


class TkinterScrolledTextImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "tkinter.scrolledtext"
    old_name     = "ScrolledText"


class TkinterTixImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "tkinter.tix"
    old_name     = "Tix"


class TkinterTtkImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "tkinter.ttk"
    old_name     = "ttk"


class TkinterConstantsImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "tkinter.constants"
    old_name     = "Tkconstants"


class TkinterDndImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "tkinter.dnd"
    old_name     = "Tkdnd"


class TkinterColorchooserImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "tkinter.colorchooser"
    old_name     = "tkColorChooser"


class TkinterCommonDialogImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "tkinter.commondialog"
    old_name     = "tkCommonDialog"


class TkinterFontImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "tkinter.font"
    old_name     = "tkFont"


class TkinterMessageboxImportFallbackFixer(ModuleImportFallbackFixerBase):

    version_info = common.VersionInfo(apply_since="2.3", apply_until="2.7")
    new_name     = "tkinter.messagebox"
    old_name     = "tkMessageBox"


# TODO (mb 2018-09-02): Only ImportFrom is permitted for
#   certain imports, so that we can determine which old
#   module to import from
#
#     new_name = "http.server"
#     old_name = "BaseHTTPServer"
#     old_name = "CGIHTTPServer"
#     old_name = "SimpleHTTPServer"
#
#     new_name = "tkinter.simpledialog"
#     old_name = "tkSimpleDialog"
#     old_name = "SimpleDialog"
#
#     new_name = "tkinter.filedialog"
#     old_name = "tkFileDialog"
#     old_name = "FileDialog"
