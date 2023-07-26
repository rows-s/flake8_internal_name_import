import ast
import dataclasses
from functools import partial
from itertools import chain
from typing import ClassVar, Iterator, Set

import pytest

from flake8_private_name_import import Plugin


@dataclasses.dataclass(frozen=True)
class PluginResult:
    line_num: int
    col_num: int
    code: str
    reported_name: str


PNI001 = partial(PluginResult, code='PNI001')


@dataclasses.dataclass
class TestCase:
    __test__: ClassVar[bool] = False

    code: str
    file_name: str = 'main.py'
    expected_results: Set[PluginResult] = dataclasses.field(default_factory=set)


VALID_CASES = (
    TestCase(code='import module'),
    TestCase(code='import module.sub_module'),
    TestCase(code='from module import allowed_name'),
    TestCase(code='from module.sub_module import allowed_name'),
    TestCase(code='from module.sub_module import allowed_name, allowed_name2'),
    TestCase(code='from module.sub_module import (\nallowed_name,\nallowed_name2\n)'),
    TestCase(code='from module.sub_module import \\\nallowed_name,\\\nallowed_name2'),
)

SKIP_CASES = (
    TestCase(code='from __future__ import annotations'),
)

INVALID_CASES = (
    TestCase(
        code='import _module',
        expected_results={PNI001(line_num=1, col_num=0, reported_name='_module')},
    ),
    TestCase(
        code='import module._sub_module',
        expected_results={PNI001(line_num=1, col_num=0, reported_name='_sub_module')},
    ),
    TestCase(
        code='import _module._sub_module',
        expected_results={
            PNI001(line_num=1, col_num=0, reported_name='_module'),
            PNI001(line_num=1, col_num=0, reported_name='_sub_module'),
        },
    ),
    TestCase(
        code='from module import _private',
        expected_results={PNI001(line_num=1, col_num=0, reported_name='_private')},
    ),
    TestCase(
        code='from module.sub_module import _private',
        expected_results={PNI001(line_num=1, col_num=0, reported_name='_private')},
    ),
    TestCase(
        code='from module.sub_module import name, _private',
        expected_results={PNI001(line_num=1, col_num=0, reported_name='_private')},
    ),
    TestCase(
        code='from module.sub_module import (\nallowed_name,\n_private\n)',
        expected_results={PNI001(line_num=1, col_num=0, reported_name='_private')},
    ),
    TestCase(
        code='from module.sub_module import \\\nallowed_name,\\\n_private',
        expected_results={PNI001(line_num=1, col_num=0, reported_name='_private')},
    ),
    TestCase(
        code='\n\nimport _module',
        expected_results={PNI001(line_num=3, col_num=0, reported_name='_module')},
    ),
)


@pytest.mark.parametrize('test_case', chain(VALID_CASES, SKIP_CASES, INVALID_CASES))
def test_plugin(test_case: TestCase):
    assert set(_run_plugin(test_case)) == test_case.expected_results


def _run_plugin(test_case: TestCase) -> Iterator[PluginResult]:
    for line_num, col_num, msg, _ in Plugin(ast.parse(test_case.code), test_case.file_name).run():
        yield PluginResult(line_num=line_num, col_num=col_num, code=msg[:6], reported_name=msg.split(': ')[1])
