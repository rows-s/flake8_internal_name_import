import ast
import dataclasses
from typing import ClassVar, Iterator, List, Set

import pytest
from flake8.options.manager import OptionManager

from flake8_private_name_import import Plugin

DEFAULT_CONFIG_STR = (
    '--private-name-import-skip-names=_function_global_skip,module_for_skip_specific_name._function '
    '--private-name-import-skip-modules=_module_skip,module._sub_module_skip '
    '--private-name-import-skip-names-from-modules=_module_for_skip_all_names,module._sub_module_for_skip_all_names '
)
SKIP_LOCAL_CONFIG_STR = DEFAULT_CONFIG_STR + '--private-name-import-skip-local'
SKIP_RELATIVE_CONFIG_STR = DEFAULT_CONFIG_STR + '--private-name-import-skip-relative'
DONT_SKIP_TEST_CONFIG_STR = DEFAULT_CONFIG_STR + '--private-name-import-dont-skip-test'
DONT_SKIP_TYPE_CHECKING_CONFIG_STR = DEFAULT_CONFIG_STR + '--private-name-import-dont-skip-type-checking'

CONFIG_PARSER = OptionManager(version='does_not_work_without_str_value')
Plugin.add_options(CONFIG_PARSER)


@dataclasses.dataclass
class TestCase:
    __test__: ClassVar[bool] = False

    code: str
    reports: Set[str] = dataclasses.field(default_factory=set)
    file_name: str = './main.py'
    config_str: str = DEFAULT_CONFIG_STR


VALID_CASES = (
    TestCase(''),  # empty file
    TestCase('import module'),
    TestCase('import module as _module'),
    TestCase('import module.sub_module'),
    TestCase('from module import function'),
    TestCase('from module.sub_module import function'),
    TestCase('from module.sub_module import function, variable'),
    TestCase('from . import function'),
    TestCase('from .module import function'),
    TestCase('from module import __custom__'),  # dunder name is not treated as private
    TestCase('from __custom__ import function'),  # dunder module is not treated as private
    TestCase('_variable = _function(_argument)'),  # usage of private names is not treated as import
)

REPORT_CASES = (
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
        'from module._sub_module import name',
        {'1:0: PNI003 found import from private module: module._sub_module'},
    ),
    TestCase(  # code under global if-statements must be checked
        'if sys.version_info == (3, 7):\n    import _module\nelse:\n    import _module',
        {
            '2:4: PNI002 found import of private module: _module',
            '4:4: PNI002 found import of private module: _module',
         },
    ),
    TestCase(  # all names must be checked
        'from module.sub_module import function, _Class',
        {'1:0: PNI001 found import of private name: _Class'},
    ),
    TestCase(  # all names must be reported
        'from module.sub_module import _function, _Class',
        {
            '1:0: PNI001 found import of private name: _function',
            '1:0: PNI001 found import of private name: _Class',
        },
    ),
)

SKIP_CASES = (  # these names are skipped in DEFAULT_CONFIG_STR
    # --private-name-import-skip-modules
    TestCase('import _module_skip'),
    TestCase('import module._sub_module_skip'),
    # --private-name-import-skip-names-from-modules
    TestCase('from _module_for_skip_all_names import _function, _Class'),
    TestCase('from module._sub_module_for_skip_all_names import _function, _Class'),
    # --private-name-import-skip-names
    TestCase('from module import _function_global_skip'),
    TestCase('from module_for_skip_specific_name import _function'),
    TestCase(  # only specific name is skipped
        'from module_for_skip_specific_name import _Class',
        {'1:0: PNI001 found import of private name: _Class'}
    ),
)

