import ast
import dataclasses
from typing import ClassVar, Iterator, Set

import pytest
from flake8.options.manager import OptionManager

from flake8_internal_name_import import Plugin

CONFIG_PARSER = OptionManager(version='does_not_work_without_str_value')
Plugin.add_options(CONFIG_PARSER)

DEFAULT_CONFIG_STR = (
    '--internal-name-import-skip-names=_function_global_skip,_ClassGlobalSkip,'  # module independent
    'module_for_skip_specific_name._function,module_for_skip_specific_name._Class '  # module dependent
    '--internal-name-import-skip-modules=_module_skip,module._sub_module_skip '
    '--internal-name-import-skip-names-from-modules=_module_for_skip_all_names,module._sub_module_for_skip_all_names '
)
SKIP_LOCAL_CONFIG_STR = DEFAULT_CONFIG_STR + '--internal-name-import-skip-local'
SKIP_RELATIVE_CONFIG_STR = DEFAULT_CONFIG_STR + '--internal-name-import-skip-relative'

CODE_WITH_LOCAL_IMPORTS = """\
def function():
    import _module  # local imports in functions are reported only if config says to
    
    if True:
        import _module  # never reported; only first indent-level of functions is checked for imports 

class MyClass:
    def method(self):
        import _module  # local imports in methods are reported only if config says to
        
        try:
            import _module  # never reported; only first indent-level of functions is checked for imports 
        finally:
            import _module  # never reported; only first indent-level of functions is checked for imports
"""


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
    TestCase('from module import __custom__'),  # dunder name is not treated as internal
    TestCase('from __custom__ import function'),  # dunder module is not treated as internal
    TestCase('_variable = _function(_argument)'),  # usage of internal names is not treated as import
    TestCase('if TYPE_CHECKING:\n    import _module'),  # TYPE_CHECKING is not reported
    # test files and dirs are skipped
    TestCase('import _module', file_name='./main_test.py'),
    TestCase('import _module', file_name='./test_main.py'),
    TestCase('import _module', file_name='./pytest_main.py'),
    TestCase('import _module', file_name='./main_test/conf.py'),
    TestCase('import _module', file_name='./test_main/conf.py'),
    TestCase('import _module', file_name='./pytest_main/conf.py'),
    # config says to skip relative imports
    TestCase('from . import _function', config_str=SKIP_RELATIVE_CONFIG_STR),
    TestCase('from ._module import _function', config_str=SKIP_RELATIVE_CONFIG_STR),
    TestCase('from ._module._sub_module import _function', config_str=SKIP_RELATIVE_CONFIG_STR),
    # config says to skip local imports
    TestCase(CODE_WITH_LOCAL_IMPORTS, config_str=SKIP_LOCAL_CONFIG_STR),
    # --internal-name-import-skip-modules (see DEFAULT_CONFIG_STR)
    TestCase('import _module_skip'),
    TestCase('import module._sub_module_skip'),
    # --internal-name-import-skip-names-from-modules (see DEFAULT_CONFIG_STR)
    TestCase('from _module_for_skip_all_names import _function, _Class, _CONSTANT'),
    TestCase('from module._sub_module_for_skip_all_names import _function, _Class, _CONSTANT'),
    # --internal-name-import-skip-names (see DEFAULT_CONFIG_STR)
    TestCase('from module import _function_global_skip'),
    TestCase('from module_for_skip_specific_name import _function'),
    TestCase('from module_for_skip_specific_name import _Class'),
)

