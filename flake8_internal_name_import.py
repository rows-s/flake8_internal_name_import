import argparse
import ast
import re
from collections import deque
from functools import partial
from itertools import chain
from typing import Any, Dict, Iterator, Set, Tuple, Type

from flake8.options.manager import OptionManager

TEST_PATH_PATTERN = re.compile('/(py)?test|test[/.]')  # directory or file name starts or ends with 'test' or 'pytest'


def is_type_checking_node(node: ast.If) -> bool:
    """returns True if the If-node tests TYPE_CHECKING"""
    return isinstance(node.test, ast.Name) and node.test.id == 'TYPE_CHECKING'


def is_internal_name(name: str, is_module: bool = False) -> bool:
    """
    returns True if the name is internal

    :param is_module: If True also checks each dot-separated module
    """
    return (
        (name.startswith('_') or is_module and '._' in name)
        and not (name.startswith('__') and name.endswith('__'))
    )


class Visitor:
    """
    Acts almost like ast.NodeVisitor.
    But instead of recursive calls uses loop over stack.
    """
    FUNC_NODE_CLASSES = (ast.FunctionDef, ast.AsyncFunctionDef)
    CLASS_AND_FUNC_NODE_CLASSES = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    IMPORT_NODE_CLASSES = (ast.Import, ast.ImportFrom)
    FUNCTION_NODE_CLASSES = (ast.Import, ast.ImportFrom)

    def __init__(self, plugin: 'Plugin') -> None:
        self.plugin = plugin

    def run(self) -> Iterator[Tuple[int, int, str]]:
        """
        visit nodes and yield reports

        :return: Iterator of (line_number, column_number, report_message)
        """
        if TEST_PATH_PATTERN.search(self.plugin.file_name):
            return

        stack: deque[ast.AST] = deque((self.plugin.tree,))

        while stack:
            node = stack.pop()
            if isinstance(node, ast.Import):
                yield from self.check_import(node)
            elif isinstance(node, ast.ImportFrom):
                yield from self.check_from_import(node)
            else:
                stack.extend(self._iter_sub_nodes(node))

    def _iter_sub_nodes(self, node: ast.AST) -> Iterator[ast.AST]:
        # plugin checks only first-indent level within functions (skips if, try, for, while, with and etc.)
        # but checks nested functions;
        # Note: visitor always starts with ast.Module and will face these nodes only if not `self.plugin.skip_local`
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            extend_node_classes = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        # both cases stand for module-level statements (if, try, and etc.); but first this excludes local
        elif self.plugin.skip_local:
            extend_node_classes = (ast.If, ast.Try)
        else:
            extend_node_classes = (ast.If, ast.Try, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)

        sub_nodes = chain(
            (node.body if not (isinstance(node, ast.If) and is_type_checking_node(node)) else ()),
            (node.orelse if isinstance(node, ast.If) else ()),
            (node.finalbody if isinstance(node, ast.Try) else ()),
            chain.from_iterable(sub_node.body for sub_node in node.handlers) if isinstance(node, ast.Try) else (),
        )

        yield from (
            sub_node
            for sub_node in sub_nodes
            if isinstance(sub_node, (ast.Import, ast.ImportFrom)) or isinstance(sub_node, extend_node_classes)
        )

    def check_import(self, node: ast.Import) -> Iterator[Tuple[int, int, str]]:
        """
        Check ast.Import and yield reports

        :return: Iterator of (line_number, column_number, report_message)
        """
        for alias in node.names:
            if is_internal_name(alias.name, is_module=True) and alias.name not in self.plugin.skip_modules:
                yield node.lineno, node.col_offset, f'PNI002 found import of internal module: {alias.name}'

    def check_from_import(self, node: ast.ImportFrom) -> None:
        """
        Check ast.ImportFrom and yield reports

        :return: Iterator of (line_number, column_number, report_message)
        """
        module = '.' * node.level + (node.module or '')

        if node.level > 0 and self.plugin.skip_relative or module in self.plugin.skip_from_modules:
            return
        if is_internal_name(module, is_module=True):
            yield node.lineno, node.col_offset, f'PNI003 found import from internal module: {module}'

        module_skip_names = self.plugin.module_to_skip_names.get(module, set())

        for alias in node.names:
            name = alias.name
            if is_internal_name(name) and name not in self.plugin.global_skip_names and name not in module_skip_names:
                yield node.lineno, node.col_offset, f'PNI001 found import of internal name: {alias.name}'


class Plugin:
    name = __name__
    version = '1.0.0'

    global_skip_names: Set[str] = {}
    """Names that must be skipped independent of module"""
    skip_modules: Set[str] = {}
    """Modules that must be skipped"""
    skip_from_modules: Set[str] = {}
    """Modules any name of which must be skipped"""
    module_to_skip_names: Dict[str, Set[str]] = {}
    """Modules to set of its names that must be skipped"""
    skip_relative: bool = False
    """Marks if relative imports must be skipped"""
    skip_local: bool = False
    """Marks if local imports must be skipped"""

    @staticmethod
    def add_options(parser: OptionManager) -> None:
        add_option = partial(parser.add_option, parse_from_config=True)
        add_option(
            '--internal-name-import-skip-names',
            dest='internal_name_import_skip_names',
            comma_separated_list=True,
            default=(),
            help='Comma separated internal names import of which must not be reported.\n'
                 'Accepts full path (module.sub_module._name) or plain name (_name).\n'
                 'If full path used then only that name from that module would be skipped.\n'
                 'If plain name used then name would be skipped independent on module it imported from.'
        )
        add_option(
            '--internal-name-import-skip-modules',
            dest='internal_name_import_skip_modules',
            comma_separated_list=True,
            default=(),
            help='Comma separated internal modules import of which must not be reported.\n'
                 'Affects only imports of modules. Imports of names from those modules will be reported.'
        )
        add_option(
            '--internal-name-import-skip-names-from-modules',
            dest='internal_name_import_skip_names_from_modules',
            comma_separated_list=True,
            default=(),
            help='Comma separated modules imports of internal names from which must not be reported.'
        )
        add_option(
            '--internal-name-import-skip-local',
            dest='internal_name_import_skip_local',
            action='store_true',
            default=False,
            help='When option used, import inside functions will not be reported'
        )
        add_option(
            '--internal-name-import-skip-relative',
            dest='internal_name_import_skip_relative',
            action='store_true',
            default=False,
            help='When option used, relative imports will not be reported'
        )

    @classmethod
    def parse_options(cls, options: argparse.Namespace) -> None:
        """parse options and save them in class' attributes"""
        cls.skip_relative = options.internal_name_import_skip_relative
        cls.skip_local = options.internal_name_import_skip_local

        cls.skip_modules = set(options.internal_name_import_skip_modules)
        cls.skip_from_modules = set(options.internal_name_import_skip_names_from_modules)

        cls.global_skip_names = set()
        cls.module_to_skip_names = {}
        for name in options.internal_name_import_skip_names:
            try:  # module.sub_module._name
                module, name = name.split('.', maxsplit=1)
            except ValueError:  # _name
                cls.global_skip_names.add(name)
            else:
                cls.module_to_skip_names.setdefault(module, set()).add(name)

    def __init__(self, tree: ast.Module, filename: str) -> None:
        self.tree = tree
        self.file_name = filename

    def run(self) -> Iterator[Tuple[int, int, str, Type[Any]]]:
        """
        Entry point for flake8

        :return: Iterator of (line_number, column_number, report_message, plugin_type)
        """
        yield from ((line_num, col_num, msg, type(self)) for line_num, col_num, msg in Visitor(self).run())