SKIP_TYPE_CHECKING_CASES = (
    TestCase('if TYPE_CHECKING:\n    import _module'),  # config says to skip TYPE_CHECKING
    TestCase(  # only global TYPE_CHECKING must be checked for private imports (if not skipped)
        'def function():\n    if TYPE_CHECKING:\n        import _module',
        config_str=DONT_SKIP_TYPE_CHECKING_CONFIG_STR,
    ),
    TestCase(  # config does not say to skip TYPE_CHECKING
        'if TYPE_CHECKING:\n    import _module',
        {'2:4: PNI002 found import of private module: _module'},
        config_str=DONT_SKIP_TYPE_CHECKING_CONFIG_STR,
    ),
)

CODE_WITH_LOCAL_IMPORTS = """\
def function():
    import _module  # local imports in functions are reported only if config says to
    
    if True:
        import _module  # never reported; only first indent-level of functions is checked for imports 

class MyClass:
    def method(self):
        import _module  # local imports in methods are reported only if config says to
"""

SKIP_LOCAL_CASES = (
    TestCase(CODE_WITH_LOCAL_IMPORTS, config_str=SKIP_LOCAL_CONFIG_STR),  # config says to skip local imports
    TestCase(
        CODE_WITH_LOCAL_IMPORTS,
        {
            '2:4: PNI002 found import of private module: _module',
            '9:8: PNI002 found import of private module: _module',
        },
    )
)


SKIP_RELATIVE_CASES = (
    TestCase('from . import _function', config_str=SKIP_RELATIVE_CONFIG_STR),
    TestCase('from ._module import _function', config_str=SKIP_RELATIVE_CONFIG_STR),
    TestCase('from ._module._sub_module import _function', config_str=SKIP_RELATIVE_CONFIG_STR),
    TestCase(
        'from ._module._sub_module import _function',
        {
            '1:0: PNI001 found import of private name: _function',
            '1:0: PNI003 found import from private module: ._module._sub_module',
        },
    ),
)


def get_skip_test_path_cases() -> List[TestCase]:
    test_cases = [
        TestCase(  # 'test' in the middle of file name is not treated as test
            'import _module',
            {'1:0: PNI002 found import of private module: _module'},
            file_name='./not_test_file.py',
         ),
        TestCase(  # 'test' in the middle of dir name is not treated as test
            'import _module',
            {'1:0: PNI002 found import of private module: _module'},
            file_name='./not_test_dir/conf.py',
         ),
    ]

    test_file_paths = (
        *('./main_test.py', './test_main.py', './pytest_main.py'),   # test files
        *('./main_test/conf.py', './test_main/conf.py', './pytest_main/conf.py'),  # test dirs
    )
    for file_path in test_file_paths:
        test_cases.extend(
            (
                TestCase('import _module', file_name=file_path),
                TestCase(
                    'import _module',
                    {'1:0: PNI002 found import of private module: _module'},
                    file_name=file_path,
                    config_str=DONT_SKIP_TEST_CONFIG_STR,
                ),
            )
        )

    return test_cases


ALL_TEST_CASES = (
    *VALID_CASES,
    *REPORT_CASES,
    *SKIP_CASES,
    *SKIP_RELATIVE_CASES,
    *SKIP_TYPE_CHECKING_CASES,
    *SKIP_LOCAL_CASES,
    *get_skip_test_path_cases(),
)


@pytest.mark.parametrize('test_case', ALL_TEST_CASES)
def test_plugin_reports(test_case: TestCase):
    assert set(_get_plugin_reports(test_case)) == test_case.reports


def _get_plugin_reports(test_case: TestCase) -> Iterator[str]:
    Plugin.parse_options(CONFIG_PARSER.parse_args(test_case.config_str.split())[0])
    for line_num, col_num, msg, _ in Plugin(ast.parse(test_case.code), test_case.file_name).run():
        yield f'{line_num}:{col_num}: {msg}'


def test_empty_config():
    """Plugin.add_options must specify all options with a default value"""
    Plugin.parse_options(CONFIG_PARSER.parse_args([])[0])  # test is valid while `parse_options` accesses all attributes