REPORT_CASES = (
    TestCase(
        'import _module',
        {'1:0: PNI002 found import of internal module: _module'},
    ),
    TestCase(  # import of internal sub-modules that stay within public module must be reported
        'import module._sub_module',
        {'1:0: PNI002 found import of internal module: module._sub_module'},
    ),
    TestCase(
        'from module import _function',
        {'1:0: PNI001 found import of internal name: _function'},
    ),
    TestCase(
        'from module.sub_module import _function',
        {'1:0: PNI001 found import of internal name: _function'},
    ),
    TestCase(
        'from module._sub_module import name',
        {'1:0: PNI003 found import from internal module: module._sub_module'},
    ),
    TestCase(  # public names must not hide internal names
        'from module.sub_module import function, _Class',
        {'1:0: PNI001 found import of internal name: _Class'},
    ),
    TestCase(  # all names must be reported
        'from module.sub_module import _function, _Class',
        {
            '1:0: PNI001 found import of internal name: _function',
            '1:0: PNI001 found import of internal name: _Class',
        },
    ),
    TestCase(  # only specific names are skipped (see DEFAULT_CONFIG_STR)
        'from module_for_skip_specific_name import _CONSTANT',
        {'1:0: PNI001 found import of internal name: _CONSTANT'}
    ),
    TestCase(  # 'test' in the middle of file name is not treated as test file
        'import _module',
        {'1:0: PNI002 found import of internal module: _module'},
        file_name='./not_test_file.py',
    ),
    TestCase(  # 'test' in the middle of dir name is not treated as test file
        'import _module',
        {'1:0: PNI002 found import of internal module: _module'},
        file_name='./not_test_dir/file.py',
    ),
    TestCase(  # relative imports are not skipped if config does not say to
        'from ._module._sub_module import _function',
        {
            '1:0: PNI001 found import of internal name: _function',
            '1:0: PNI003 found import from internal module: ._module._sub_module',
        },
    ),
    TestCase(  # config does not say to skip local imports
        CODE_WITH_LOCAL_IMPORTS,
        {
            '2:4: PNI002 found import of internal module: _module',
            '9:8: PNI002 found import of internal module: _module',
        },
    ),
    TestCase(  # internal imports within module-level if-statements must be reported
        'if True:\n'
        '    import _module\n'
        'elif False:\n'
        '    import _module\n'
        'else:\n'
        '    if True:\n'
        '        import _module\n'
        '    else:\n'
        '        import _module',
        {
            '2:4: PNI002 found import of internal module: _module',
            '4:4: PNI002 found import of internal module: _module',
            '7:8: PNI002 found import of internal module: _module',
            '9:8: PNI002 found import of internal module: _module',
         },
    ),
    TestCase(  # internal imports within module-level try-except blocks must be reported
        'try:\n'
        '    import _module\n'
        'except ImportError:\n'
        '    import _module\n'
        'except Exception:\n'
        '    import _module\n'
        'else:\n'
        '    import _module\n'
        'finally:\n'
        '    try:\n'
        '        import _module\n'
        '    finally:\n'
        '        import _module',
        {
            '2:4: PNI002 found import of internal module: _module',
            '4:4: PNI002 found import of internal module: _module',
            '6:4: PNI002 found import of internal module: _module',
            '11:8: PNI002 found import of internal module: _module',
            '13:8: PNI002 found import of internal module: _module',
         },
    ),
)


@pytest.mark.parametrize('test_case', VALID_CASES)
def test_plugin__not_reported(test_case: TestCase):
    assert set(_get_plugin_reports(test_case)) == test_case.reports


@pytest.mark.parametrize('test_case', REPORT_CASES)
def test_plugin__reported(test_case: TestCase):
    assert set(_get_plugin_reports(test_case)) == test_case.reports


def _get_plugin_reports(test_case: TestCase) -> Iterator[str]:
    Plugin.parse_options(CONFIG_PARSER.parse_args(test_case.config_str.split())[0])
    for line_num, col_num, msg, _ in Plugin(ast.parse(test_case.code), test_case.file_name).run():
        yield f'{line_num}:{col_num}: {msg}'


def test_empty_config():
    """Plugin.add_options must specify all options with a default value"""
    Plugin.parse_options(CONFIG_PARSER.parse_args([])[0])  # test is valid while `parse_options` accesses all attributes
