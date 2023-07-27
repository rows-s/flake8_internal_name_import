import ast
import dataclasses
from itertools import chain
from typing import ClassVar, Iterator, Set

import pytest
from flake8.options.manager import OptionManager

from flake8_private_name_import import Plugin

DEFAULT_CONFIG_STR = (
    '--private-name-import-skip-names=_function_skip,_variable_skip '
    '--private-name-import-skip-modules=_module_skip,module._sub_module_skip'
)
DONT_SKIP_TEST_CONFIG_STR = DEFAULT_CONFIG_STR + ' --private-name-import-dont-skip-test'
SKIP_RELATIVE_CONFIG_STR = DEFAULT_CONFIG_STR + ' --private-name-import-skip-relative'

CONFIG_PARSER = OptionManager(version='does_not_work_without_some_str_value')
Plugin.add_options(CONFIG_PARSER)


@dataclasses.dataclass
class TestCase:
    __test__: ClassVar[bool] = False

    code: str
    reports: Set[str] = dataclasses.field(default_factory=set)
    file_name: str = './main.py'
    config_str: str = DEFAULT_CONFIG_STR


VALID_CASES = (
    TestCase('import module'),
    TestCase('import module.sub_module'),
    TestCase('from module import function'),
    TestCase('from module.sub_module import function'),
    TestCase('from module.sub_module import function, variable'),
    TestCase('from . import function'),
    TestCase('from .module import function'),
)

INVALID_CASES = (
    TestCase(
        'import _module',
        {'1:0: PNI002 found import of private module: _module'},
    ),
    TestCase(
        'import module._sub_module',
        {'1:0: PNI002 found import of private module: module._sub_module'},
    ),
    TestCase(
        'from module import _function',
        {'1:0: PNI001 found import of private name: _function'},
    ),
    TestCase(
        'from module.sub_module import _function',
        {'1:0: PNI001 found import of private name: _function'},
    ),
    TestCase(
        'from module.sub_module import function, _variable',
        {'1:0: PNI001 found import of private name: _variable'},
    ),
    TestCase(
        'from module.sub_module import _function, _variable',
        {
            '1:0: PNI001 found import of private name: _function',
            '1:0: PNI001 found import of private name: _variable',
        },
    ),
    TestCase(
        'import _module\nimport module\nimport module._sub_module',
        {
            '1:0: PNI002 found import of private module: _module',
            '3:0: PNI002 found import of private module: module._sub_module',
        },
    ),
)

SKIP_CASES = (
    TestCase('from module import __custom__'),  # dunder is not treated as private
    TestCase('from __custom__ import function'),  # dunder is not treated as private
    TestCase('import _module', file_name='./main_test.py'),  # skip if FILE ENDS with 'test'
    TestCase('import _module', file_name='./test_main.py'),  # skip if FILE STARTS with 'test'
    TestCase('import _module', file_name='./pytest_main.py'),  # skip if FILE STARTS with 'pytest'
    TestCase('import _module', file_name='./main_test/conf.py'),  # skip if DIR ENDS with 'test'
    TestCase('import _module', file_name='./test_main/conf.py'),  # skip if DIR STARTS with 'test'
    TestCase('import _module', file_name='./pytest_main/conf.py'),  # skip if DIR STARTS with 'pytest'
    TestCase('import _module_skip', file_name='./pytest_main/conf.py'),  # config says to skip the module
    TestCase('import _sub_module_skip', file_name='./pytest_main/conf.py'),  # config says to skip the module
    TestCase('from module import _function_skip', file_name='./pytest_main/conf.py'),  # config says to skip the name
    TestCase('from module import _variable_skip', file_name='./pytest_main/conf.py'),  # config says to skip the name
    # config says to skip relative
    TestCase('from .module._sub_module import _private', config_str=SKIP_RELATIVE_CONFIG_STR),
)

ALMOST_SKIP_CASES = (
    TestCase(
        'import _module',
        {'1:0: PNI002 found import of private module: _module'},
        file_name='./not_test_conf.py',  # test in the middle of file name is not treated as test
     ),
    TestCase(
        'import _module',
        {'1:0: PNI002 found import of private module: _module'},
        file_name='./not_test_dir/conf.py',  # test in the middle of dir name is not treated as test
     ),
    TestCase(
        'import _module',
        {'1:0: PNI002 found import of private module: _module'},
        file_name='./main_test.py',  # config says to not skip test files
        config_str=DONT_SKIP_TEST_CONFIG_STR,
     ),
    TestCase(
        'from .module import _private',  # config does not say to skip relative
        {'1:0: PNI001 found import of private name: _private'},
     ),
)

CONFIG_PARSER = OptionManager(version='whatever')
Plugin.add_options(CONFIG_PARSER)


@pytest.mark.parametrize('test_case', chain(VALID_CASES, INVALID_CASES, SKIP_CASES, ALMOST_SKIP_CASES))
def test_plugin(test_case: TestCase):
    assert set(_get_plugin_reports(test_case)) == test_case.reports


def _get_plugin_reports(test_case: TestCase) -> Iterator[str]:
    Plugin.parse_options(CONFIG_PARSER.parse_args(test_case.config_str.split())[0])
    for line_num, col_num, msg, _ in Plugin(ast.parse(test_case.code), test_case.file_name).run():
        yield f'{line_num}:{col_num}: {msg}'


def test_empty_config():
    """Plugin.add_options must specify all options with a default value"""
    Plugin.parse_options(CONFIG_PARSER.parse_args([])[0])  # test is valid while `parse_options` accesses all attributes
