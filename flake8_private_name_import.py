import ast
import re
from itertools import chain
from typing import Any, Generator, Iterator, List, Tuple, Type

SKIP_NAMES = ('__future__',)
TEST_PATH_PATTERN = re.compile('/test|test[/.]')  # directory or file name starts or ends with 'test'


class Visitor(ast.NodeVisitor):
    def __init__(self, tree: ast.AST, file_name: str) -> None:
        self.tree = tree
        self.file_name = file_name
        self.reports: List[Tuple[int, int, str]] = []

    def run(self) -> Iterator[Tuple[int, int, str]]:
        if TEST_PATH_PATTERN.search(self.file_name):
            return
        self.visit(self.tree)
        yield from iter(self.reports)

    def visit_Import(self, node: ast.Import) -> None:
        self._report_names(
            line_num=node.lineno,
            col_num=node.col_offset,
            names=chain.from_iterable(alias.name.split('.') for alias in node.names)
        )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self._report_names(
            line_num=node.lineno,
            col_num=node.col_offset,
            names=chain(node.module.split('.'), (alias.name for alias in node.names))
        )

    def _report_names(self, line_num: int, col_num: int, names: Iterator[str]) -> None:
        self.reports.extend(
            (line_num, col_num, f'PNI001 found import of private name: {name}')
            for name in names
            if name.startswith('_') and name not in SKIP_NAMES
        )


class Plugin:
    name = __name__
    version = '0.1.3'

    def __init__(self, tree: ast.AST, filename: str) -> None:
        self._visitor = Visitor(tree=tree, file_name=filename)

    def run(self) -> Generator[Tuple[int, int, str, Type[Any]], None, None]:
        yield from ((line_num, col_num, msg, type(self)) for line_num, col_num, msg in self._visitor.run())
