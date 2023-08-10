import argparse
import ast
import dataclasses
import re
from abc import ABC
from functools import partial
from typing import Any, ClassVar, Dict, Iterator, List, Set, Tuple, Type, Union

from flake8.options.manager import OptionManager


@dataclasses.dataclass
class INIXXX(ABC):
    """Used for encapsulation of message generation and avoiding copy line_number, column_number duplicate access"""
    BASE_MESSAGE: ClassVar[str]

    node: Union[ast.Import, ast.ImportFrom]
    message: str

    @property
    def full_message(self) -> str:
        return f'{type(self).__name__} {self.BASE_MESSAGE}: {self.message}'


class INI001(INIXXX):
    BASE_MESSAGE = 'found import of internal name'


class INI002(INIXXX):
    BASE_MESSAGE = 'found import of internal module'


class INI003(INIXXX):
    BASE_MESSAGE = 'found import from internal module'


def _is_internal_module_path(module_path: str) -> bool:
    """returns True if module_path is internal such as '_module' or 'module._sub_module'"""
    return (
        module_path.startswith('_')
        and not (module_path.startswith('__') and module_path.endswith('__'))
        or '._' in module_path
    )


class Visitor(ast.NodeVisitor):
    """Visits Nodes looking for imports of internal names"""

    global_skip_names: Set[str] = {}
    """Names that must be skipped independent of module"""
    skip_modules: Set[str] = {}
    """Modules that must be skipped"""
    skip_from_modules: Set[str] = {}
    """Modules any name of which must be skipped"""
    module_to_skip_names: Dict[str, Set[str]] = {}
    """Modules to set of its names that must be skipped: `{'module.sub_module': {'_name', 'name'}, ...}`"""
    skip_relative: bool = False
    """Marks if relative imports must be skipped"""
    skip_local: bool = False
    """Marks if local imports must be skipped"""

    def __init__(self) -> None:
        self.reports: List[INIXXX] = []

    def visit_Import(self, node: ast.Import) -> None:
        """Check ast.Import and appends reports to `self.reports`"""
        for alias in node.names:
            if _is_internal_module_path(alias.name) and alias.name not in self.skip_modules:
                self.reports.append(INI002(node=node, message=alias.name))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Check ast.ImportFrom and appends reports to `self.reports`"""
        module = '.' * node.level + (node.module or '')

        if (
            (node.level > 0 and self.skip_relative)
            or module in self.skip_from_modules
        ):
            return

        if _is_internal_module_path(module):
            self.reports.append(INI003(node=node, message=module))

        module_specific_skip_names = self.module_to_skip_names.get(module, set())
        for name in (alias.name for alias in node.names):
            if (
                name.startswith('_')
                and not (name.startswith('__') and name.endswith('__'))
                and name not in self.global_skip_names
                and name not in module_specific_skip_names
            ):
                self.reports.append(INI001(node=node, message=name))

    def generic_visit(self, node: ast.AST) -> None:
        """Extends default generic_visit with precondition to skip local imports or TYPE_CHECKING"""
        if self.skip_local and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return
        if isinstance(node, ast.If) and isinstance(node.test, ast.Name) and node.test.id == 'TYPE_CHECKING':
            return
        super().generic_visit(node)


class Plugin:
    name = __name__
    version = '1.0.1'

    # pattern of directory or file name that starts or ends with 'test' or 'pytest'
    TEST_PATH_PATTERN: ClassVar[re.Pattern] = re.compile('/(py)?test|test[/.]')

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
                 'If full path used then only that specific name from that specific module would be skipped.\n'
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

    @staticmethod
    def parse_options(options: argparse.Namespace) -> None:
        """Parse options and save them in Visitor's attributes"""
        Visitor.skip_relative = options.internal_name_import_skip_relative
        Visitor.skip_local = options.internal_name_import_skip_local

        Visitor.skip_modules = set(options.internal_name_import_skip_modules)
        Visitor.skip_from_modules = set(options.internal_name_import_skip_names_from_modules)

        Visitor.global_skip_names = set()
        Visitor.module_to_skip_names = {}
        for name in options.internal_name_import_skip_names:
            try:  # module.sub_module._name
                module, name = name.split('.', maxsplit=1)
            except ValueError:  # _name
                Visitor.global_skip_names.add(name)
            else:
                Visitor.module_to_skip_names.setdefault(module, set()).add(name)

    def __init__(self, tree: ast.Module, filename: str) -> None:
        self.tree = tree
        self.file_name = filename

    def run(self) -> Iterator[Tuple[int, int, str, Type[Any]]]:
        """
        Entry point for flake8

        :return: Iterator of (line_number, column_number, report_message, plugin_type)
        """
        if self.TEST_PATH_PATTERN.search(self.file_name):
            return

        for report in self._iter_reports():
            yield report.node.lineno, report.node.col_offset, report.full_message, type(self)

    def _iter_reports(self) -> Iterator[INIXXX]:
        """Encapsulates logic of running Visitor and getting reports"""
        visitor = Visitor()
        visitor.visit(self.tree)
        yield from visitor.reports
