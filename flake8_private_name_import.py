import argparse
import ast
import re
from functools import partial
from typing import Any, Iterator, List, Tuple, Type

from flake8.options.manager import OptionManager


TEST_PATH_PATTERN = re.compile('/(py)?test|test[/.]')  # directory or file name starts or ends with 'test' or 'pytest'


class Visitor(ast.NodeVisitor):
    def __init__(self, plugin: 'Plugin') -> None:
        self.reports: List[Tuple[int, int, str]] = []
        self.plugin = plugin

    def run(self) -> Iterator[Tuple[int, int, str]]:
        if self.plugin.skip_test and TEST_PATH_PATTERN.search(self.plugin.file_name):
            return
        self.visit(self.plugin.tree)
        yield from iter(self.reports)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._report_private_module(alias.name, line_num=node.lineno, col_num=node.col_offset)

    def _report_private_module(self, module: str, *, line_num: int, col_num: int) -> None:
        is_private = module.startswith('_') or '._' in module
        is_dunder = module.startswith('__') and module.endswith('__')
        if is_private and not is_dunder and module not in self.plugin.skip_modules:
            self.reports.append((line_num, col_num, f'PNI002 found import of private module: {module}'))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.level > 0 and self.plugin.skip_relative:
            return

        module_path = '.' * node.level + (node.module or '')
        self._report_private_module(module_path, line_num=node.lineno, col_num=node.col_offset)

        for alias in node.names:
            self._report_private_name(alias.name, line_num=node.lineno, col_num=node.col_offset)

    def _report_private_name(self, name: str, *, line_num: int, col_num: int) -> None:
        if name.startswith('_') and not name.endswith('_') and name not in self.plugin.skip_names:
            self.reports.append((line_num, col_num, f'PNI001 found import of private name: {name}'))


class Plugin:
    name = __name__
    version = '0.1.5'

    skip_names = {}
    skip_modules = {}
    skip_relative = False
    skip_test = True

    @staticmethod
    def add_options(parser: OptionManager) -> None:
        add_option = partial(parser.add_option, parse_from_config=True)
        add_option(
            '--private-name-import-skip-names',
            dest='private_name_import_skip_names',
            comma_separated_list=True,
            default=(),
            help='Comma separated private names import of which must not be reported.'
        )
        add_option(
            '--private-name-import-skip-modules',
            dest='private_name_import_skip_modules',
            comma_separated_list=True,
            default=(),
            help='Comma separated private modules import of which must not be reported.'
        )
        add_option(
            '--private-name-import-skip-relative',
            dest='private_name_import_skip_relative',
            action='store_true',
            default=False,
            help='Allow import private name when import is relative (from .utils import _private_util)'
        )
        add_option(
            '--private-name-import-dont-skip-test',
            dest='private_name_import_dont_skip_test',
            action='store_true',
            default=False,
            help='By default, imports of private names in test directories/files are not reported.\n'
                 'This option turn the feature off (test files and folders will be checked for private imports).'
        )

    @classmethod
    def parse_options(cls, options: argparse.Namespace) -> None:
        cls.skip_names = set(options.private_name_import_skip_names)
        cls.skip_modules = set(options.private_name_import_skip_modules)
        cls.skip_relative = options.private_name_import_skip_relative
        cls.skip_test = not options.private_name_import_dont_skip_test

    def __init__(self, tree: ast.AST, filename: str) -> None:
        self.tree = tree
        self.file_name = filename

    def run(self) -> Iterator[Tuple[int, int, str, Type[Any]]]:
        yield from ((line_num, col_num, msg, type(self)) for line_num, col_num, msg in Visitor(self).run())
