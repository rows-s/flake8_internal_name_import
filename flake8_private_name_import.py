import ast
from itertools import chain
from typing import Any, Generator, Iterator, List, Tuple, Type


class Visitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.reports: List[Tuple[int, int, str]] = []

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
            if name.startswith('_')
        )


class Plugin:
    name = __name__
    version = '0.1.2'

    def __init__(self, tree: ast.AST) -> None:
        self._tree = tree

    def run(self) -> Generator[Tuple[int, int, str, Type[Any]], None, None]:
        visitor = Visitor()
        visitor.visit(self._tree)
        for line_num, col_num, msg in visitor.reports:
            yield line_num, col_num, msg, type(self)
